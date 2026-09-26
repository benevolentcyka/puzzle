param(
    [ValidateRange(0, 2147483647)][int]$Index = 0,
    [ValidateRange(0, 32)][int]$Platform = 1,
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
node (Join-Path $PSScriptRoot 'verify-search-inputs.cjs')
if ($LASTEXITCODE -ne 0) { throw 'Exact-byte input verification failed.' }
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'bip39-gpu-review\src'))) {
    throw 'Run setup-gpu.ps1 first to prepare the pinned GPU dependency.'
}
$baseNames = @(
    'four-groups-lflf', 'four-groups-crlfcrlf',
    'three-groups-lflf', 'three-groups-crlfcrlf',
    'raw-lflf', 'raw-crlfcrlf'
)
foreach ($baseName in $baseNames) {
    $witness = Join-Path $PSScriptRoot "FOUND-$baseName-index$Index.json"
    if (Test-Path -LiteralPath $witness) {
        Write-Host "A local matching witness already exists: $witness"
        return
    }
    $base = Join-Path $PSScriptRoot "bases\$baseName.txt"
    & $Python (Join-Path $PSScriptRoot 'gpu-case-pairs.py') --base $base --all --index $Index --platform $Platform
    if ($LASTEXITCODE -ne 0) { throw "Search failed for $baseName. Its saved checkpoint can be resumed." }
    if (Test-Path -LiteralPath $witness) {
        Write-Host "Verified match saved locally: $witness"
        return
    }
}
Write-Host "All six specified pair-toggle families completed at index $Index."
