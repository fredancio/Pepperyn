[CmdletBinding()]
param([ValidateSet('insert','disable')][string]$Action, [switch]$ConfirmSqlExecutedOnce, [switch]$LocalCheckOnly, [string]$ResultPath, [string]$InsertLoadedPath, [string]$DisableLoadedPath)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$attempt = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\v41-injected-6'
$python = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$pins = @{
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
foreach ($entry in $pins.GetEnumerator()) {
    if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -cne $entry.Value) { throw 'INTEGRITY_REFUSED' }
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

$gitExe = @(Get-Command git.exe -CommandType Application -All)[0].Source
if (-not $LocalCheckOnly) {
    foreach ($entry in $pins.GetEnumerator()) {
        $headBlob = & $gitExe -c "safe.directory=$repo" -C $repo rev-parse ("HEAD:" + $entry.Key)
        if ($LASTEXITCODE -ne 0) { throw 'NOT_CHECKPOINTED' }
        $workBlob = & $gitExe -c "safe.directory=$repo" -C $repo hash-object ("--path=" + $entry.Key) (Join-Path $repo $entry.Key)
        if ($LASTEXITCODE -ne 0 -or $headBlob -cne $workBlob) { throw 'NOT_CHECKPOINTED' }
    }
}
Push-Location -LiteralPath (Join-Path $repo 'backend')
try {
    if ($LocalCheckOnly) {
        if ($Action -or $ResultPath -or $ConfirmSqlExecutedOnce -or $InsertLoadedPath -or $DisableLoadedPath) { throw 'MIXED_MODE' }
        & $python -B -W ignore -m sandbox.run_v41_attempt6 --local-check
    } elseif ($InsertLoadedPath -or $DisableLoadedPath) {
        if (-not $InsertLoadedPath -or -not $DisableLoadedPath -or $Action -or $ResultPath -or $ConfirmSqlExecutedOnce) { throw 'MIXED_MODE' }
        & $python -B -W ignore -m sandbox.run_v41_attempt6 --verify-transfers $InsertLoadedPath $DisableLoadedPath
    } elseif ($ResultPath) {
        if ($Action -or $ConfirmSqlExecutedOnce) { throw 'MIXED_MODE' }
        & $python -B -W ignore -m sandbox.run_v41_attempt6 --attest $ResultPath
    } else {
        if (-not $Action -or -not $ConfirmSqlExecutedOnce) { throw 'EXPLICIT_LOCAL_ACTION_REQUIRED' }
        & $python -B -W ignore -m sandbox.run_v41_attempt6 --publish $Action --confirm-sql-executed-once
    }
    if ($LASTEXITCODE -ne 0) { throw 'LOCAL_OPERATION_REFUSED_NO_RETRY' }
} finally { Pop-Location }
