param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_INTEGRITY'
$exitCode = 1
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\preflight_connected_b1.py'
$manifest = Join-Path $runtime 'b1-connected-rehearsal.json'
$oldKey = [Environment]::GetEnvironmentVariable('SUPABASE_SERVICE_KEY','Process')
$oldPath = [Environment]::GetEnvironmentVariable('PYTHONPATH','Process')
$pins = @{
    'backend\sandbox\preflight_connected_b1.py' = '8917A5D234801CFC25156A937F98029B084911E98D851E5805C35597946C1468'
    'backend\services\governed_rehearsal_permit.py' = '6C419B01595E44911F4BCEAF26E652AB940BB11B18059E7412ED62E80C042A78'
    'backend\services\governed_analysis_persistence.py' = '6587CD6B9283A7973173464D4FF4A2AA4F33783412ECACB0F7249A156A453F4E'
    'backend\tests\golden\fixtures\pepperyn_v1_heterogeneous_english.xlsx' = 'FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93'
}
try {
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'INTEGRITY_REFUSED' }
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    foreach ($suffix in @('.json','.pending','.attempt','.closed')) {
        if (Test-Path -LiteralPath ([IO.Path]::ChangeExtension($manifest,$suffix))) { throw 'EXISTING_STATE_NO_RERUN' }
    }
    if ($CheckOnly) {
        Write-Output 'B1_LOCAL_PREFLIGHT_CHECK: PASS. No network, no activation, no write.'
        $exitCode = 0
    } else {
        $stage = 'SERVICE_KEY_AVAILABILITY'
        if ([string]::IsNullOrWhiteSpace($oldKey)) {
            $secure = Read-Host 'SUPABASE_SERVICE_KEY de Pepperyn Integration Test uniquement (saisie masquee)' -AsSecureString
            $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            try { $env:SUPABASE_SERVICE_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
        }
        if ([string]::IsNullOrWhiteSpace($env:SUPABASE_SERVICE_KEY)) { throw 'KEY_ABSENT' }
        $env:PYTHONPATH = Join-Path $repo 'backend'
        $stage = 'READ_ONLY_PREFLIGHT'
        $output = & $python -B -W ignore $source --manifest $manifest 2>$null
        $code = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($code -ne 0 -or $result.status -ne 'B1_READ_ONLY_PREFLIGHT_PASS' -or
            $result.business_write_performed -ne $false -or $result.transport_activated -ne $false -or
            $result.new_analysis_created -ne $false -or $result.external_provider_used -ne $false -or $result.real_data_used -ne $false) {
            if ($result.status -eq 'REFUSED' -and $result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            if ($result.diagnostic -match '^[A-Za-z0-9_]+$') { Write-Output ('SAFE_DIAGNOSTIC: ' + $result.diagnostic) }
            throw 'PREFLIGHT_REFUSED'
        }
        # Fixed safe projection only; do not echo arbitrary child output.
        [pscustomobject]@{
            status = 'B1_READ_ONLY_PREFLIGHT_PASS'
            business_write_performed = $false
            transport_activated = $false
            new_analysis_created = $false
            external_provider_used = $false
            real_data_used = $false
        } | ConvertTo-Json -Compress | Write-Output
        Write-Output 'JWT_AND_V33_UNTOUCHED; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "B1_PREFLIGHT_REFUSED_STAGE: $stage"
    Write-Output 'No activation or remote write. Do not rerun; preserve local evidence and report this stage.'
} finally {
    [Environment]::SetEnvironmentVariable('SUPABASE_SERVICE_KEY',$oldKey,'Process')
    [Environment]::SetEnvironmentVariable('PYTHONPATH',$oldPath,'Process')
    $output = $null; $result = $null; $oldKey = $null
}
exit $exitCode
