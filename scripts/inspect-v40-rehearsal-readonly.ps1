param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_INTEGRITY'
$exitCode = 1
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\preflight_v40_rehearsal.py'
$outputFile = Join-Path $runtime 'v40-service-readonly-preflight-19.json'
$pins = @{
    'backend\sandbox\preflight_v40_rehearsal.py' = '7A0E2FDA58AAB889A6B6174EDB8C38EC50FAEB68E8D2B276BC9C8D3C0DB99622'
    'backend\tests\golden\fixtures\pepperyn_v1_heterogeneous_english.xlsx' = 'FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93'
}
$names = @('PYTHONPATH','PEPPERYN_ISOLATION_SERVICE_KEY','PEPPERYN_V40_PREFLIGHT_AUTHORIZATION')
$previous = @{}
foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
try {
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'INTEGRITY_REFUSED' }
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    $env:PYTHONPATH = Join-Path $repo 'backend'
    $stage = 'LOCAL_CHECK'
    $output = & $python -B -W ignore $source --check 2>$null
    $code = $LASTEXITCODE
    $result = ($output -join "`n") | ConvertFrom-Json
    if ($code -ne 0 -or $result.status -ne 'V40_PREFLIGHT_LOCAL_CHECK_PASS' -or $result.network_used -ne $false -or $result.secret_read -ne $false) { throw 'LOCAL_CHECK_REFUSED' }
    if ($CheckOnly) {
        Write-Output 'V40_READ_ONLY_WRAPPER_LOCAL_CHECK: PASS. No key read; no network; no login; no remote write.'
        $exitCode = 0
    } else {
        $stage = 'EXISTING_REPORT_REFUSAL'
        if (Test-Path -LiteralPath $outputFile) { throw 'PRESERVE_EXISTING_REPORT_NO_RERUN' }
        $stage = 'SERVICE_KEY_AVAILABILITY'
        $value = [Environment]::GetEnvironmentVariable('SUPABASE_SERVICE_KEY','Process')
        if ([string]::IsNullOrWhiteSpace($value)) {
            $secure = Read-Host 'Cle service Supabase Pepperyn Integration Test uniquement (saisie masquee)' -AsSecureString
            $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            try { $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
        }
        if ([string]::IsNullOrWhiteSpace($value)) { throw 'KEY_ABSENT' }
        $env:PEPPERYN_ISOLATION_SERVICE_KEY = $value
        $env:PEPPERYN_V40_PREFLIGHT_AUTHORIZATION = 'READ_ONLY_NO_LOGIN'
        $value = $null
        $stage = 'READ_ONLY_PREFLIGHT'
        $output = & $python -B -W ignore $source --output $outputFile 2>$null
        $code = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($code -ne 0 -or $result.status -ne 'V40_SERVICE_READ_ONLY_PREFLIGHT_PASS' -or $result.new_registries_empty -ne $true) { throw 'PREFLIGHT_REFUSED' }
        foreach ($flag in @('authenticated_actor_proven','schema_catalog_verified_by_this_script','business_write_performed','rehearsal_ready','external_provider_used','real_data_used')) {
            if ($result.$flag -ne $false) { throw 'BOUNDARY_REFUSED' }
        }
        if ($result.auth_attempts -ne 0 -or $result.effect_attempts -ne 0) { throw 'EFFECT_BOUNDARY_REFUSED' }
        $result | ConvertTo-Json -Compress | Write-Output
        Write-Output 'NO_AUTH_LOGIN; NO_REMOTE_WRITE; JWT_AND_V33_UNTOUCHED; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "V40_READ_ONLY_REFUSED_STAGE: $stage"
    Write-Output 'No login or remote write attempted. No automatic retry. Preserve any report and return only this diagnostic.'
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
    $value = $null; $output = $null; $result = $null
}
exit $exitCode
