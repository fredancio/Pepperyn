param([switch]$CheckOnly)
$Mode = 'Backend'
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_INTEGRITY'
$exitCode = 1
$closeOnExit = $false
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$manifest = Join-Path $runtime 'b1-connected-rehearsal-r5.json'
$closed = [IO.Path]::ChangeExtension($manifest,'.closed')
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\run_connected_b1_r5.py'
$names = @('PYTHONPATH','PEPPERYN_GOVERNED_PIPELINE_TRANSPORT','PEPPERYN_GOVERNED_REHEARSAL_MANIFEST','NEXT_PUBLIC_GOVERNED_PIPELINE_TRANSPORT')
$previous = @{}
foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
$pins = @{
    'backend\sandbox\inspect_closed_b1_r3.py' = '5E61FC1D188AD14FD2E9C46F2F306ABC373C75375FCD3C227DC52662369EC673'
    'backend\sandbox\preflight_connected_b1.py' = '8917A5D234801CFC25156A937F98029B084911E98D851E5805C35597946C1468'
    'backend\sandbox\run_connected_b1_r5.py' = '2009F2429552A8E56EBD59F60C1F1EE4253F2A75EA9C71E3E955880861917616'
    'backend\services\governed_pipeline_mount.py' = '1938B29437AD221977E4A96137B0346D8FBC162F53610C1C536A00525A60FC53'
    'backend\services\governed_rehearsal_permit.py' = '6C419B01595E44911F4BCEAF26E652AB940BB11B18059E7412ED62E80C042A78'
}
try {
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'INTEGRITY_REFUSED' }
    }
    if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ne '76BB3542C091C5556B381454827F4335BC14200D733469BA0D418615A42BE0E5') { throw 'MANIFEST_CHANGED' }
    if (-not $CheckOnly) { $closeOnExit = $true }
    $stage = 'PERMIT_VALIDITY'
    $permit = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    if ([DateTimeOffset]::Parse($permit.expires_at).UtcDateTime -le [DateTime]::UtcNow) { throw 'PERMIT_EXPIRED' }
    if ((Test-Path -LiteralPath $closed) -or (Test-Path -LiteralPath ([IO.Path]::ChangeExtension($manifest,'.attempt')))) { throw 'CLOSED_OR_ALREADY_ATTEMPTED' }
    if ($CheckOnly) {
        $env:PYTHONPATH = Join-Path $repo 'backend'
        & $python -B -W ignore $source --manifest $manifest --local-check
        if ($LASTEXITCODE -ne 0) { throw 'LOCAL_CHECK_REFUSED' }
        Write-Output 'B1_LAUNCHER_CHECK: PASS. No remote operation, no activation, no secret modification.'
        $exitCode = 0
    } else {
        $stage = 'PORT_MUST_BE_FREE'
        $port = if ($Mode -eq 'Backend') { 8000 } else { 3000 }
        $listeners = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
        if (@($listeners | Where-Object { $_.Port -in @(3000,8000) }).Count -ne 0) { throw 'PORT_IN_USE_NO_KILL' }
        if ($Mode -eq 'Backend') {
            $stage = 'EXISTING_BACKEND_ENVIRONMENT'
            if ($env:SUPABASE_URL -ne 'https://ejixkplrgobgwqnhidwt.supabase.co' -or
                $env:ENVIRONMENT -ne 'development' -or $env:PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO -ne '1' -or
                $env:PEPPERYN_SYNTHETIC_V1_COMPANY_ID -ne $permit.company_id) { throw 'ENVIRONMENT_REFUSED' }
            foreach ($name in @('SUPABASE_ANON_KEY','SUPABASE_SERVICE_KEY','JWT_GUEST_SECRET')) {
                if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name,'Process'))) { throw 'EXISTING_SECRET_ABSENT' }
            }
            $env:PYTHONPATH = Join-Path $repo 'backend'
            $env:PEPPERYN_GOVERNED_PIPELINE_TRANSPORT = '1'
            $env:PEPPERYN_GOVERNED_REHEARSAL_MANIFEST = $manifest
            $stage = 'BOUNDED_BACKEND'
            Push-Location (Join-Path $repo 'backend')
            try { & $python -B -W ignore $source --manifest $manifest; $exitCode = $LASTEXITCODE }
            finally { Pop-Location }

        }
    }
} catch {
    Write-Output "B1_START_REFUSED_STAGE: $stage"
    Write-Output 'Stop. Do not retry or reset the permit. No secret displayed or regenerated.'
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
    if ($closeOnExit) {
        if (-not (Test-Path -LiteralPath $closed)) {
            $handle = [IO.File]::Open($closed,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
            try { $bytes = [Text.Encoding]::UTF8.GetBytes('CLOSED_NO_AUTOMATIC_RESUME'); $handle.Write($bytes,0,$bytes.Length); $handle.Flush() }
            finally { $handle.Dispose() }
        }
        Write-Output 'B1_TEMPORARY_SURFACE: CLOSED. No live PASS inferred.'
    }
}
exit $exitCode
