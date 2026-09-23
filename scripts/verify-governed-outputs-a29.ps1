param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_PREFLIGHT'
$exitCode = 1
$source = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend\sandbox\verify_governed_output_isolation.py'
$python = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$bundleFile = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\secrets\a24-isolation-accounts.dpapi'
$jwtFile = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\secrets\jwt-guest-integration\jwt-guest-secret.dpapi'
$names = @('PEPPERYN_ISOLATION_BOOTSTRAP','PEPPERYN_ISOLATION_ANON_KEY','PEPPERYN_ISOLATION_SERVICE_KEY','JWT_GUEST_SECRET','ENVIRONMENT','PYTHONPATH')
$old = @{}
foreach ($n in $names) { $old[$n] = [Environment]::GetEnvironmentVariable($n,'Process') }
try {
    foreach ($p in @($source,$python,$bundleFile,$jwtFile)) { if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw 'FILE_ABSENT' } }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne '9A0609149DB87CB1F2C02ADD350E76D1ECE70966E498B8BDD584E802A63D16A8') { throw 'SOURCE_CHANGED' }
    if ($CheckOnly) {
        Write-Output 'A29_PREFLIGHT: PASS. No secrets read; no network; no writes.'
        $exitCode = 0
    } else {
        Add-Type -AssemblyName System.Security
        $bundleHash = (Get-FileHash -LiteralPath $bundleFile -Algorithm SHA256).Hash
        $jwtHash = (Get-FileHash -LiteralPath $jwtFile -Algorithm SHA256).Hash
        function RestoreExisting($file,$entropyText) {
            $entropy = [Text.Encoding]::UTF8.GetBytes($entropyText)
            $plain = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($file),$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
            try { return (New-Object Text.UTF8Encoding($false,$true)).GetString($plain) }
            finally { [Array]::Clear($plain,0,$plain.Length) }
        }
        $stage = 'EXISTING_DPAPI_RESTORE'
        $bundle = RestoreExisting $bundleFile 'Pepperyn|IntegrationTest|A24IsolationAccounts|v1'
        $jwt = RestoreExisting $jwtFile 'Pepperyn|IntegrationTest|JWT_GUEST_SECRET|v1'
        if ($jwt -notmatch '^[A-Za-z0-9+/]{64}$') { throw 'JWT_FORMAT_REFUSED' }
        $env:PEPPERYN_ISOLATION_BOOTSTRAP = $bundle
        $env:JWT_GUEST_SECRET = $jwt
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
            if ($name -eq 'SUPABASE_ANON_KEY') { $env:PEPPERYN_ISOLATION_ANON_KEY = $value }
            else { $env:PEPPERYN_ISOLATION_SERVICE_KEY = $value }
            $value = $null
        }
        $env:ENVIRONMENT = 'development'
        $env:PYTHONPATH = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend;C:\Users\ADMIN-FRED\Documents\Codex\2026-08-31\use-this-local-repository-as-the\test-dependencies-a27'
        $stage = 'READ_ONLY_ASGI'
        $output = & $python -B -W ignore $source 2>$null
        $code = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($code -ne 0 -or $result.status -ne 'BOUNDED_A29_ASGI_OUTPUT_ISOLATION_PASS') {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            throw 'REHEARSAL_REFUSED'
        }
        $stage = 'RESULT_GATE'
        if ($result.proof_scope -ne 'REAL_USER_SESSIONS_PERSISTED_A26_ISOLATED_ASGI_GET_ONLY' -or $result.positive_outputs -ne 8 -or $result.denials -ne 24) { throw 'SCOPE_REFUSED' }
        foreach ($field in @('business_write_performed','live_server_transport_proven','global_isolation_proven','write_isolation_proven','production_proof','external_provider_used','real_data_used')) {
            if ($result.$field -ne $false) { throw 'PROOF_SCOPE_REFUSED' }
        }
        if ((Get-FileHash -LiteralPath $bundleFile -Algorithm SHA256).Hash -ne $bundleHash -or (Get-FileHash -LiteralPath $jwtFile -Algorithm SHA256).Hash -ne $jwtHash) { throw 'DPAPI_CHANGED' }
        $result | ConvertTo-Json -Compress | Write-Output
        Write-Output 'EXISTING_DPAPI_UNCHANGED: PASS; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "A29_REFUSED_STAGE: $stage"
    Write-Output 'No business-write route or seed was invoked. Report this safe stage; do not change persisted fixtures.'
} finally {
    foreach ($n in $names) { [Environment]::SetEnvironmentVariable($n,$old[$n],'Process') }
    $bundle = $null; $jwt = $null; $value = $null; $output = $null
}
exit $exitCode
