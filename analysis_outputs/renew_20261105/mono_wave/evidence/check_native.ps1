$ErrorActionPreference = 'Stop'
$root = 'C:\Users\slowg\Downloads\OIBC_2026_DATA\analysis_outputs\renew_20261105\mono_wave'
$start = Get-Content -LiteralPath "$root\evidence\run_attempt01_start.json" -Raw | ConvertFrom-Json
$identities = @(@{pid=$start.pid;creation_filetime=$start.creation_filetime})
foreach ($arm in @('fair_control','fair_monotone')) {
    foreach ($fold in @('primary','recent')) {
        foreach ($seed in @(0,1,2)) {
            $receipt = Get-Content -LiteralPath "$root\trials\$arm\$fold\seed$seed\controller_receipt.json" -Raw | ConvertFrom-Json
            $identities += $receipt.identity
        }
    }
}
$records = @()
foreach ($identity in $identities) {
    $observed = Get-CimInstance Win32_Process -Filter ('ProcessId='+$identity.pid)
    $exactAbsent = $true
    $observedTime = $null
    if ($observed) {
        $observedTime = $observed.CreationDate.ToUniversalTime().ToFileTimeUtc()
        $exactAbsent = $observedTime -ne $identity.creation_filetime
    }
    if (-not $exactAbsent) { throw ('Exact identity still running: '+$identity.pid) }
    $records += @{pid=$identity.pid;creation_filetime=$identity.creation_filetime;exact_absent=$exactAbsent;observed_creation_filetime=$observedTime}
}
if ($records.Count -ne 13) { throw 'Expected thirteen identities' }
@{passed=$true;utc=[DateTime]::UtcNow.ToString('o');records=$records} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$root\evidence\native_terminal_identities.json" -Encoding UTF8
Write-Output 'NATIVE THIRTEEN IDENTITIES ABSENT PASS'
