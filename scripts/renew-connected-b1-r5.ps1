param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-development'
$runtime = 'C:\Users\ADMIN-FRED\Documents\Codex\Pepperyn-runtime'
$python = Join-Path $runtime 'fresh-founder-20260907-075758\backend-venv\Scripts\python.exe'
$source = Join-Path $repo 'backend\sandbox\renew_connected_b1_r5.py'
$previousPermit = Join-Path $runtime 'b1-connected-rehearsal-r4.json'
$successor = Join-Path $runtime 'b1-connected-rehearsal-r5.json'
$oldPythonPath = [Environment]::GetEnvironmentVariable('PYTHONPATH','Process')
$stage = 'LOCAL_INTEGRITY'
$code = 1
try {
    $pins = @{
        'backend\sandbox\inspect_closed_b1_r3.py' = '5E61FC1D188AD14FD2E9C46F2F306ABC373C75375FCD3C227DC52662369EC673'
        'backend\sandbox\renew_connected_b1_r5.py' = '74DF8B8745F48129E5B4E2512192D8AE0DD6488DEC12A4D68935B0F0B2A2DDD1'
        'backend\sandbox\preflight_connected_b1.py' = '8917A5D234801CFC25156A937F98029B084911E98D851E5805C35597946C1468'
        'backend\services\governed_rehearsal_permit.py' = '6C419B01595E44911F4BCEAF26E652AB940BB11B18059E7412ED62E80C042A78'
    }
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath (Join-Path $repo $entry.Key) -Algorithm SHA256).Hash -ne $entry.Value) { throw 'INTEGRITY_REFUSED' }
    }
    $stage = 'HOST_PORTS_3000_8000_MUST_BE_FREE'
    $listeners = [Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
    if (@($listeners | Where-Object { $_.Port -in @(3000,8000) }).Count -ne 0) { throw 'PORT_OCCUPIED_NO_PERMIT_CREATION' }
    $env:PYTHONPATH = Join-Path $repo 'backend'
    if ($CheckOnly) {
        & $python -B -W ignore $source --previous $previousPermit --successor $successor --local-check
        if ($LASTEXITCODE -ne 0) { throw 'LOCAL_CHECK_REFUSED' }
        $code = 0
    } else {
        $stage = 'EXISTING_ENVIRONMENT_AVAILABILITY'
        foreach ($name in @('SUPABASE_ANON_KEY','SUPABASE_SERVICE_KEY','JWT_GUEST_SECRET')) {
            if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name,'Process'))) { throw 'PREPARED_ENVIRONMENT_MISSING' }
        }
        $stage = 'READ_ONLY_RENEWAL'
        $output = & $python -B -W ignore $source --previous $previousPermit --successor $successor 2>$null
        $pythonCode = $LASTEXITCODE
        $result = ($output -join "`n") | ConvertFrom-Json
        if ($pythonCode -ne 0 -or $result.status -ne 'B1_R5_PERMIT_CREATED') {
            if ($result.stage -match '^[A-Z0-9_]+$') { $stage = $result.stage }
            if ($result.diagnostic -match '^[A-Za-z0-9_]+$') { Write-Output ('SAFE_DIAGNOSTIC: ' + $result.diagnostic) }
            throw 'RENEWAL_REFUSED'
        }
        if ($result.analysis_id -ne 'e2dc7bd5-c71a-4c88-821c-b1f2696fb04b' -or
            $result.prospective_uuid_absent -ne $true -or $result.preexisting_hashes_unchanged -ne $true -or
            $result.previous_permit_unchanged -ne $true -or $result.new_permit_created -ne $true -or
            $result.business_write_performed -ne $false -or $result.transport_activated -ne $false -or
            $result.external_provider_used -ne $false -or $result.real_data_used -ne $false -or
            $result.successor_sha256 -notmatch '^[A-F0-9]{64}$') { throw 'RESULT_SCOPE_REFUSED' }
        [pscustomobject]@{
            status = 'B1_R5_PERMIT_CREATED'
            analysis_id = 'e2dc7bd5-c71a-4c88-821c-b1f2696fb04b'
            prospective_uuid_absent = $true
            preexisting_hashes_unchanged = $true
            previous_permit_unchanged = $true
            new_permit_created = $true
            successor_sha256 = $result.successor_sha256
            business_write_performed = $false
            transport_activated = $false
            external_provider_used = $false
            real_data_used = $false
        } | ConvertTo-Json -Compress | Write-Output
        Write-Output 'JWT_AND_V33_UNTOUCHED; EXTERNAL_PROVIDER: CLOSED; REAL_DATA_ADMISSION: CLOSED'
        $code = 0
    }
} catch {
    if ((Test-Path -LiteralPath $successor) -or (Test-Path -LiteralPath ([IO.Path]::ChangeExtension($successor,'.pending')))) {
        $refusedMarker = [IO.Path]::ChangeExtension($successor,'.closed')
        if (-not (Test-Path -LiteralPath $refusedMarker)) {
            $handle = [IO.File]::Open($refusedMarker,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
            try { $bytes = [Text.Encoding]::UTF8.GetBytes('RENEWAL_WRAPPER_REFUSED_NO_RETRY'); $handle.Write($bytes,0,$bytes.Length); $handle.Flush() }
            finally { $handle.Dispose() }
        }
    }
    Write-Output "B1_RENEWAL_REFUSED_STAGE: $stage"
    Write-Output 'Do not rerun, reset, activate or clean up. Preserve both permit records and report.'
} finally {
    [Environment]::SetEnvironmentVariable('PYTHONPATH',$oldPythonPath,'Process')
    $output = $null; $result = $null
}
exit $code
