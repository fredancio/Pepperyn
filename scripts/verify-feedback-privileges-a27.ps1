param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_PREFLIGHT'
$exitCode = 1
$secretFile = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\secrets\a24-isolation-accounts.dpapi'
$source = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend\sandbox\verify_feedback_privileges.py'
$python = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$expected = 'B652B171BB5EC3ADD9552E9DA1F4C8B6C7AA209B2B25BD82CA9A334184715A23'
$previousBundle = $env:PEPPERYN_ISOLATION_BOOTSTRAP
$previousAnon = $env:PEPPERYN_ISOLATION_ANON_KEY
try {
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $expected) { throw 'SOURCE_HASH_MISMATCH' }
    if (-not (Test-Path -LiteralPath $secretFile -PathType Leaf)) { throw 'BUNDLE_ABSENT' }
    if ($CheckOnly) {
        Write-Output 'A27_PREFLIGHT: PASS. No secrets read; no network.'
        $exitCode = 0
    } else {
        $beforeHash = (Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash
        $stage = 'EXISTING_DPAPI_RESTORE'
        Add-Type -AssemblyName System.Security
        $entropy = [Text.Encoding]::UTF8.GetBytes('Pepperyn|IntegrationTest|A24IsolationAccounts|v1')
        $plain = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($secretFile),$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        try { $json = [Text.Encoding]::UTF8.GetString($plain) }
        finally { [Array]::Clear($plain,0,$plain.Length) }
        $bundle = $json | ConvertFrom-Json
        if ($bundle.project_url -ne 'https://ejixkplrgobgwqnhidwt.supabase.co' -or $bundle.purpose -ne 'A24_TECHNICAL_ISOLATION_ONLY' -or $bundle.accounts.Count -ne 2) { throw 'BUNDLE_REFUSED' }
        $stage = 'ANON_KEY_AVAILABILITY'
        $anon = $env:SUPABASE_ANON_KEY
        if ([string]::IsNullOrWhiteSpace($anon)) {
            $secure = Read-Host 'SUPABASE_ANON_KEY Integration Test uniquement (saisie masquee; pas service_role)' -AsSecureString
            $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            try { $anon = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
        }
        if ([string]::IsNullOrWhiteSpace($anon)) { throw 'KEY_ABSENT' }
        $env:PEPPERYN_ISOLATION_BOOTSTRAP = $json
        $env:PEPPERYN_ISOLATION_ANON_KEY = $anon
        $stage = 'SESSION_DENIAL_REHEARSAL'
        $output = & $python -B -W ignore $source 2>$null
        $pythonExit = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($pythonExit -ne 0 -or $result.status -ne 'BOUNDED_FEEDBACK_DIRECT_DML_DENIAL_PASS') {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            throw 'REHEARSAL_REFUSED'
        }
        $stage = 'RESULT_GATE'
        if ($result.denied_operations -ne 6 -or $result.authority -ne 'TWO_REAL_AUTHENTICATED_USER_SESSIONS' -or $result.proof_scope -ne 'DECISION_FEEDBACK_DIRECT_TABLE_PRIVILEGES_ONLY') { throw 'SCOPE_REFUSED' }
        foreach ($field in @('business_write_performed','api_write_isolation_proven','write_isolation_proven','analysis_export_isolation_proven','global_isolation_proven','production_proof','external_provider_used','real_data_used')) {
            if ($result.$field -ne $false) { throw 'PROOF_SCOPE_REFUSED' }
        }
        if ((Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash -ne $beforeHash) { throw 'BUNDLE_CHANGED' }
        $result | ConvertTo-Json -Depth 4 -Compress | Write-Output
        Write-Output 'EXISTING_DPAPI_UNCHANGED: PASS; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "A27_REFUSED_STAGE: $stage"
    Write-Output 'Do not retry or regenerate credentials. No account creation/reset or A26 pair modification is part of this procedure.'
} finally {
    $env:PEPPERYN_ISOLATION_BOOTSTRAP = $previousBundle
    $env:PEPPERYN_ISOLATION_ANON_KEY = $previousAnon
    $json = $null; $bundle = $null; $anon = $null; $output = $null
}
exit $exitCode
