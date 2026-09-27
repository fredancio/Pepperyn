param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'PERMIT_INTEGRITY'
$exitCode = 1
$closeOnExit = $false
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$manifest = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\b1-connected-rehearsal-r2.json'
$closed = [IO.Path]::ChangeExtension($manifest,'.closed')
$anon = $null
try {
    if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ne '457403C3E5812E6A978C14CC0CC00DCBB5A1CEE520F18C87C0740FBC18F51B46') { throw 'PERMIT_CHANGED' }
    if (-not $CheckOnly) { $closeOnExit = $true }
    $permit = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    if ([DateTimeOffset]::Parse($permit.expires_at).UtcDateTime -le [DateTime]::UtcNow -or
        (Test-Path -LiteralPath $closed) -or
        (Test-Path -LiteralPath ([IO.Path]::ChangeExtension($manifest,'.attempt'))) -or
        -not (Test-Path -LiteralPath ([IO.Path]::ChangeExtension($manifest,'.activated')))) { throw 'PERMIT_NOT_READY' }
    $stage = 'FRONTEND_RUNTIME'
    $node = (Get-Command node.exe -ErrorAction Stop).Source
    if (-not (Test-Path -LiteralPath (Join-Path $repo 'frontend\node_modules\next\dist\bin\next'))) { throw 'NEXT_ABSENT' }
    if ($CheckOnly) {
        Write-Output 'B1_R2_FRONTEND_CHECK: PASS. No network, activation, secret access or write.'
        $exitCode = 0
    } else {
        $stage = 'PORT_3000_MUST_BE_FREE'
        $listeners = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
        if (@($listeners | Where-Object { $_.Port -eq 3000 }).Count -ne 0) { throw 'PORT_IN_USE_NO_KILL' }
        $stage = 'BACKEND_ROUTE_CHECK'
        $schema = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/openapi.json' -TimeoutSec 5
        if (-not $schema.paths.PSObject.Properties['/api/governed/analyses']) { throw 'ROUTE_ABSENT' }
        $stage = 'PUBLIC_ANON_KEY'
        $anon = $env:NEXT_PUBLIC_SUPABASE_ANON_KEY
        if ([string]::IsNullOrWhiteSpace($anon)) {
            $masked = Read-Host 'Cle publique anon Supabase Integration Test (jamais service_role)' -AsSecureString
            $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($masked)
            try { $anon = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr); $masked.Dispose() }
        }
        # Accept only the existing project's legacy public anon JWT, never a service key.
        $parts = $anon.Split('.')
        if ($parts.Count -ne 3) { throw 'PUBLIC_ANON_FORMAT_REFUSED' }
        $payload = $parts[1].Replace('-','+').Replace('_','/')
        while (($payload.Length % 4) -ne 0) { $payload += '=' }
        $claims = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload)) | ConvertFrom-Json
        if ($claims.role -ne 'anon' -or $claims.ref -ne 'ejixkplrgobgwqnhidwt') { throw 'PUBLIC_ANON_SCOPE_REFUSED' }
        # This script runs in a child PowerShell; the parent/backend environment is untouched.
        foreach ($name in @('SUPABASE_SERVICE_KEY','SUPABASE_SERVICE_ROLE_KEY','JWT_GUEST_SECRET','PEPPERYN_CORRESPONDENCE_KEY','OPENAI_API_KEY','ANTHROPIC_API_KEY')) {
            [Environment]::SetEnvironmentVariable($name,$null,'Process')
        }
        $env:NEXT_PUBLIC_SUPABASE_URL = 'https://ejixkplrgobgwqnhidwt.supabase.co'
        $env:NEXT_PUBLIC_SUPABASE_ANON_KEY = $anon
        $env:NEXT_PUBLIC_API_URL = 'http://127.0.0.1:8000'
        $env:NEXT_PUBLIC_ENABLE_SYNTHETIC_V1_DEMO = '1'
        $env:NEXT_PUBLIC_GOVERNED_PIPELINE_TRANSPORT = '1'
        $env:PEPPERYN_GOVERNED_PIPELINE_TRANSPORT = '0'
        $env:PEPPERYN_GOVERNED_REHEARSAL_MANIFEST = $null
        $stage = 'FINAL_PERMIT_CHECK'
        if ((Test-Path -LiteralPath $closed) -or [DateTimeOffset]::Parse($permit.expires_at).UtcDateTime -le [DateTime]::UtcNow) { throw 'PERMIT_CLOSED_OR_EXPIRED' }
        $stage = 'FRONTEND_RUNNING'
        Write-Output 'B1_R2_FRONTEND: public configuration loaded. No automatic upload. External Provider and Real-data Admission CLOSED.'
        Push-Location (Join-Path $repo 'frontend')
        try { & $node 'node_modules/next/dist/bin/next' dev -H 127.0.0.1 -p 3000; $exitCode = $LASTEXITCODE }
        finally { Pop-Location }
    }
} catch {
    Write-Output "B1_FRONTEND_REFUSED_STAGE: $stage"
    Write-Output 'Stop. No retry or permit reset. No credential displayed.'
} finally {
    $anon = $null
    if ($closeOnExit) {
        if (-not (Test-Path -LiteralPath $closed)) {
            $handle = [IO.File]::Open($closed,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
            try { $bytes = [Text.Encoding]::UTF8.GetBytes('CLOSED_NO_AUTOMATIC_RESUME'); $handle.Write($bytes,0,$bytes.Length); $handle.Flush() }
            finally { $handle.Dispose() }
        }
        Write-Output 'B1_TEMPORARY_SURFACE: CLOSED. No live PASS inferred.'
    }
}
exit $exitCode
