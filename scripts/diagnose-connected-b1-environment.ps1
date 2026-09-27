# Read-only diagnostic. Run from the original backend terminal, not a fresh one.
# No secret value, length, fingerprint, exception text, network or file output.
$expected = [ordered]@{
    SUPABASE_URL = 'https://ejixkplrgobgwqnhidwt.supabase.co'
    ENVIRONMENT = 'development'
    PEPPERYN_ENABLE_SYNTHETIC_V1_DEMO = '1'
    PEPPERYN_SYNTHETIC_V1_COMPANY_ID = '89644cea-1e5c-478a-b797-b34d646064be'
}
$checks = [ordered]@{}
foreach ($name in $expected.Keys) {
    $value = [Environment]::GetEnvironmentVariable($name,'Process')
    if ([string]::IsNullOrWhiteSpace($value)) { $checks[$name] = 'MISSING' }
    elseif ($value -eq $expected[$name]) { $checks[$name] = 'MATCH' }
    else { $checks[$name] = 'MISMATCH' }
    $value = $null
}
foreach ($name in @('SUPABASE_ANON_KEY','SUPABASE_SERVICE_KEY','JWT_GUEST_SECRET')) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name,'Process'))) {
        $checks[$name] = 'MISSING'
    } else { $checks[$name] = 'PRESENT_NOT_VALIDATED' }
}
[pscustomobject]@{
    status = 'B1_ENVIRONMENT_INSPECTED_ONLY'
    checks = $checks
    network_used = $false
    environment_modified = $false
    permit_modified = $false
    secret_value_disclosed = $false
    transport_activated = $false
} | ConvertTo-Json -Depth 3
