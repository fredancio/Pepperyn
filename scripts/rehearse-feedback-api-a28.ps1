param([switch]$CheckOnly, [switch]$ExistingOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_PREFLIGHT'
$exitCode = 1
$secretFile = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\secrets\a24-isolation-accounts.dpapi'
$source = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend\sandbox\rehearse_feedback_api.py'
$python = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$expected = '9079AED6BC68BCD64BF0597702C021DC08703FE2E45D63FF671588FB8D640C72'
$previousBundle = $env:PEPPERYN_ISOLATION_BOOTSTRAP
$previousAnon = $env:PEPPERYN_ISOLATION_ANON_KEY
$previousService = $env:PEPPERYN_ISOLATION_SERVICE_KEY
$previousPath = $env:PYTHONPATH
$previousAuthorization = $env:PEPPERYN_A28_AUTHORIZATION
$previousMode = $env:PEPPERYN_A28_MODE
try {
    if (-not $ExistingOnly) { throw 'EXISTING_ONLY_REQUIRED' }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $expected) { throw 'SOURCE_HASH_MISMATCH' }
    if (-not (Test-Path -LiteralPath $secretFile -PathType Leaf)) { throw 'EXISTING_BUNDLE_ABSENT' }
    if ($CheckOnly) {
        Write-Output 'A28_API_PREFLIGHT: PASS. No secrets read; no network; no writes.'
        $exitCode = 0
    } else {
        $stage = 'BACKEND_REVISION'
        $schema = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/openapi.json' -TimeoutSec 8
        if ($schema.paths.'/api/decision-feedback'.post.'x-pepperyn-write-authority' -ne 'owned-persisted-recommendation-v1') { throw 'RELOAD_REQUIRED' }
        $beforeHash = (Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash
        $stage = 'EXISTING_DPAPI_RESTORE'
        Add-Type -AssemblyName System.Security
        $entropy = [Text.Encoding]::UTF8.GetBytes('Pepperyn|IntegrationTest|A24IsolationAccounts|v1')
        $plain = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($secretFile),$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        $json = [Text.Encoding]::UTF8.GetString($plain)
        [Array]::Clear($plain,0,$plain.Length)
        $bundle = $json | ConvertFrom-Json
        if ($bundle.project_url -ne 'https://ejixkplrgobgwqnhidwt.supabase.co' -or $bundle.purpose -ne 'A24_TECHNICAL_ISOLATION_ONLY' -or $bundle.accounts.Count -ne 2) { throw 'BUNDLE_REFUSED' }
        foreach ($name in @('SUPABASE_ANON_KEY','SUPABASE_SERVICE_KEY')) {
            $stage = $name + '_AVAILABILITY'
            $value = [Environment]::GetEnvironmentVariable($name,'Process')
            if ([string]::IsNullOrWhiteSpace($value)) {
                $secure = Read-Host "$name Integration Test uniquement (saisie masquee)" -AsSecureString
                $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
                try { $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
                finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
            }
            if ([string]::IsNullOrWhiteSpace($value)) { throw 'KEY_ABSENT' }
            if ($name -eq 'SUPABASE_ANON_KEY') { $anon = $value } else { $service = $value }
            $value = $null
        }
        $stage = 'AUTHORIZED_REHEARSAL'
        $env:PEPPERYN_A28_AUTHORIZATION = 'A28_TWO_LEGACY_FIXTURES_UNSURE_AND_PATTERNS_ONLY'
        $env:PEPPERYN_A28_MODE = 'EXISTING_ONLY'
        $env:PEPPERYN_ISOLATION_BOOTSTRAP = $json
        $env:PEPPERYN_ISOLATION_ANON_KEY = $anon
        $env:PEPPERYN_ISOLATION_SERVICE_KEY = $service
        $env:PYTHONPATH = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend'
        $rehearsalArguments = @('-B', '-W', 'ignore', $source)
        $expectedStatus = 'BOUNDED_LEGACY_FEEDBACK_API_ISOLATION_PASS'
        $output = & $python @rehearsalArguments 2>$null
        $pythonExit = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($pythonExit -ne 0 -or $result.status -ne $expectedStatus) {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            throw 'REHEARSAL_REFUSED'
        }
        $stage = 'RESULT_GATE'
        if ($result.proof_scope -ne 'A28_TWO_LEGACY_UNSURE_API_WRITES_ONLY') { throw 'SCOPE_REFUSED' }
        if ($result.continuation_existing_only -ne $true -or $result.existing_fixtures_verified -ne 2 -or $result.authorized_fixture_inserts -ne 0 -or $result.authorized_unsure_writes -ne 2 -or $result.authorized_pattern_rows_verified -ne 2 -or $result.adversarial_refusals -ne 15) { throw 'COUNTS_REFUSED' }
        foreach ($field in @('a26_pairs_unchanged','business_write_performed','api_write_isolation_proven')) {
            if ($result.$field -ne $true) { throw 'POSITIVE_PROOF_REFUSED' }
        }
        foreach ($field in @('arcs_created','write_isolation_proven','analysis_export_isolation_proven','global_isolation_proven','production_proof','external_provider_used','real_data_used')) {
            if ($result.$field -ne $false) { throw 'PROOF_SCOPE_REFUSED' }
        }
        if ((Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash -ne $beforeHash) { throw 'BUNDLE_CHANGED' }
        $result | ConvertTo-Json -Depth 5 -Compress | Write-Output
        Write-Output 'EXISTING_DPAPI_UNCHANGED: PASS; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "A28_API_REFUSED_STAGE: $stage"
    if ($result -and $result.status -eq 'REFUSED') {
        foreach ($field in @('seed_attempts','seed_acknowledged','authorized_post_attempts','authorized_post_acknowledged','negative_post_attempts')) {
            $count = 0
            if ([int]::TryParse([string]$result.$field, [ref]$count)) { Write-Output ($field + ': ' + $count) }
        }
        foreach ($field in @('observed_http_status','expected_http_status')) {
            $code = 0
            if ([int]::TryParse([string]$result.$field, [ref]$code) -and $code -ge 100 -and $code -le 599) { Write-Output ($field + ': ' + $code) }
        }
    }
    Write-Output 'Partial authorized writes may exist. Do not rerun, reseed, delete or regenerate credentials. Report only this safe diagnostic.'
} finally {
    $env:PEPPERYN_ISOLATION_BOOTSTRAP = $previousBundle
    $env:PEPPERYN_ISOLATION_ANON_KEY = $previousAnon
    $env:PEPPERYN_ISOLATION_SERVICE_KEY = $previousService
    $env:PYTHONPATH = $previousPath
    $env:PEPPERYN_A28_AUTHORIZATION = $previousAuthorization
    $env:PEPPERYN_A28_MODE = $previousMode
    $json = $null; $bundle = $null; $anon = $null; $service = $null; $value = $null; $output = $null
}
exit $exitCode
