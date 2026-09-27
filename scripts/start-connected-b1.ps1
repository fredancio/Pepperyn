param([Parameter(Mandatory=$true)][ValidateSet('Backend','Frontend')][string]$Mode,[switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_INTEGRITY'
$exitCode = 1
$closeOnExit = $false
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$manifest = Join-Path $runtime 'b1-connected-rehearsal.json'
$closed = [IO.Path]::ChangeExtension($manifest,'.closed')
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\run_connected_b1.py'
$names = @('PYTHONPATH','PEPPERYN_GOVERNED_PIPELINE_TRANSPORT','PEPPERYN_GOVERNED_REHEARSAL_MANIFEST','NEXT_PUBLIC_GOVERNED_PIPELINE_TRANSPORT')
$previous = @{}
foreach ($name in $names) { $previous[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
$pins = @{
    'backend\sandbox\run_connected_b1.py' = 'CA56F275D15D5A64FB58F173EE81CB47ACFAA78E2831ED98A21F9F182C1D9D8E'
    'backend\services\governed_pipeline_mount.py' = '1938B29437AD221977E4A96137B0346D8FBC162F53610C1C536A00525A60FC53'
    'backend\services\governed_rehearsal_permit.py' = '6C419B01595E44911F4BCEAF26E652AB940BB11B18059E7412ED62E80C042A78'
}
try {
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'INTEGRITY_REFUSED' }
    }
    if ((Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash -ne 'A68F439F3267C1E5B6E3C128B7BD079D0F8EC6832209818CB35095B4D502DF14') { throw 'MANIFEST_CHANGED' }
    if (-not $CheckOnly) { $closeOnExit = $true }
    $stage = 'PERMIT_VALIDITY'
    $permit = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
    if ([DateTimeOffset]::Parse($permit.expires_at).UtcDateTime -le [DateTime]::UtcNow) { throw 'PERMIT_EXPIRED' }
    if ((Test-Path -LiteralPath $closed) -or (Test-Path -LiteralPath ([IO.Path]::ChangeExtension($manifest,'.attempt')))) { throw 'CLOSED_OR_ALREADY_ATTEMPTED' }
    if ($CheckOnly) {
        $env:PYTHONPATH = Join-Path $repo 'backend'
        & $python -B -W ignore $source --manifest $manifest --local-check
        if ($LASTEXITCODE -ne 0) { throw 'LOCAL_CHECK_REFUSED' }
        Write-Output 'B1_LAUNCHER_CHECK: PASS. No remote operation, no activation, no secret modification.'
        $exitCode = 0
    } else {
        $stage = 'PORT_MUST_BE_FREE'
        $port = if ($Mode -eq 'Backend') { 8000 } else { 3000 }
        $listeners = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
        if (@($listeners | Where-Object { $_.Port -eq $port }).Count -ne 0) { throw 'PORT_IN_USE_NO_KILL' }
        if ($Mode -eq 'Backend') {
            $stage = 'EXISTING_BACKEND_ENVIRONMENT'
            if ($env:SUPABASE_URL -ne 'https://ejixkplrgobgwqnhidwt.supabase.co' -or
                $env:ENVIRONMENT -ne 'development' -or $env:PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO -ne '1' -or
                $env:PEPPERYN_SYNTHETIC_V1_COMPANY_ID -ne $permit.company_id) { throw 'ENVIRONMENT_REFUSED' }
            foreach ($name in @('SUPABASE_ANON_KEY','SUPABASE_SERVICE_KEY','JWT_GUEST_SECRET')) {
                if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name,'Process'))) { throw 'EXISTING_SECRET_ABSENT' }
            }
            $env:PYTHONPATH = Join-Path $repo 'backend'
            $env:PEPPERYN_GOVERNED_PIPELINE_TRANSPORT = '1'
            $env:PEPPERYN_GOVERNED_REHEARSAL_MANIFEST = $manifest
            $stage = 'BOUNDED_BACKEND'
            Push-Location (Join-Path $repo 'backend')
            try { & $python -B -W ignore $source --manifest $manifest; $exitCode = $LASTEXITCODE }
            finally { Pop-Location }
        } else {
            $stage = 'EXISTING_FRONTEND_ENVIRONMENT'
            if ($env:NEXT_PUBLIC_SUPABASE_URL -ne 'https://ejixkplrgobgwqnhidwt.supabase.co' -or
                [string]::IsNullOrWhiteSpace($env:NEXT_PUBLIC_SUPABASE_ANON_KEY) -or
                $env:NEXT_PUBLIC_API_URL -ne 'http://127.0.0.1:8000' -or
                $env:NEXT_PUBLIC_ENABLE_SYNTHETIC_V1_DEMO -ne '1') { throw 'FRONTEND_ENVIRONMENT_REFUSED' }
            if (-not (Test-Path -LiteralPath ([IO.Path]::ChangeExtension($manifest,'.activated')))) { throw 'BACKEND_NOT_ACTIVATED' }
            $stage = 'BACKEND_ROUTE_CHECK'
            $schema = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/openapi.json' -TimeoutSec 5
            if (-not $schema.paths.PSObject.Properties['/api/governed/analyses']) { throw 'ROUTE_ABSENT' }
            $node = (Get-Command node.exe -ErrorAction Stop).Source
            $env:NEXT_PUBLIC_GOVERNED_PIPELINE_TRANSPORT = '1'
            $stage = 'BOUNDED_FRONTEND'
            Write-Output 'B1_FRONTEND: existing public configuration reused. No automatic upload.'
            Push-Location (Join-Path $repo 'frontend')
            try { & $node 'node_modules/next/dist/bin/next' dev -H 127.0.0.1 -p 3000; $exitCode = $LASTEXITCODE }
            finally { Pop-Location }
        }
    }
} catch {
    Write-Output "B1_START_REFUSED_STAGE: $stage"
    Write-Output 'Stop. Do not retry or reset the permit. No secret displayed or regenerated.'
} finally {
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$previous[$name],'Process') }
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
