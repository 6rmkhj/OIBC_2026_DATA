$ErrorActionPreference = 'Stop'
$root = 'C:\Users\slowg\Downloads\OIBC_2026_DATA\analysis_outputs\renew_20261106\poisson_wave'
$start = Get-Content -LiteralPath "$root\evidence\run_attempt01_start.json" -Raw | ConvertFrom-Json
$identities = @(@{pid=$start.pid;creation_filetime=$start.creation_filetime})
foreach ($fold in @('primary','recent')) {
    foreach ($seed in @(0,1,2)) {
        $receipt = Get-Content -LiteralPath "$root\trials\$fold\seed$seed\controller_receipt.json" -Raw | ConvertFrom-Json
        $identities += $receipt.identity
    }
}
$records = @()
foreach ($identity in $identities) {
    $observed = Get-Process -Id $identity.pid -ErrorAction SilentlyContinue
    $exactAbsent = $true
    $observedTime = $null
    if ($observed) {
        $observedTime = $observed.StartTime.ToUniversalTime().ToFileTimeUtc()
        $exactAbsent = $observedTime -ne $identity.creation_filetime
    }
    if (-not $exactAbsent) { throw ('Exact identity still running: '+$identity.pid) }
    $records += @{pid=$identity.pid;creation_filetime=$identity.creation_filetime;exact_absent=$exactAbsent;observed_creation_filetime=$observedTime}
}
if ($records.Count -ne 7) { throw 'Expected seven identities' }
@{passed=$true;utc=[DateTime]::UtcNow.ToString('o');records=$records} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$root\evidence\native_terminal_identities.json" -Encoding UTF8
Write-Output 'NATIVE SEVEN IDENTITIES ABSENT PASS'
