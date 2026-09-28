param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_INTEGRITY'
$exitCode = 1
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\run_v40_rehearsal.py'
$secretFile = Join-Path $runtime 'secrets\a24-isolation-accounts.dpapi'
$pins = @{
    'backend/sandbox/run_v40_rehearsal.py' = '3756D79D553DF3E8A6648FE6C983ED1A27B451A7B3E70AB325FC4FAE94FCDE20'
    'backend/sandbox/v40_rehearsal_orchestration.py' = 'D9898930AF96DA991F9740637101720BFC8E640BDC59AEFD738B278C74450D6C'
    'backend/sandbox/v40_rehearsal_processes.py' = 'D8A95EB838DA0E58F75F8D686F3EE5237D5B160043F391B45B8AE786D1F2C419'
    'backend/sandbox/v40_rehearsal_owner.py' = '4A685AEE29D840C974956196AF8E8E2065E245E76DC8CA25717F087489F4ECD4'
    'backend/sandbox/v40_rehearsal_budget.py' = 'B1EC4D3980B365104C49560D551D968260F75F76FAB5D1D55B6B238C3402FBB4'
    'backend/sandbox/v40_rehearsal_transport.py' = 'DE1767A06883D4CC97CB463BE67EE5B2A08B862482C40FB51B0F7FBC2F375FA9'
    'backend/sandbox/preflight_v40_rehearsal.py' = '7A0E2FDA58AAB889A6B6174EDB8C38EC50FAEB68E8D2B276BC9C8D3C0DB99622'
    'backend/sandbox/heterogeneous_workbooks.py' = '6BF8791EE18529B49B1A02917FA7AEF3CE15903A08787166B87D594AFE594C4B'
    'backend/services/governed_producer_admission.py' = 'B2ECE48D4F056530482A9FA14F57525427CDC0B512C6341EEE5196A325A3BF44'
    'backend/services/durable_producer_admission.py' = '74AB61CB8741A78A1A1F6D22EDD47BC24B0A008C66E5A15B522AFB73C5ED2152'
    'backend/services/producer_execution_contract.py' = '768D8DCD109533ABADD968EAF86269333DB1E4E78E19278F987AA2FD27DCABEA'
    'backend/services/governed_analysis_persistence.py' = '6587CD6B9283A7973173464D4FF4A2AA4F33783412ECACB0F7249A156A453F4E'
    'backend/services/governed_analysis_read.py' = '0DC9605395001C8DB32F1C10B4E5FFE7351FA556B2A643E21D5D85A6769779C0'
    'backend/services/governed_workbook_ingestion.py' = '513EB3A1D475C4637921A5A0C851C575D318ADA5BA7C651A182324E7C8E08B5F'
    'backend/services/ownership_authority.py' = '00DC57818D26F52F11D9458954BF4BBB007853CADB22C085FCBD534BFDEC897D'
    'backend/services/v1_analysis_contract.py' = 'EEA915C30F4B11FB5C22B9DA7BF307812471C7337BF923DCD404216ED5C3755C'
    'backend/migrations/v40_prospective_execution_admission.sql' = 'D4D278FD0BD3E9E582AE9E572D1BA36604A03977C4BA021411F3542A3B2D3F24'
    'backend/migrations/v39_governed_execution_receipts.sql' = 'FED32557CBA5B93AA7DFAF7E850C4924342DFDFA26CAEC83A2AB0C9A7A3B389D'
    'backend/tests/golden/fixtures/pepperyn_v1_heterogeneous_english.xlsx' = 'FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93'
}
$oldPythonPath = [Environment]::GetEnvironmentVariable('PYTHONPATH','Process')
$oldEncoding = $OutputEncoding
$beforeHash = $null
try {
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'INTEGRITY_REFUSED' }
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    $env:PYTHONPATH = Join-Path $repo 'backend'
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $stage = 'LOCAL_CHECK'
    $output = & $python -B -W ignore $source --check 2>$null
    $code = $LASTEXITCODE
    $result = ($output -join "`n") | ConvertFrom-Json
    if ($code -ne 0 -or $result.status -ne 'V40_RUNNER_LOCAL_CHECK_PASS' -or $result.network_used -ne $false -or $result.secret_read -ne $false) { throw 'LOCAL_CHECK_REFUSED' }
    if ($CheckOnly) {
        Write-Output 'V40_WRAPPER_LOCAL_CHECK: PASS. No credentials read; no network; no Auth; no remote writes.'
        $exitCode = 0
    } else {
        $stage = 'EXISTING_DPAPI_RESTORE'
        $beforeHash = (Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash
        Add-Type -AssemblyName System.Security
        $entropy = [Text.Encoding]::UTF8.GetBytes('Pepperyn|IntegrationTest|A24IsolationAccounts|v1')
        $plain = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($secretFile),$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        try { $bundle = [Text.Encoding]::UTF8.GetString($plain) | ConvertFrom-Json }
        finally { [Array]::Clear($plain,0,$plain.Length) }
        if ($bundle.project_url -ne 'https://ejixkplrgobgwqnhidwt.supabase.co' -or $bundle.purpose -ne 'A24_TECHNICAL_ISOLATION_ONLY' -or $bundle.accounts.Count -ne 2 -or $bundle.accounts[0].email -ne 'pepperyn-isolation-a24-a@pepperyn-test.invalid') { throw 'BUNDLE_REFUSED' }
        $keys = @{}
        foreach ($name in @('SUPABASE_ANON_KEY','SUPABASE_SERVICE_KEY')) {
            $stage = $name + '_AVAILABILITY'
            $value = [Environment]::GetEnvironmentVariable($name,'Process')
            if ([string]::IsNullOrWhiteSpace($value)) {
                $secure = Read-Host "$name Pepperyn Integration Test uniquement (saisie masquee)" -AsSecureString
                $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
                try { $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
                finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
            }
            if ([string]::IsNullOrWhiteSpace($value)) { throw 'KEY_ABSENT' }
            $keys[$name] = $value
            $value = $null
        }
        $packet = @{anon=$keys.SUPABASE_ANON_KEY;service=$keys.SUPABASE_SERVICE_KEY;bundle=$bundle;authorization='V40_19_EFFECTS_7_ROWS_ONE_AUTH_ONLY'} | ConvertTo-Json -Depth 12 -Compress
        $keys = $null; $bundle = $null
        $stage = 'ONE_SHOT_ORCHESTRATION'
        # Secret JSON through stdin only, never argv, file or output.
        # Python emits only controlled stage/count records and safe result JSON.
        $packet | & $python -B -W ignore $source 2>$null
        $code = $LASTEXITCODE
        $packet = $null
        if ($code -ne 0) { throw 'ORCHESTRATION_REFUSED_NO_RETRY' }
        $stage = 'FINAL_ARTIFACT'
        $result = Get-Content -LiteralPath (Join-Path $runtime 'v40-rehearsal-19\result.json') -Raw | ConvertFrom-Json
        if ($result.status -ne 'BOUNDED_V40_REHEARSAL_PASS' -or $result.new_durable_rows -ne 7 -or $result.effect_attempts -ne 19 -or $result.auth_attempts -ne 1) { throw 'RESULT_REFUSED' }
        foreach ($flag in @('external_provider_used','real_data_used','b1_global_proven','generic_producer_admitted','production_proven','global_isolation_proven')) {
            if ($result.$flag -ne $false) { throw 'BOUNDARY_REFUSED' }
        }
        $stage = 'DPAPI_UNCHANGED'
        if ((Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash -ne $beforeHash) { throw 'DPAPI_CHANGED' }
        Write-Output 'EXISTING_DPAPI_UNCHANGED: PASS; JWT_AND_V33_UNTOUCHED; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "V40_WRAPPER_REFUSED_STAGE: $stage"
    Write-Output 'Stop. No retry, cleanup, reset or second authentication. Preserve all artifacts; remote state may be partial.'
} finally {
    [Environment]::SetEnvironmentVariable('PYTHONPATH',$oldPythonPath,'Process')
    $OutputEncoding = $oldEncoding
    $packet = $null; $bundle = $null; $keys = $null; $value = $null; $plain = $null
}
exit $exitCode
