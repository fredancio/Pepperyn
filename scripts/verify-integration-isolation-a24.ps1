param([switch]$CheckOnly, [switch]$IncludeHistory)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_PREFLIGHT'
$exitCode = 1
$secretFile = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\secrets\a24-isolation-accounts.dpapi'
$source = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend\sandbox\verify_isolation_accounts.py'
$python = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$expected = 'D918EFA0F5B6335ECD840022028C8F857255742E4002FD3F0A8AF098FF600C81'
$previousBundle = $env:PEPPERYN_ISOLATION_BOOTSTRAP
$previousAnon = $env:PEPPERYN_ISOLATION_ANON_KEY
try {
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $expected) { throw 'SOURCE_HASH_MISMATCH' }
    if (-not (Test-Path -LiteralPath $secretFile -PathType Leaf)) { throw 'EXISTING_BUNDLE_ABSENT' }
    if ($CheckOnly) {
        Write-Output 'A24_READ_REHEARSAL_PREFLIGHT: PASS. No secrets read; no network; no writes.'
        $exitCode = 0
    } else {
        $beforeHash = (Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash
        $stage = 'EXISTING_DPAPI_RESTORE'
        Add-Type -AssemblyName System.Security
        $entropy = [Text.Encoding]::UTF8.GetBytes('Pepperyn|IntegrationTest|A24IsolationAccounts|v1')
        $plain = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($secretFile),$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        $json = [Text.Encoding]::UTF8.GetString($plain)
        [Array]::Clear($plain,0,$plain.Length)
        $bundle = $json | ConvertFrom-Json
        if ($bundle.project_url -ne 'https://ejixkplrgobgwqnhidwt.supabase.co' -or $bundle.purpose -ne 'A24_TECHNICAL_ISOLATION_ONLY' -or $bundle.accounts.Count -ne 2) { throw 'BUNDLE_REFUSED' }
        $stage = 'ANON_KEY'
        $anon = [Environment]::GetEnvironmentVariable('SUPABASE_ANON_KEY','Process')
        if ([string]::IsNullOrWhiteSpace($anon)) {
            $secure = Read-Host 'SUPABASE_ANON_KEY Integration Test uniquement (saisie masquee)' -AsSecureString
            $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
            try { $anon = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
        }
        if ([string]::IsNullOrWhiteSpace($anon)) { throw 'ANON_KEY_ABSENT' }
        $stage = 'READ_REHEARSAL'
        $env:PEPPERYN_ISOLATION_BOOTSTRAP = $json
        $env:PEPPERYN_ISOLATION_ANON_KEY = $anon
        $rehearsalArguments = @('-B', '-W', 'ignore', $source)
        $expectedStatus = 'BOUNDED_TWO_USER_READ_ISOLATION_PASS'
        if ($IncludeHistory) {
            $rehearsalArguments += '--include-history'
            $expectedStatus = 'BOUNDED_HISTORY_SCOPE_READ_PASS'
        }
        $output = & $python @rehearsalArguments 2>$null
        $pythonExit = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($pythonExit -ne 0 -or $result.status -ne $expectedStatus) {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            throw 'REHEARSAL_REFUSED'
        }
        $stage = 'RESULT_GATE'
        if ($result.global_isolation_proven -ne $false -or $result.business_write_performed -ne $false -or $result.external_provider_used -ne $false -or $result.real_data_used -ne $false) { throw 'RESULT_REFUSED' }
        if ($result.populated_history_isolation_proven -ne $false -or $result.write_isolation_proven -ne $false -or $result.analysis_export_isolation_proven -ne $false -or $result.production_proof -ne $false) { throw 'PROOF_SCOPE_REFUSED' }
        if ((Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash -ne $beforeHash) { throw 'BUNDLE_CHANGED' }
        $result | ConvertTo-Json -Depth 5 -Compress | Write-Output
        Write-Output 'EXISTING_DPAPI_UNCHANGED: PASS; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "A24_READ_REHEARSAL_REFUSED_STAGE: $stage"
    Write-Output 'No account creation, reset, deletion or business write attempted. Report this stage; do not regenerate credentials.'
} finally {
    $env:PEPPERYN_ISOLATION_BOOTSTRAP = $previousBundle
    $env:PEPPERYN_ISOLATION_ANON_KEY = $previousAnon
    $json = $null; $bundle = $null; $anon = $null; $output = $null
}
exit $exitCode
