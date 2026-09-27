param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$stage = 'SOURCE_INTEGRITY'
$exitCode = 1
$anon = $null
$pins = @{
    'frontend\lib\api.ts' = 'AC1DC57E988D2CDCB7884C4808703336FDF8C9D37B5EE8881835572F0B5F6C0F'
    'frontend\lib\governed-temporal-api.ts' = '603D67FDAC72B6AA9FDC244DB4640A1A843FC1FE696A4800F0EFCF95F5ED54F8'
    'frontend\components\chat\MessageBubble.tsx' = 'ED24B707F6EBFE61C682A2D38C2BB72D15461DBE58C669154FB0632192FE541B'
    'frontend\components\chat\GovernedTemporalComparison.tsx' = '74E1244BCC90008608A627AE32538D8D47011C2FDAF0FBFB51AEA5CF7D4C37D8'
    'frontend\components\chat\ChatContainer.tsx' = '34B4722045CC680D58F9D883A0FB01AA4F291D6269295AADC5AA559F909DB77C'
}
try {
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'SOURCE_CHANGED' }
    }
    $stage = 'FRONTEND_RUNTIME'
    $nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
    $node = if ($nodeCommand) { $nodeCommand.Source } else { 'C:\Users\ADMIN-FRED\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' }
    if (-not (Test-Path -LiteralPath $node) -or -not (Test-Path -LiteralPath (Join-Path $repo 'frontend\node_modules\next\dist\bin\next'))) { throw 'RUNTIME_ABSENT' }
    if ($CheckOnly) {
        Write-Output 'B1_CORRECTED_FRONTEND_CHECK: PASS. Source hashes only; no startup, network or secret access.'
        $exitCode = 0
    } else {
        $stage = 'PORTS_MUST_BE_FREE'
        $listeners = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
        if (@($listeners | Where-Object { $_.Port -in @(3000,8000) }).Count -ne 0) { throw 'PORT_OCCUPIED_NO_KILL' }
        $stage = 'PUBLIC_ANON_KEY'
        $anon = $env:NEXT_PUBLIC_SUPABASE_ANON_KEY
        if ([string]::IsNullOrWhiteSpace($anon)) {
            $masked = Read-Host 'Cle publique anon Supabase Integration Test uniquement (jamais service_role)' -AsSecureString
            $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($masked)
            try { $anon = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
            finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr); $masked.Dispose() }
        }
        $parts = $anon.Split('.')
        if ($parts.Count -ne 3) { throw 'ANON_FORMAT_REFUSED' }
        $payload = $parts[1].Replace('-','+').Replace('_','/')
        while (($payload.Length % 4) -ne 0) { $payload += '=' }
        $claims = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload)) | ConvertFrom-Json
        if ($claims.role -ne 'anon' -or $claims.ref -ne 'ejixkplrgobgwqnhidwt') { throw 'ANON_SCOPE_REFUSED' }
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
        $stage = 'FRONTEND_ONLY'
        Write-Output 'B1_CORRECTED_FRONTEND: source hashes verified. Delivered bundle verification still pending. Backend remains closed; no permit opened.'
        Push-Location (Join-Path $repo 'frontend')
        try { & $node 'node_modules/next/dist/bin/next' dev -H 127.0.0.1 -p 3000; $exitCode = $LASTEXITCODE }
        finally { Pop-Location }
    }
} catch {
    Write-Output "B1_CORRECTED_FRONTEND_REFUSED_STAGE: $stage"
    Write-Output 'No automatic retry. No secret displayed or regenerated. No permit modified.'
} finally { $anon = $null }
exit $exitCode
