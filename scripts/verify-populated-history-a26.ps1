param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_PREFLIGHT'
$exitCode = 1
$secretFile = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\secrets\a24-isolation-accounts.dpapi'
$source = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend\sandbox\verify_populated_history.py'
$python = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$expected = '3C850754B93BA236B2E7F5E67A8A22A3DBA742D11B0868E26884533F650A4477'
$previousBundle = $env:PEPPERYN_ISOLATION_BOOTSTRAP
$previousAnon = $env:PEPPERYN_ISOLATION_ANON_KEY
$previousService = $env:PEPPERYN_ISOLATION_SERVICE_KEY
$previousPath = $env:PYTHONPATH
try {
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $expected) { throw 'SOURCE_HASH_MISMATCH' }
    if (-not (Test-Path -LiteralPath $secretFile -PathType Leaf)) { throw 'EXISTING_BUNDLE_ABSENT' }
    if ($CheckOnly) {
        Write-Output 'A26_POPULATED_READ_PREFLIGHT: PASS. No secrets read; no network; no writes.'
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
        $stage = 'READ_REHEARSAL'
        $env:PEPPERYN_ISOLATION_BOOTSTRAP = $json
        $env:PEPPERYN_ISOLATION_ANON_KEY = $anon
        $env:PEPPERYN_ISOLATION_SERVICE_KEY = $service
        $env:PYTHONPATH = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend'
        $rehearsalArguments = @('-B', '-W', 'ignore', $source)
        $expectedStatus = 'BOUNDED_POPULATED_HISTORY_ISOLATION_PASS'
        $output = & $python @rehearsalArguments 2>$null
        $pythonExit = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($pythonExit -ne 0 -or $result.status -ne $expectedStatus) {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            throw 'REHEARSAL_REFUSED'
        }
        $stage = 'RESULT_GATE'
        if ($result.proof_scope -ne 'A26_TWO_SEEDED_ANALYSES_HISTORY_GET_ONLY') { throw 'SCOPE_REFUSED' }
        if ($result.engagement_reference_authority -ne 'SERVICE_READ_ONLY' -or $result.history_probe_authority -ne 'USER_SESSIONS_ONLY') { throw 'AUTHORITY_REFUSED' }
        if ($result.global_isolation_proven -ne $false -or $result.business_write_performed -ne $false -or $result.external_provider_used -ne $false -or $result.real_data_used -ne $false) { throw 'RESULT_REFUSED' }
        if ($result.populated_history_isolation_proven -ne $true -or $result.write_isolation_proven -ne $false -or $result.analysis_export_isolation_proven -ne $false -or $result.production_proof -ne $false) { throw 'PROOF_SCOPE_REFUSED' }
        if ((Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash -ne $beforeHash) { throw 'BUNDLE_CHANGED' }
        $result | ConvertTo-Json -Depth 5 -Compress | Write-Output
        Write-Output 'EXISTING_DPAPI_UNCHANGED: PASS; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "A26_POPULATED_READ_REFUSED_STAGE: $stage"
    Write-Output 'No account creation, reset, deletion or business write attempted. Report this stage; do not regenerate credentials.'
} finally {
    $env:PEPPERYN_ISOLATION_BOOTSTRAP = $previousBundle
    $env:PEPPERYN_ISOLATION_ANON_KEY = $previousAnon
    $env:PEPPERYN_ISOLATION_SERVICE_KEY = $previousService
    $env:PYTHONPATH = $previousPath
    $json = $null; $bundle = $null; $anon = $null; $service = $null; $value = $null; $output = $null
}
exit $exitCode
