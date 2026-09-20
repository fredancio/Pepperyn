param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_PREFLIGHT'
$scriptExit = 1
$secretFile = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\secrets\a24-isolation-accounts.dpapi'
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$python = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\provision_isolation_accounts.py'
$expected = 'AEE2E71B03AFCA3C97708D4D3316CAAEFB1A14D208CF35EF77B52232A61B5496'
$ephemeralNames = @('PEPPERYN_ISOLATION_BOOTSTRAP','PEPPERYN_ISOLATION_SERVICE_KEY','PEPPERYN_ISOLATION_ANON_KEY')
$saved = @{}
foreach ($name in $ephemeralNames) { $saved[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
function Read-LocalKey([string]$Name) {
    $existing = [Environment]::GetEnvironmentVariable($Name,'Process')
    if (-not [string]::IsNullOrWhiteSpace($existing)) { return $existing }
    $secure = Read-Host "Saisir localement $Name de Pepperyn Integration Test (saisie masquee)" -AsSecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
}
try {
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $expected) { throw 'SOURCE_HASH_MISMATCH' }
    if (Test-Path -LiteralPath $secretFile) { $stage = 'EXISTING_ATTEMPT_REFUSED'; throw 'DO_NOT_RETRY' }
    Add-Type -AssemblyName System.Security
    if ($CheckOnly) {
        Write-Output 'A24_LOCAL_PREFLIGHT: PASS. No credentials read; no file written; no network.'
        $scriptExit = 0
    } else {
        $stage = 'LOCAL_KEYS'
        $service = Read-LocalKey 'SUPABASE_SERVICE_KEY'
        $anon = Read-LocalKey 'SUPABASE_ANON_KEY'
        if ([string]::IsNullOrWhiteSpace($service) -or [string]::IsNullOrWhiteSpace($anon) -or $service -eq $anon) { throw 'KEYS_REFUSED' }
        $stage = 'PROTECTED_CREDENTIALS'
        $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
        $accounts = @()
        try {
            foreach ($suffix in @('a','b')) {
                $randomBytes = New-Object byte[] 48
                $rng.GetBytes($randomBytes)
                $accounts += @{ email = "pepperyn-isolation-a24-$suffix@pepperyn-test.invalid"; password = [Convert]::ToBase64String($randomBytes) }
                [Array]::Clear($randomBytes,0,$randomBytes.Length)
            }
        } finally { $rng.Dispose() }
        $bundle = @{ project_url = 'https://ejixkplrgobgwqnhidwt.supabase.co'; purpose = 'A24_TECHNICAL_ISOLATION_ONLY'; accounts = $accounts; dpapi_roundtrip_verified = $true }
        $json = $bundle | ConvertTo-Json -Depth 5 -Compress
        $plain = [Text.Encoding]::UTF8.GetBytes($json)
        $entropy = [Text.Encoding]::UTF8.GetBytes('Pepperyn|IntegrationTest|A24IsolationAccounts|v1')
        $cipher = [Security.Cryptography.ProtectedData]::Protect($plain,$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        $parent = Split-Path -Parent $secretFile
        if (-not (Test-Path -LiteralPath $parent -PathType Container)) { throw 'SECRETS_DIRECTORY_ABSENT' }
        # CreateNew is both the one-attempt guard and durable recovery record.
        # Never overwrite/delete this file on error: remote creation may have happened.
        $stream = [IO.File]::Open($secretFile,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try { $stream.Write($cipher,0,$cipher.Length); $stream.Flush($true) } finally { $stream.Dispose() }
        $restored = [Security.Cryptography.ProtectedData]::Unprotect([IO.File]::ReadAllBytes($secretFile),$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        if ([Text.Encoding]::UTF8.GetString($restored) -cne $json) { throw 'DPAPI_ROUNDTRIP_FAILED' }
        [Array]::Clear($plain,0,$plain.Length)
        [Array]::Clear($restored,0,$restored.Length)
        $stage = 'PROVISION_AND_VERIFY'
        $env:PEPPERYN_ISOLATION_BOOTSTRAP = $json
        $env:PEPPERYN_ISOLATION_SERVICE_KEY = $service
        $env:PEPPERYN_ISOLATION_ANON_KEY = $anon
        # Standalone file, not python -c; no application startup or provider imports.
        $output = & $python -B -W ignore $source 2>$null
        $processExit = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($processExit -ne 0 -or $result.status -ne 'ACCOUNTS_CREATED_SCOPE_VERIFIED') {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            throw 'PROVISION_REFUSED'
        }
        if ($result.accounts_created -ne 2 -or $result.distinct_users_companies_entities -ne $true -or $result.adversarial_isolation_proven -ne $false) { throw 'RESULT_REFUSED' }
        Write-Output 'A24_TECHNICAL_ACCOUNTS: CREATED_AND_SCOPE_VERIFIED'
        Write-Output 'WINDOWS_DPAPI_CURRENT_USER: PASS'
        Write-Output 'TWO_USER_ADVERSARIAL_ISOLATION: NOT_YET_PROVEN'
        Write-Output 'EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $scriptExit = 0
    }
} catch {
    Write-Output "A24_REFUSED_STAGE: $stage"
    Write-Output 'Do not rerun. Preserve the DPAPI file: remote partial creation may exist. No secret displayed.'
} finally {
    foreach ($name in $ephemeralNames) { [Environment]::SetEnvironmentVariable($name,$saved[$name],'Process') }
    $service = $null; $anon = $null; $json = $null; $bundle = $null; $accounts = $null; $output = $null
}
exit $scriptExit
