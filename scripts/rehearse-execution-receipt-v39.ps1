param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_INTEGRITY'
$exitCode = 1
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$secretFile = Join-Path $runtime 'secrets\a24-isolation-accounts.dpapi'
$manifest = Join-Path $runtime 'v39-receipt-rehearsal.json'
$source = Join-Path $repo 'backend\sandbox\rehearse_execution_receipt_v39.py'
$pins = @{
    'backend\sandbox\rehearse_execution_receipt_v39.py' = 'B832B00D120723FAE5040A9A24F02D0DFEB55E6337E1D9D8F6F13F9277CE1D90'
    'backend\services\execution_provenance.py' = 'DCA7780C51895C1A481E00B43A822E9D911CCDC50971DA69DA36090E4D2999CD'
    'backend\services\governed_analysis_persistence.py' = '6587CD6B9283A7973173464D4FF4A2AA4F33783412ECACB0F7249A156A453F4E'
    'backend\sandbox\heterogeneous_workbooks.py' = '7D65AA143F80E22448D5D8A14DE1AB87486BC56BEC0C348543187A26F2210C66'
    'backend\migrations\v39_governed_execution_receipts.sql' = 'FED32557CBA5B93AA7DFAF7E850C4924342DFDFA26CAEC83A2AB0C9A7A3B389D'
    'backend\tests\golden\fixtures\pepperyn_v1_heterogeneous_english.xlsx' = 'FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93'
}
$names = @('PYTHONPATH','PEPPERYN_ISOLATION_BOOTSTRAP','PEPPERYN_ISOLATION_ANON_KEY','PEPPERYN_ISOLATION_SERVICE_KEY','PEPPERYN_V39_AUTHORIZATION')
$previous = @{}
foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
try {
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'INTEGRITY_REFUSED' }
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    if ((Test-Path -LiteralPath $manifest) -or (Test-Path -LiteralPath ([IO.Path]::ChangeExtension($manifest,'.pending')))) { throw 'EXISTING_ATTEMPT_NO_RERUN' }
    $env:PYTHONPATH = Join-Path $repo 'backend'
    $stage = 'LOCAL_MOCK_CHECK'
    $output = & $python -B -W ignore $source --phase check --manifest $manifest 2>$null
    $code = $LASTEXITCODE
    $result = ($output -join "`n") | ConvertFrom-Json
    if ($code -ne 0 -or $result.status -ne 'V39_LOCAL_CHECK_PASS' -or $result.network_used -ne $false -or $result.write_performed -ne $false) { throw 'LOCAL_CHECK_REFUSED' }
    if ($CheckOnly) {
        Write-Output 'V39_LOCAL_CHECK: PASS. No credentials read, no network, no remote writes.'
        $exitCode = 0
    } else {
        $stage = 'EXISTING_DPAPI_RESTORE'
        $beforeHash = (Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash
        Add-Type -AssemblyName System.Security
        $entropy = [Text.Encoding]::UTF8.GetBytes('Pepperyn|IntegrationTest|A24IsolationAccounts|v1')
        $plain = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($secretFile),$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        try { $json = [Text.Encoding]::UTF8.GetString($plain) } finally { [Array]::Clear($plain,0,$plain.Length) }
        $bundle = $json | ConvertFrom-Json
        if ($bundle.project_url -ne 'https://ejixkplrgobgwqnhidwt.supabase.co' -or $bundle.purpose -ne 'A24_TECHNICAL_ISOLATION_ONLY' -or $bundle.accounts.Count -ne 2) { throw 'BUNDLE_REFUSED' }
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
            if ($name -eq 'SUPABASE_ANON_KEY') { $env:PEPPERYN_ISOLATION_ANON_KEY = $value }
            else { $env:PEPPERYN_ISOLATION_SERVICE_KEY = $value }
            $value = $null
        }
        $env:PEPPERYN_ISOLATION_BOOTSTRAP = $json
        $env:PEPPERYN_V39_AUTHORIZATION = 'V39_FOUR_CALLS_THREE_ROWS_TECHNICAL_ONE'
        $stage = 'FIRST_PROCESS'
        $output = & $python -B -W ignore $source --phase persist --manifest $manifest 2>$null
        $code = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($code -ne 0 -or $result.status -ne 'V39_PERSISTED_PENDING_SECOND_PROCESS' -or $result.rpc_attempts -ne 4 -or $result.new_durable_rows -ne 3) {
            if ($result.status -eq 'REFUSED' -and $result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            throw 'PERSIST_REFUSED'
        }
        Write-Output 'V39_FIRST_PROCESS: EXITED_SUCCESSFULLY. Final PASS not yet established.'
        # Invocation above has returned: first Python process is fully terminated.
        $stage = 'SECOND_PROCESS_READ_ONLY'
        $output = & $python -B -W ignore $source --phase verify --manifest $manifest 2>$null
        $code = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($code -ne 0 -or $result.status -ne 'BOUNDED_V39_PERSISTENCE_RECOVERY_PASS' -or $result.rpc_attempts -ne 0 -or $result.new_durable_rows -ne 3 -or $result.existing_scope_rows_unchanged -ne $true) { throw 'RECOVERY_REFUSED' }
        if ($result.binding_denial -ne 'P0001_NO_ROWS' -or $result.late_rollback -ne '23514_NO_ANALYSIS_ENVELOPE_OR_RECEIPT' -or $result.replay_denial -ne '23505_UNCHANGED') { throw 'EVIDENCE_REFUSED' }
        foreach ($flag in @('external_provider_used','real_data_used','b1_global_proven','http_uvicorn_proven','global_isolation_proven','production_proven')) {
            if ($result.$flag -ne $false) { throw 'PROOF_SCOPE_REFUSED' }
        }
        $stage = 'DPAPI_UNCHANGED'
        if ((Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash -ne $beforeHash) { throw 'BUNDLE_CHANGED' }
        $result | ConvertTo-Json -Compress | Write-Output
        Write-Output 'EXISTING_DPAPI_UNCHANGED: PASS; JWT_AND_V33_UNTOUCHED; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "V39_REFUSED_STAGE: $stage"
    if ($null -ne $result -and $result.status -eq 'REFUSED' -and $null -ne $result.rpc_attempts -and $result.rpc_attempts -ge 0 -and $result.rpc_attempts -le 4) {
        Write-Output ('RPC_ATTEMPTS_REPORTED: ' + $result.rpc_attempts)
    }
    Write-Output 'No automatic retry or cleanup. If first process started, rows may exist. Preserve manifest and report this stage; do not rerun.'
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
    $json = $null; $bundle = $null; $value = $null; $output = $null
}
exit $exitCode
