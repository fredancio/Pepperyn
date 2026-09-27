param([switch]$CheckOnly)
# Run with Windows PowerShell -NoExit: credentials remain only in that process.
# No server, network, permit creation/reset, credential generation or file write.
& {
    $ErrorActionPreference = 'Stop'
    $stage = 'CLOSED_ATTEMPT_INTEGRITY'
    $runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
    $manifest = Join-Path $runtime 'b1-connected-rehearsal.json'
    $closed = Join-Path $runtime 'b1-connected-rehearsal.closed'
    $jwtFile = Join-Path $runtime 'secrets\jwt-guest-integration\jwt-guest-secret.dpapi'
    $names = @('ENVIRONMENT','SUPABASE_URL','SUPABASE_ANON_KEY','SUPABASE_SERVICE_KEY','JWT_GUEST_SECRET',
        'PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO','PEPPERYN_SYNTHETIC_V1_COMPANY_ID',
        'PEPPERYN_TRUST_GATE_SLICE1','PEPPERYN_GOVERNED_PIPELINE_TRANSPORT',
        'PEPPERYN_GOVERNED_REHEARSAL_MANIFEST','CORS_ORIGINS')
    $previous = @{}
    $success = $false
    $changed = $false
    $jwt = $null
    $keys = @{}
    try {
        if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ne 'A68F439F3267C1E5B6E3C128B7BD079D0F8EC6832209818CB35095B4D502DF14' -or
            (Get-FileHash -LiteralPath $closed -Algorithm SHA256).Hash -ne 'D565E1E2EDC2024F2A9DBC529B03C620F4556F3301C152CF2ECD1A094332430C') { throw 'PRIOR_EVIDENCE_CHANGED' }
        if ((Test-Path -LiteralPath (Join-Path $runtime 'b1-connected-rehearsal.attempt')) -or
            (Test-Path -LiteralPath (Join-Path $runtime 'b1-connected-rehearsal.activated'))) { throw 'ATTEMPT_STATE_REQUIRES_INSPECTION' }
        if ($CheckOnly) {
            Write-Output 'B1_ENVIRONMENT_PREPARATION_CHECK: PASS. DPAPI not read; no network or environment change.'
            return
        }
        foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
        $stage = 'EXISTING_JWT_DPAPI_RESTORE'
        Add-Type -AssemblyName System.Security
        $jwtBefore = (Get-FileHash -LiteralPath $jwtFile -Algorithm SHA256).Hash
        $entropy = [Text.Encoding]::UTF8.GetBytes('Pepperyn|IntegrationTest|JWT_GUEST_SECRET|v1')
        $plain = [Security.Cryptography.ProtectedData]::Unprotect(
            [IO.File]::ReadAllBytes($jwtFile),$entropy,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        try { $jwt = (New-Object Text.UTF8Encoding($false,$true)).GetString($plain) }
        finally { [Array]::Clear($plain,0,$plain.Length) }
        if ($jwt -notmatch '^[A-Za-z0-9+/]{64}$') { throw 'EXISTING_JWT_FORMAT_REFUSED' }
        if ($previous['JWT_GUEST_SECRET'] -and $previous['JWT_GUEST_SECRET'] -cne $jwt) { throw 'JWT_SOURCES_DISAGREE' }
        foreach ($name in @('SUPABASE_ANON_KEY','SUPABASE_SERVICE_KEY')) {
            $stage = $name + '_LOCAL_AVAILABILITY'
            $value = $previous[$name]
            if ([string]::IsNullOrWhiteSpace($value)) {
                $secure = Read-Host "$name - Pepperyn Integration Test uniquement (saisie masquee)" -AsSecureString
                $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
                try { $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
                finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
            }
            if ([string]::IsNullOrWhiteSpace($value)) { throw 'KEY_MISSING' }
            $keys[$name] = $value
            $value = $null
        }
        $stage = 'SOURCE_INTEGRITY_RECHECK'
        if ((Get-FileHash -LiteralPath $jwtFile -Algorithm SHA256).Hash -ne $jwtBefore -or
            (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ne 'A68F439F3267C1E5B6E3C128B7BD079D0F8EC6832209818CB35095B4D502DF14' -or
            (Get-FileHash -LiteralPath $closed -Algorithm SHA256).Hash -ne 'D565E1E2EDC2024F2A9DBC529B03C620F4556F3301C152CF2ECD1A094332430C') { throw 'SOURCE_CHANGED' }
        $stage = 'PROCESS_ENVIRONMENT_LOAD'
        $changed = $true
        $env:ENVIRONMENT = 'development'
        $env:SUPABASE_URL = 'https://ejixkplrgobgwqnhidwt.supabase.co'
        $env:PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO = '1'
        $env:PEPPERYN_SYNTHETIC_V1_COMPANY_ID = '89644cea-1e5c-478a-b797-b34d646064be'
        $env:PEPPERYN_TRUST_GATE_SLICE1 = '1'
        $env:PEPPERYN_GOVERNED_PIPELINE_TRANSPORT = '0'
        [Environment]::SetEnvironmentVariable('PEPPERYN_GOVERNED_REHEARSAL_MANIFEST',$null,'Process')
        $env:CORS_ORIGINS = 'http://localhost:3000,http://127.0.0.1:3000'
        $env:SUPABASE_ANON_KEY = $keys['SUPABASE_ANON_KEY']
        $env:SUPABASE_SERVICE_KEY = $keys['SUPABASE_SERVICE_KEY']
        $env:JWT_GUEST_SECRET = $jwt
        $success = $true
        Write-Output 'B1_TEMPORARY_ENVIRONMENT: LOADED_IN_THIS_PROCESS'
        Write-Output 'EXISTING_JWT_DPAPI: RESTORED_UNCHANGED; SUPABASE_KEYS: PRESENT_NOT_REMOTE_VALIDATED'
        Write-Output 'PREVIOUS_PERMIT: CLOSED_UNCHANGED; NEW_PERMIT: NOT_CREATED; TRANSPORT: DISABLED; BACKEND_STARTED: NO'
        Write-Output 'V33_UNTOUCHED; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        Write-Output 'Keep this PowerShell open. Do not run the old preflight/start scripts.'
    } catch {
        Write-Output "B1_ENVIRONMENT_PREPARATION_REFUSED_STAGE: $stage"
        Write-Output 'No activation or permit reset. No secret generated or displayed. Stop and report this stage.'
    } finally {
        if ($changed -and -not $success) {
            foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
        }
        $jwt = $null; $value = $null; $keys.Clear(); $previous.Clear()
    }
}
