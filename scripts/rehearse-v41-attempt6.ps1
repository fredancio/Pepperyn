# Successor default mode validates only local integrity. Execute mode remains
# one-shot and requires a distinct Founder GO plus fresh read-only attestation.
param([switch]$ExecuteAfterFounderGO)
$ErrorActionPreference = 'Stop'
$stage = 'LOCAL_INTEGRITY'
$exitCode = 1
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\run_v41_attempt6.py'
$secretFile = Join-Path $runtime 'secrets\a24-isolation-accounts.dpapi'
$attempt = Join-Path $runtime 'v41-injected-6'
$pins = @{
    'scripts/publish-v41-attempt6-owner-ack.ps1' = 'FAED9AC9AAFDC7728A614908E98C91B2CC021AA8B6D0A5234A0D63014DFC10DF'
    'backend/sandbox/v41_injected_rehearsal.py' = 'A8864F0EB1ED374760004B2B2A4EECC894AA1F11DD3D380BC7BAB8F68DFD5136'
    'backend/tests/test_v41_owner_ack_successor.py' = '71DF9DF26FD0072BF77BF271CBF83B58EDFF65DBD721FAF059EB2CD2AE3D8988'
    'frontend/components/chat/__tests__/ExecutionProvenance.rehearsal.test.tsx' = 'D5720168189DF96302A92D7CAE255E5A5C6C7D2DC0B2508D1DAD773A400E059A'
    'backend/tests/test_v41_recording_db_composition.py' = '30B0F6C26D3EF9B267DA063124E02D11F3C387C28218513B104D2B6FF0C4A0B6'
    'backend/sandbox/run_v41_injected_rehearsal.py' = '46EB91F8F9A0A72EB22ADECB193E15FCAB03358592631B7BAA96CBD1BD59F6B6'
    'backend/tests/test_v41_owner_handoff.py' = '8D3EC7B40EC6222915C601FE5E8AEF9BEC7D5B5F2106AD53013BD5EFF9A44587'
    'backend/tests/fixtures/v41_attempt4_accepted_precontrol.json' = '7205B6612A16746E768AFCC596D5D0B193DF547CAC08E2748A301F8ABE0C3853'
    'backend/tests/test_v41_injected_rehearsal_launcher.py' = '6B34A91E02F022D95B53419A6FCB3A2E8A8D6BA16A7F8C6618658C1956807C55'
    'backend/tests/test_v41_two_policy_history.py' = 'EA8C3D4660CB15199822ED76CC00F962F88A45C22A31E69D60A089264C7723E8'
    'backend/sandbox/v41_owner_handoff.py' = '816EFA09EB0C71B0B9CE7627810FCFC34D1443C34975298442FD6CE26D1502CD'
    'docs/Project_Control/PPR069_ATTEMPT6_PRESERVED_HISTORY.json' = 'CDE06A127C5702E9507CEE588445973AC9324DDC2F4F4C32B6496367A3B3771B'
    'backend/tests/test_v41_attempt6_preparation.py' = '12502FD7DB2208FCBBA67DF9639AABF6B7193EA3211632936F5D328A761A432A'
    'backend/tests/test_v41_conservative_freshness.py' = '6D260EFD9798B15962A32468B2C2F1367A515E0AC7C21DD3A53BDF353953EB4D'
    'docs/Project_Control/PPR069_OWNER_ACK_SUCCESSOR_PROTOCOL.md' = 'CD8167C8BE8AB4D4C283B580350F34AB8923D59DD3A150C2E8F94BA70B3332F1'
    'backend/sandbox/run_v41_attempt6.py' = 'CB7858F03F4F67A818A8109EBC6F5BE8848AE28AE354D0F2C817B58A4A6D6173'
    'backend/sandbox/v41_two_policy_history.py' = '601DF67ED24C3D1FE6BFB93C1719842A0E2E7B141A8BA9E43FEB56E546646456'
    'docs/Project_Control/PPR069_ATTEMPT6_PROTOCOL.md' = 'D34FF884F54A48B7B7469CA4C1AE67A2E7BCB910FE8A2A42AC6AF5CD4DA8740C'
    'backend/tests/golden/fixtures/pepperyn_v1_heterogeneous_english.xlsx' = 'FE7FE4CC8FC6CE649F1FF61D18FDD3D45E2097031FD05AA8C9E2B7A47FAD3B93'
    'backend/tests/test_v41_attempt5_terminal_ack.py' = '97C0D37F144BC882F08CFF46F65A94BF2DD31996EF47CF972EC1DF2EF9A23AFE'
    'backend/sandbox/run_v41_owner_ack_successor.py' = 'D3F7DD39E8553BEB4B24D7A54F652D4F0543D7F1B8C65A2EE66E769409669533'
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
        'precontrol.sql' = 'E20294CFE292C505033B792E131054D1EE87284D5603E8A4EB6087C067BD45F3'
        'manifest.json' = '167BF3E9A41C0571863CC6B559E081D14AFAD7D375279397A996066CFA8EB325'
        'policy-disable.sql' = '6081A67CB058F700C652874914016242049E3D21303BD15DE41F41DB28BF0AA4'
        'policy-insert.sql' = 'F0079A203D3292666D0A8CAC13AF436790DF05DC19F0DA53E23DA3A1E6E4C9B0'
    }
    foreach ($name in $frozen.Keys) {
        if ((Get-FileHash -LiteralPath (Join-Path $attempt $name) -Algorithm SHA256).Hash -cne $frozen[$name]) { throw 'FROZEN_ARTIFACT_CHANGED' }
    }
    $history = Get-Content -LiteralPath (Join-Path $repo 'docs/Project_Control/PPR069_ATTEMPT6_PRESERVED_HISTORY.json') -Raw | ConvertFrom-Json
    foreach ($item in $history) {
        if ((Get-FileHash -LiteralPath $item.path -Algorithm SHA256).Hash -cne $item.hash) { throw 'HISTORY_CHANGED' }
    }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'PYTHON_ABSENT' }
    $head = & git.exe -c "safe.directory=$repo" -C $repo rev-parse HEAD
    & git.exe -c "safe.directory=$repo" -C $repo merge-base --is-ancestor `
        '0250a52c0002ef46d3df673fbf810548a17517ff' $head
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
            (Join-Path $repo 'backend\tests\test_v41_owner_ack_successor.py') `
            (Join-Path $repo 'backend\tests\test_v41_attempt6_preparation.py') `
            (Join-Path $repo 'backend\tests\test_v41_recording_db_composition.py') `
            (Join-Path $repo 'backend\tests\test_v41_attempt5_terminal_ack.py') `
            (Join-Path $repo 'backend\tests\test_v41_two_policy_history.py')
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
        & $python -B -W ignore -c "from sandbox.run_v41_attempt6 import read_manifest, ATTEMPT, validate_attestation, require_transfers; m=read_manifest(ATTEMPT); require_transfers(m); validate_attestation(m)"
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
