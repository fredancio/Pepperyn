# Successor default mode validates only local integrity. Execute mode remains
# one-shot and requires a distinct Founder GO plus fresh read-only attestation.
param([switch]$ExecuteAfterFounderGO)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_INTEGRITY'
$exitCode = 1
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\run_v41_injected_rehearsal.py'
$secretFile = Join-Path $runtime 'secrets\a24-isolation-accounts.dpapi'
$attempt = Join-Path $runtime 'v41-injected-4'
$pins = @{
    'backend/sandbox/run_v41_injected_rehearsal.py' = '510A63CE8D970167C7FBC725AE83C3600C79A38BEF14BB3A6EEA1E6A2FBB2661'
    'backend/sandbox/v41_injected_rehearsal.py' = '7BFDB68478C3ABD7770E735D92E96C7604358DB8E7F21B442D27685272A98F8F'
    'backend/tests/test_v41_injected_rehearsal_launcher.py' = '6B34A91E02F022D95B53419A6FCB3A2E8A8D6BA16A7F8C6618658C1956807C55'
    'backend/tests/test_v41_successor_precontrol_postgres.py' = '38504210E46E86EFED1269EC817B824429BE0C05B56122CECEF7DD68F4DC48C0'
    'backend/tests/test_v41_injected_successor_postgres.py' = '55CA80EAC4DA8CBC8F48116D5CCC9756DAA9D68E601E00B8DC0F919E46EE37E6'
    'frontend/components/chat/__tests__/ExecutionProvenance.rehearsal.test.tsx' = 'D5720168189DF96302A92D7CAE255E5A5C6C7D2DC0B2508D1DAD773A400E059A'
    'docs/Project_Control/INSIGHT_SHAPER_B1_V41_INJECTED_DURABLE_REHEARSAL_SUCCESSOR_PROTOCOL.md' = 'FB7AA56B9209392B6E64E4C125DACF4551CA27F129A91E175269152FE7B8861F'
    'backend/tests/golden/fixtures/pepperyn_v1_heterogeneous_english.xlsx' = 'FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93'
}
$oldPythonPath = [Environment]::GetEnvironmentVariable('PYTHONPATH','Process')
$oldEncoding = $OutputEncoding
$beforeHash = $null
try {
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) {
            throw 'INTEGRITY_REFUSED'
        }
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    $head = & git.exe -c "safe.directory=$repo" -C $repo rev-parse HEAD
    & git.exe -c "safe.directory=$repo" -C $repo merge-base --is-ancestor `
        'ccab95c2b6bfeaaae59ecbcbfea1da38f8231ca5' $head
    if ($LASTEXITCODE -ne 0) { throw 'CHECKPOINT_BASELINE_REFUSED' }
    if ($ExecuteAfterFounderGO) {
        $remote = & git.exe -c "safe.directory=$repo" -C $repo rev-parse '@{u}'
        if ($head -ne $remote) { throw 'CHECKPOINT_SYNCHRONISATION_REFUSED' }
        foreach ($entry in $pins.GetEnumerator()) {
            $blob = & git.exe -c "safe.directory=$repo" -C $repo rev-parse ("HEAD:" + $entry.Key)
            if ($LASTEXITCODE -ne 0) { throw 'CHECKPOINTED_FILE_ABSENT' }
            $worktreeBlob = & git.exe -c "safe.directory=$repo" -C $repo hash-object (Join-Path $repo $entry.Key)
            if ($blob -ne $worktreeBlob) { throw 'CHECKPOINTED_FILE_DIFFERS' }
        }
    }
    $env:PYTHONPATH = Join-Path $repo 'backend'
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $stage = 'LOCAL_TESTS'
    Push-Location -LiteralPath $repo
    try {
        & $python -B -m pytest -q --basetemp (Join-Path $runtime "v41-injected-pytest-$PID") `
            (Join-Path $repo 'backend\tests\test_v41_injected_rehearsal_launcher.py')
    } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { throw 'LOCAL_TESTS_REFUSED' }
    if (-not $ExecuteAfterFounderGO) {
        Write-Output 'V41_INJECTED_SUCCESSOR_WRAPPER_LOCAL_CHECK: PASS. No credential read; no network; no Auth; no remote write.'
        $exitCode = 0
    } else {
        $stage = 'PRECONTROL_ATTESTATION'
        if (-not (Test-Path -LiteralPath (Join-Path $attempt 'precontrol-ready.json') -PathType Leaf)) {
            throw 'PRECONTROL_ATTESTATION_ABSENT'
        }
        $stage = 'EXISTING_DPAPI_RESTORE'
        $beforeHash = (Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash
        Add-Type -AssemblyName System.Security
        $entropy = [Text.Encoding]::UTF8.GetBytes('Pepperyn|IntegrationTest|A24IsolationAccounts|v1')
        $plain = [Security.Cryptography.ProtectedData]::Unprotect(
            [IO.File]::ReadAllBytes($secretFile), $entropy,
            [Security.Cryptography.DataProtectionScope]::CurrentUser)
        try { $bundle = [Text.Encoding]::UTF8.GetString($plain) | ConvertFrom-Json }
        finally { [Array]::Clear($plain,0,$plain.Length) }
        if ($bundle.project_url -ne 'https://ejixkplrgobgwqnhidwt.supabase.co' -or
            $bundle.purpose -ne 'A24_TECHNICAL_ISOLATION_ONLY' -or
            $bundle.accounts.Count -ne 2 -or
            $bundle.accounts[0].email -ne 'pepperyn-isolation-a24-a@pepperyn-test.invalid') {
            throw 'BUNDLE_REFUSED'
        }
        $keys = @{}
        foreach ($name in @('SUPABASE_ANON_KEY','SUPABASE_SERVICE_KEY')) {
            $stage = $name + '_AVAILABILITY'
            $value = [Environment]::GetEnvironmentVariable($name,'Process')
            if ([string]::IsNullOrWhiteSpace($value)) {
                $secure = Read-Host "$name Pepperyn Integration Test uniquement (saisie masquee)" -AsSecureString
                $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
                try { $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
                finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $secure.Dispose() }
            }
            if ([string]::IsNullOrWhiteSpace($value)) { throw 'KEY_ABSENT' }
            $keys[$name] = $value
            $value = $null
        }
        $packet = @{
            anon=$keys.SUPABASE_ANON_KEY
            service=$keys.SUPABASE_SERVICE_KEY
            bundle=$bundle
            authorization='V41_INJECTED_DURABLE_SUCCESSOR_GO_10_EFFECTS_5_ROWS'
        } | ConvertTo-Json -Depth 12 -Compress
        $keys = $null; $bundle = $null
        $stage = 'ONE_SHOT_ORCHESTRATION'
        $packet | & $python -B -W ignore $source --execute 2>$null
        $code = $LASTEXITCODE
        $packet = $null
        if ($code -ne 0) { throw 'ORCHESTRATION_REFUSED_NO_RETRY' }
        $stage = 'FINAL_ARTIFACT'
        $result = Get-Content -LiteralPath (Join-Path $attempt 'result.json') -Raw | ConvertFrom-Json
        if ($result.status -ne 'BOUNDED_V41_INJECTED_DURABLE_SUCCESSOR_REHEARSAL_PASS' -or
            $result.new_durable_rows -ne 5 -or $result.effect_attempts -ne 10 -or
            $result.auth_logins -ne 1 -or $result.policy_enabled -ne $false -or
            $result.provider_execution_attested -ne $false -or
            $result.producer_global_status -ne 'UNADMITTED' -or
            $result.external_provider_used -ne $false -or $result.real_data_used -ne $false -or
            $result.b1_closed -ne $false) { throw 'RESULT_REFUSED' }
        $stage = 'DPAPI_UNCHANGED'
        if ((Get-FileHash -LiteralPath $secretFile -Algorithm SHA256).Hash -ne $beforeHash) {
            throw 'DPAPI_CHANGED'
        }
        Write-Output 'EXISTING_DPAPI_UNCHANGED: PASS; JWT_AND_V33_UNTOUCHED; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $exitCode = 0
    }
} catch {
    Write-Output "V41_INJECTED_SUCCESSOR_WRAPPER_REFUSED_STAGE: $stage"
    Write-Output 'Stop. No retry, cleanup, reset or second authentication. Preserve all artifacts; remote state may be partial.'
} finally {
    [Environment]::SetEnvironmentVariable('PYTHONPATH',$oldPythonPath,'Process')
    $OutputEncoding = $oldEncoding
    $packet = $null; $bundle = $null; $keys = $null; $value = $null; $plain = $null
}
exit $exitCode
