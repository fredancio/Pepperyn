param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\read_b1_temporal_confirmation_r2.py'
$names = @('PYTHONPATH','PEPPERYN_GOVERNED_PIPELINE_TRANSPORT')
$previous = @{}
foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
$stage = 'INTEGRITY'
$result = 1
try {
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne '604C954FE2F791D84178C25A67FDFDAFC3D83BF8370B46B70F7059A361EF502D') { throw 'INTEGRITY_REFUSED' }
    if ((Get-FileHash -LiteralPath (Join-Path $repo 'backend\sandbox\read_completed_b1.py') -Algorithm SHA256).Hash -ne '6AC41A455F083A050D172745E5D698A5CA4D23E267322828FFC2819D3E72BBF0') { throw 'SHARED_BOUNDARY_CHANGED' }
    if (-not (Test-Path -LiteralPath $python)) { throw 'RUNTIME_MISSING' }
    if ($CheckOnly) {
        Write-Output 'B1_TEMPORAL_CONFIRMATION_R2_SCRIPT_CHECK: PASS. No network, secret access, marker or server.'
        $result = 0
    } else {
        $stage = 'PORT_8000_MUST_BE_FREE'
        $listeners = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
        if (@($listeners | Where-Object { $_.Port -eq 8000 }).Count -ne 0) { throw 'PORT_OCCUPIED_NO_KILL' }
        $stage = 'FRONTEND_MUST_BE_READY'
        if (@($listeners | Where-Object { $_.Port -eq 3000 }).Count -eq 0) { throw 'FRONTEND_NOT_LISTENING' }
        $stage = 'EXISTING_ENVIRONMENT_REQUIRED'
        if ($env:SUPABASE_URL -ne 'https://ejixkplrgobgwqnhidwt.supabase.co' -or $env:ENVIRONMENT -ne 'development') { throw 'ENVIRONMENT_MISSING' }
        foreach ($name in @('SUPABASE_SERVICE_KEY','SUPABASE_ANON_KEY','JWT_GUEST_SECRET')) {
            if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name,'Process'))) { throw 'EXISTING_SECRET_MISSING' }
        }
        $stage = 'NO_PREVIOUS_READ_WINDOW'
        if (Test-Path -LiteralPath (Join-Path $runtime 'b1-r5-temporal-confirmation-r2.started')) { throw 'NO_RESTART' }
        $env:PYTHONPATH = Join-Path $repo 'backend'
        $env:PEPPERYN_GOVERNED_PIPELINE_TRANSPORT = '0'
        $stage = 'BOUNDED_READ_ONLY_SERVER'
        Push-Location (Join-Path $repo 'backend')
        try { & $python -B -W ignore $source --runtime $runtime; $result = $LASTEXITCODE }
        finally { Pop-Location }
    }
} catch {
    Write-Output "B1_TEMPORAL_CONFIRMATION_R2_START_REFUSED_STAGE: $stage"
    Write-Output 'No automatic retry. No secret displayed or regenerated. R5 untouched.'
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
}
exit $result
