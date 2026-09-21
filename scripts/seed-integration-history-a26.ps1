param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_PREFLIGHT'
$exitCode = 1
$secretFile = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\secrets\a24-isolation-accounts.dpapi'
$source = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend\sandbox\seed_isolation_history.py'
$python = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$expected = '5B733140F22A1016C52DFA755FB606EB97AD3CFBCECADBEBD5D2A1BC353691F9'
$previousBundle = $env:PEPPERYN_ISOLATION_BOOTSTRAP
$previousAnon = $env:PEPPERYN_ISOLATION_ANON_KEY
$previousService = $env:PEPPERYN_ISOLATION_SERVICE_KEY
$previousPath = $env:PYTHONPATH
$previousAuthorization = $env:PEPPERYN_A26_SEED_AUTHORIZATION
try {
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $expected) { throw 'SOURCE_HASH_MISMATCH' }
    if (-not (Test-Path -LiteralPath $secretFile -PathType Leaf)) { throw 'EXISTING_BUNDLE_ABSENT' }
    if ($CheckOnly) {
        Write-Output 'A26_CONTROLLED_SEED_PREFLIGHT: PASS. No secrets read; no network; no writes.'
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
        $stage = 'CONTROLLED_SEED'
        $env:PEPPERYN_A26_SEED_AUTHORIZATION = 'A26_TWO_SYNTHETIC_PAIRS_ONLY'
        $env:PEPPERYN_ISOLATION_BOOTSTRAP = $json
        $env:PEPPERYN_ISOLATION_ANON_KEY = $anon
        $env:PEPPERYN_ISOLATION_SERVICE_KEY = $service
        $env:PYTHONPATH = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend'
        $rehearsalArguments = @('-B', '-W', 'ignore', $source)
        $expectedStatus = 'A26_SYNTHETIC_PAIRS_SEEDED'
        $output = & $python @rehearsalArguments 2>$null
        $pythonExit = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($pythonExit -ne 0 -or $result.status -ne $expectedStatus) {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            if ($result.status -eq 'REFUSED') { $result | ConvertTo-Json -Depth 4 -Compress | Write-Output }
            throw 'REHEARSAL_REFUSED'
        }
        $stage = 'RESULT_GATE'
        if ($result.acknowledged_pairs -ne 2 -or $result.verified_pairs -ne 2) { throw 'PAIR_COUNT_REFUSED' }
        if ($result.global_isolation_proven -ne $false -or $result.business_write_performed -ne $true -or $result.external_provider_used -ne $false -or $result.real_data_used -ne $false) { throw 'RESULT_REFUSED' }
        if ($result.populated_history_isolation_proven -ne $false -or $result.write_isolation_proven -ne $false -or $result.analysis_export_isolation_proven -ne $false -or $result.production_proof -ne $false) { throw 'PROOF_SCOPE_REFUSED' }
        if ((Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash -ne $beforeHash) { throw 'BUNDLE_CHANGED' }
        $result | ConvertTo-Json -Depth 5 -Compress | Write-Output
        Write-Output 'EXISTING_DPAPI_UNCHANGED: PASS; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "A26_CONTROLLED_SEED_REFUSED_STAGE: $stage"
    Write-Output 'Writes may have occurred if Python was launched. Do not rerun or delete anything; report this stage and safe diagnostic.'
} finally {
    $env:PEPPERYN_ISOLATION_BOOTSTRAP = $previousBundle
    $env:PEPPERYN_ISOLATION_ANON_KEY = $previousAnon
    $env:PEPPERYN_ISOLATION_SERVICE_KEY = $previousService
    $env:PYTHONPATH = $previousPath
    $env:PEPPERYN_A26_SEED_AUTHORIZATION = $previousAuthorization
    $json = $null; $bundle = $null; $anon = $null; $service = $null; $value = $null; $output = $null
}
exit $exitCode
