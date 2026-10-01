# Successor default mode validates only local integrity. Execute mode remains
# one-shot and requires a distinct Founder GO plus fresh read-only attestation.
param([switch]$ExecuteAfterFounderGO)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_INTEGRITY'
$exitCode = 1
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\run_v41_owner_ack_successor.py'
$secretFile = Join-Path $runtime 'secrets\a24-isolation-accounts.dpapi'
$attempt = Join-Path $runtime 'v41-injected-5'
$pins = @{
    'backend/sandbox/run_v41_owner_ack_successor.py' = 'D3F7DD39E8553BEB4B24D7A54F652D4F0543D7F1B8C65A2EE66E769409669533'
    'backend/sandbox/run_v41_injected_rehearsal.py' = '7FDBA35CD6A97FAD99A3558E95DB0A62DE30D7F80C912460D0E744707A67F62C'
    'backend/sandbox/v41_injected_rehearsal.py' = '6696489BB6316EB3A140845222046DCD07A29FED894E1F0577BA22841F2373E5'
    'backend/sandbox/v41_owner_handoff.py' = '816EFA09EB0C71B0B9CE7627810FCFC34D1443C34975298442FD6CE26D1502CD'
    'backend/tests/test_v41_owner_ack_successor.py' = '71DF9DF26FD0072BF77BF271CBF83B58EDFF65DBD721FAF059EB2CD2AE3D8988'
    'backend/tests/test_v41_owner_handoff.py' = '8D3EC7B40EC6222915C601FE5E8AEF9BEC7D5B5F2106AD53013BD5EFF9A44587'
    'backend/tests/test_v41_injected_rehearsal_launcher.py' = '6B34A91E02F022D95B53419A6FCB3A2E8A8D6BA16A7F8C6618658C1956807C55'
    'backend/tests/test_v41_conservative_freshness.py' = '6D260EFD9798B15962A32468B2C2F1367A515E0AC7C21DD3A53BDF353953EB4D'
    'backend/tests/test_v41_owner_ack_postgres.py' = 'BA0C44F4A027DFB85E79D31689004A4B12E6713F1306964099426A129CE6EA88'
    'backend/tests/fixtures/v41_attempt4_accepted_precontrol.json' = '7205B6612A16746E768AFCC596D5D0B193DF547CAC08E2748A301F8ABE0C3853'
    'docs/Project_Control/PPR069_OWNER_ACK_SUCCESSOR_PROTOCOL.md' = 'CD8167C8BE8AB4D4C283B580350F34AB8923D59DD3A150C2E8F94BA70B3332F1'
    'backend/tests/golden/fixtures/pepperyn_v1_heterogeneous_english.xlsx' = 'FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93'
    'frontend/components/chat/__tests__/ExecutionProvenance.rehearsal.test.tsx' = 'D5720168189DF96302A92D7CAE255E5A5C6C7D2DC0B2508D1DAD773A400E059A'
    'docs/Project_Control/PPR069_OWNER_ACK_PRESERVED_HISTORY.json' = '7C92079DF6F805FBA69C4264907E95BE24F759E10B9D5F1CA57B04C648DB6B82'
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

    $frozen = @{
        'manifest.json' = '31AAAC4D01DD11209A3F15B412B89D6BC785943A96025A23E667E5825761E7B6'
        'policy-disable.sql' = '87CF8ECCC4F2FC17061EC9CBF31F0299ADD8762039E1875F4918E85EE0B55D0A'
        'policy-insert.sql' = '30FB057EDC265C0846543EB198A6F7BE45F9F67581893A8816BD75E21C2FB86D'
        'precontrol.sql' = '0A24E82D836D30C0763822FD23500A5A50CDAD7C781953EA4C0C439B687B95B7'
    }
    foreach ($name in $frozen.Keys) {
        if ((Get-FileHash -LiteralPath (Join-Path $attempt $name) -Algorithm SHA256).Hash -cne $frozen[$name]) { throw 'FROZEN_ARTIFACT_CHANGED' }
    }
    $history = Get-Content -LiteralPath (Join-Path $repo 'docs/Project_Control/PPR069_OWNER_ACK_PRESERVED_HISTORY.json') -Raw | ConvertFrom-Json
    foreach ($item in $history) {
        if ((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash -cne $item.hash) { throw 'HISTORY_CHANGED' }
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    $head = & git.exe -c "safe.directory=$repo" -C $repo rev-parse HEAD
    & git.exe -c "safe.directory=$repo" -C $repo merge-base --is-ancestor `
        'ff14a3237152388c6b32989f29f5fd80f39874e9' $head
    if ($LASTEXITCODE -ne 0) { throw 'CHECKPOINT_BASELINE_REFUSED' }
    if ($ExecuteAfterFounderGO) {
        $remote = & git.exe -c "safe.directory=$repo" -C $repo rev-parse '@{u}'
        if ($head -ne $remote) { throw 'CHECKPOINT_SYNCHRONISATION_REFUSED' }
        foreach ($entry in $pins.GetEnumerator()) {
            $blob = & git.exe -c "safe.directory=$repo" -C $repo rev-parse ("HEAD:" + $entry.Key)
            if ($LASTEXITCODE -ne 0) { throw 'CHECKPOINTED_FILE_ABSENT' }
            $worktreeBlob = & git.exe -c "safe.directory=$repo" -C $repo hash-object ("--path=" + $entry.Key) (Join-Path $repo $entry.Key)
            if ($blob -ne $worktreeBlob) { throw 'CHECKPOINTED_FILE_DIFFERS' }
        }
    }
    $env:PYTHONPATH = Join-Path $repo 'backend'
    $OutputEncoding = New-Object System.Text.UTF8Encoding($false)
    $stage = 'LOCAL_TESTS'
    Push-Location -LiteralPath $repo
    try {
        & $python -B -m pytest -q -p no:cacheprovider --basetemp (Join-Path $runtime "v41-injected-pytest-$PID") `
            (Join-Path $repo 'backend\tests\test_v41_injected_rehearsal_launcher.py') `
            (Join-Path $repo 'backend\tests\test_v41_conservative_freshness.py') `
            (Join-Path $repo 'backend\tests\test_v41_owner_handoff.py') `
            (Join-Path $repo 'backend\tests\test_v41_owner_ack_successor.py')
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
        & $python -B -W ignore -c "from sandbox.run_v41_owner_ack_successor import read_manifest, ATTEMPT, validate_attestation; validate_attestation(read_manifest(ATTEMPT))"
        if ($LASTEXITCODE -ne 0) { throw 'ATTESTATION_REFUSED_BEFORE_SECRET_READ' }
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
