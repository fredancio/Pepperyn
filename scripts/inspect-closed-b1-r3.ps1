param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$oldPath = $env:PYTHONPATH
$stage = 'LOCAL_INTEGRITY'
$code = 1
try {
    $pins = @{
        'backend\sandbox\inspect_closed_b1_r3.py' = '5E61FC1D188AD14FD2E9C46F2F306ABC373C75375FCD3C227DC52662369EC673'
        'backend\sandbox\preflight_connected_b1.py' = '8917A5D234801CFC25156A937F98029B084911E98D851E5805C35597946C1468'
        'backend\services\governed_rehearsal_permit.py' = '6C419B01595E44911F4BCEAF26E652AB940BB11B18059E7412ED62E80C042A78'
    }
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'INTEGRITY_REFUSED' }
    }
    $env:PYTHONPATH = Join-Path $repo 'backend'
    $source = Join-Path $repo 'backend\sandbox\inspect_closed_b1_r3.py'
    if ($CheckOnly) {
        & $python -B -W ignore $source --runtime $runtime --local-check
        if ($LASTEXITCODE -ne 0) { throw 'LOCAL_CHECK_REFUSED' }
    } else {
        $stage = 'EXISTING_SERVICE_KEY'
        if ([string]::IsNullOrWhiteSpace($env:SUPABASE_SERVICE_KEY)) { throw 'KEY_UNAVAILABLE' }
        $stage = 'READ_ONLY_POSTFLIGHT'
        $output = & $python -B -W ignore $source --runtime $runtime 2>$null
        $resultCode = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($resultCode -ne 0 -or $result.status -ne 'B1_R3_NO_WRITE_POSTFLIGHT_PASS') {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            if ($result.diagnostic -match '^[A-Za-z0-9_]+$') { Write-Output ('SAFE_DIAGNOSTIC: ' + $result.diagnostic) }
            throw 'POSTFLIGHT_REFUSED'
        }
        if ($result.analysis_id -ne 'e2dc7bd5-c71a-4c88-821c-b1f2696fb04b') { throw 'RESULT_REFUSED' }
        foreach ($name in @('prospective_uuid_absent_in_three_tables','preexisting_scope_hashes_unchanged','engagement_binding_unchanged','permits_closed_unchanged')) {
            if ($result.$name -cne $true) { throw 'RESULT_REFUSED' }
        }
        foreach ($name in @('business_write_performed','permit_created','transport_activated','external_provider_used','real_data_used','b1_global_proven')) {
            if ($result.$name -cne $false) { throw 'RESULT_REFUSED' }
        }
        $result | Select-Object status,analysis_id,prospective_uuid_absent_in_three_tables,preexisting_scope_hashes_unchanged,engagement_binding_unchanged,permits_closed_unchanged,business_write_performed,permit_created,transport_activated,external_provider_used,real_data_used,b1_global_proven | ConvertTo-Json -Compress | Write-Output
        Write-Output 'JWT_AND_V33_UNTOUCHED; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
    }
    $code = 0
} catch {
    Write-Output "B1_R3_INSPECTION_REFUSED_STAGE: $stage"
    Write-Output 'No write, renewal, cleanup or server start. Preserve state and report.'
} finally {
    $env:PYTHONPATH = $oldPath
    $output = $null; $result = $null
}
exit $code
