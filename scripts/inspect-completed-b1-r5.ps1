param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$oldPath = $env:PYTHONPATH
$oldUrl = $env:SUPABASE_URL
$oldKey = $env:SUPABASE_SERVICE_KEY
$stage = 'LOCAL_INTEGRITY'
$code = 1
try {
    $pins = @{
        'backend\sandbox\inspect_completed_b1_r5.py' = '7738C8886D29FA605A1534EC01D8BCF83305C4E4147550AD658003852F3C763A'
        'backend\sandbox\preflight_connected_b1.py' = '8917A5D234801CFC25156A937F98029B084911E98D851E5805C35597946C1468'
        'backend\services\governed_rehearsal_permit.py' = '6C419B01595E44911F4BCEAF26E652AB940BB11B18059E7412ED62E80C042A78'
        'backend\services\governed_analysis_persistence.py' = '6587CD6B9283A7973173464D4FF4A2AA4F33783412ECACB0F7249A156A453F4E'
        'backend\services\execution_provenance.py' = 'DCA7780C51895C1A481E00B43A822E9D911CCDC50971DA69DA36090E4D2999CD'
    }
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'INTEGRITY_REFUSED' }
    }
    $env:PYTHONPATH = Join-Path $repo 'backend'
    $source = Join-Path $repo 'backend\sandbox\inspect_completed_b1_r5.py'
    if ($CheckOnly) {
        & $python -B -W ignore $source --runtime $runtime --local-check
        if ($LASTEXITCODE -ne 0) { throw 'LOCAL_CHECK_REFUSED' }
    } else {
        $stage = 'SERVICE_KEY_AVAILABILITY'
        $env:SUPABASE_URL = 'https://ejixkplrgobgwqnhidwt.supabase.co'
        if ([string]::IsNullOrWhiteSpace($env:SUPABASE_SERVICE_KEY)) {
            $secure = Read-Host 'Cle service Supabase Integration Test (saisie masquee)' -AsSecureString
            $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            try { $env:SUPABASE_SERVICE_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr); $secure.Dispose() }
        }
        if ([string]::IsNullOrWhiteSpace($env:SUPABASE_SERVICE_KEY)) { throw 'KEY_UNAVAILABLE' }
        $stage = 'READ_ONLY_POSTFLIGHT'
        $output = & $python -B -W ignore $source --runtime $runtime 2>$null
        $resultCode = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($resultCode -ne 0 -or $result.status -ne 'BOUNDED_B1_R5_PERSISTED_TRIO_POSTFLIGHT_PASS') {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            if ($result.diagnostic -match '^[A-Za-z0-9_]+$') { Write-Output ('SAFE_DIAGNOSTIC: ' + $result.diagnostic) }
            throw 'POSTFLIGHT_REFUSED'
        }
        if ($result.analysis_id -ne 'e2dc7bd5-c71a-4c88-821c-b1f2696fb04b' -or $result.new_durable_rows -ne 3) { throw 'RESULT_REFUSED' }
        foreach ($name in @('preexisting_scope_hashes_unchanged','receipt_binding_verified','closed_permits_unchanged')) {
            if ($result.$name -cne $true) { throw 'RESULT_REFUSED' }
        }
        foreach ($name in @('business_write_performed','transport_activated','external_provider_used','real_data_used','b1_global_proven')) {
            if ($result.$name -cne $false) { throw 'RESULT_REFUSED' }
        }
        $result | Select-Object status,analysis_id,new_durable_rows,preexisting_scope_hashes_unchanged,receipt_binding_verified,closed_permits_unchanged,business_write_performed,transport_activated,external_provider_used,real_data_used,b1_global_proven | ConvertTo-Json -Compress | Write-Output
        Write-Output 'JWT_AND_V33_UNTOUCHED; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
    }
    $code = 0
} catch {
    Write-Output "B1_R5_INSPECTION_REFUSED_STAGE: $stage"
    Write-Output 'No write, renewal, cleanup or server start. Preserve state and report. Do not retry automatically.'
} finally {
    $env:PYTHONPATH = $oldPath
    $env:SUPABASE_URL = $oldUrl
    $env:SUPABASE_SERVICE_KEY = $oldKey
    $output = $null; $result = $null; $oldKey = $null
}
exit $code
