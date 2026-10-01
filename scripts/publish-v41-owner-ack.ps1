[CmdletBinding()]
param([ValidateSet('insert','disable')][string]$Action, [switch]$ConfirmSqlExecutedOnce, [switch]$LocalCheckOnly, [string]$ResultPath)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$attempt = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\v41-injected-5'
$python = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime\fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
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
foreach ($entry in $pins.GetEnumerator()) {
    if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -cne $entry.Value) { throw 'INTEGRITY_REFUSED' }
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
        if ($Action -or $ResultPath -or $ConfirmSqlExecutedOnce) { throw 'MIXED_MODE' }
        & $python -B -W ignore -m sandbox.run_v41_owner_ack_successor --local-check
    } elseif ($ResultPath) {
        if ($Action -or $ConfirmSqlExecutedOnce) { throw 'MIXED_MODE' }
        & $python -B -W ignore -m sandbox.run_v41_owner_ack_successor --attest $ResultPath
    } else {
        if (-not $Action -or -not $ConfirmSqlExecutedOnce) { throw 'EXPLICIT_LOCAL_ACTION_REQUIRED' }
        & $python -B -W ignore -m sandbox.run_v41_owner_ack_successor --publish $Action --confirm-sql-executed-once
    }
    if ($LASTEXITCODE -ne 0) { throw 'LOCAL_OPERATION_REFUSED_NO_RETRY' }
} finally { Pop-Location }
