param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_PREFLIGHT'
$exitCode = 1
$source = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend\sandbox\verify_governed_output_isolation.py'
$python = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$bundleFile = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\secrets\a24-isolation-accounts.dpapi'
$jwtFile = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\secrets\jwt-guest-integration\jwt-guest-secret.dpapi'
$names = @('PEPPERYN_ISOLATION_BOOTSTRAP','PEPPERYN_ISOLATION_ANON_KEY','PEPPERYN_ISOLATION_SERVICE_KEY','JWT_GUEST_SECRET','ENVIRONMENT','PYTHONPATH','PEPPERYN_OUTPUT_TRANSPORT','PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO')
$old = @{}
foreach ($n in $names) { $old[$n] = [Environment]::GetEnvironmentVariable($n,'Process') }
try {
    foreach ($p in @($source,$python,$bundleFile,$jwtFile)) { if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { throw 'FILE_ABSENT' } }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne '48EF092109A26109DB0DB2E807EB330315F36FC18801D70DDF15EFC56AEA3EFD') { throw 'SOURCE_CHANGED' }
    if ((Get-FileHash -LiteralPath 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend\sandbox\output_live_transport.py' -Algorithm SHA256).Hash -ne 'BF8933E71059ED7D602A7076129C02B87B1EF2A7597BE37FDCF6CD39CC986FFB') { throw 'TRANSPORT_CHANGED' }
    if ($CheckOnly) {
        Write-Output 'A30_PREFLIGHT: PASS. No secrets read; no network; no writes.'
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
        $env:PEPPERYN_OUTPUT_TRANSPORT = 'A30_UVICORN'
        $env:PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO = '1'
        $env:PYTHONPATH = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development\backend;C:\Users\ADMIN-FRED\Documents\Codex\2026-08-31\use-this-local-repository-as-the\test-dependencies-a27'
        $stage = 'READ_ONLY_ASGI'
        $output = & $python -B -W ignore $source 2>$null
        $code = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($code -ne 0 -or $result.status -ne 'BOUNDED_A30_UVICORN_OUTPUT_ISOLATION_PASS') {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            throw 'REHEARSAL_REFUSED'
        }
        $stage = 'RESULT_GATE'
        if ($result.proof_scope -ne 'REAL_SESSIONS_A26_TEMPORARY_LOOPBACK_UVICORN_READ_SURFACE' -or $result.positive_outputs -ne 8 -or $result.denials -ne 24) { throw 'SCOPE_REFUSED' }
        if ($result.live_server_transport_proven -ne $true) { throw 'TRANSPORT_NOT_PROVEN' }
        foreach ($field in @('business_write_performed','global_isolation_proven','write_isolation_proven','production_proof','external_provider_used','real_data_used')) {
            if ($result.$field -ne $false) { throw 'PROOF_SCOPE_REFUSED' }
        }
        if ((Get-FileHash -LiteralPath $bundleFile -Algorithm SHA256).Hash -ne $bundleHash -or (Get-FileHash -LiteralPath $jwtFile -Algorithm SHA256).Hash -ne $jwtHash) { throw 'DPAPI_CHANGED' }
        $result | ConvertTo-Json -Compress | Write-Output
        Write-Output 'EXISTING_DPAPI_UNCHANGED: PASS; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "A30_REFUSED_STAGE: $stage"
    Write-Output 'No business-write route or seed was invoked. Report this safe stage; do not change persisted fixtures.'
} finally {
    foreach ($n in $names) { [Environment]::SetEnvironmentVariable($n,$old[$n],'Process') }
    $bundle = $null; $jwt = $null; $value = $null; $output = $null
}
exit $exitCode
