param(
    [string]$Python = 'python',
    [ValidateRange(0, 32)][int]$Platform = 1,
    [switch]$AllowHintTypo,
    [switch]$EncodingHintTypo
)
# Follow the user's requested assumption: investigate beyond the pair family.
# This script neither launches that family nor marks its checkpoint complete.
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$followup = Join-Path $root 'followup-2026-09-26'
if (-not (Test-Path -LiteralPath (Join-Path $root 'bip39-gpu-review\src'))) {
    throw 'Run setup-gpu.ps1 first to prepare the pinned and repaired dependency.'
}
node (Join-Path $root 'verify-search-inputs.cjs')
if ($LASTEXITCODE -ne 0) { throw 'Exact-byte input verification failed.' }
& $Python (Join-Path $root 'gpu-probe.py') 4096 --platform $Platform
if ($LASTEXITCODE -ne 0) { throw 'GPU certification failed; no search was launched.' }
if (-not (Test-Path -LiteralPath (Join-Path $followup 'verification\languages\trezor-vectors.json'))) {
    node (Join-Path $followup 'prepare-historical-languages.cjs')
    if ($LASTEXITCODE -ne 0) { throw 'Could not fetch and validate historical wordlists.' }
}
$jobs = @(
    @{ Script = 'chapter-whitespace-gpu.py'; Args = @('--all') },
    @{ Script = 'chapter-nbsp-gpu.py'; Args = @('--all') },
    @{ Script = 'example-unfiltered-gpu.py'; Args = @('--draft', 'published', '--join', 'lf', '--index', '0', '--all') },
    @{ Script = 'example-unfiltered-gpu.py'; Args = @('--draft', 'published', '--join', 'crlf', '--index', '0', '--all') },
    @{ Script = 'example-unfiltered-gpu.py'; Args = @('--draft', 'published', '--join', 'lf', '--indices', '1,2,3,4,5,6', '--all') },
    @{ Script = 'example-unfiltered-gpu.py'; Args = @('--draft', 'published', '--join', 'crlf', '--indices', '1,2,3,4,5,6', '--all') },
    @{ Script = 'example-converter-gpu.py'; Args = @('--prefix-errors', '0') },
    @{ Script = 'example-converter-gpu.py'; Args = @('--prefix-errors', '1') },
    @{ Script = 'language-settings-gpu.py'; Args = @('--family', 'example') },
    @{ Script = 'language-settings-gpu.py'; Args = @('--family', 'canonical-example', '--languages', 'all') },
    @{ Script = 'language-settings-gpu.py'; Args = @('--family', 'example', '--prefix-errors', '1', '--languages', 'english') },
    @{ Script = 'language-settings-gpu.py'; Args = @('--family', 'chapter') },
    @{ Script = 'example-encoding-gpu.py'; Args = @('--prefix-errors', '0') }
)
if ($AllowHintTypo) {
    $jobs += @{ Script = 'language-settings-gpu.py'; Args = @('--family', 'example', '--prefix-errors', '1') }
}
if ($EncodingHintTypo) {
    $jobs += @{ Script = 'example-encoding-gpu.py'; Args = @('--prefix-errors', '1') }
}
foreach ($job in $jobs) {
    if (Get-ChildItem -LiteralPath $followup -Filter 'FOUND-*' -File) {
        Write-Host 'A verified local witness exists in followup-2026-09-26. Inspect it before more computation.'
        return
    }
    $jobArgs = @((Join-Path $followup $job.Script), '--platform', "$Platform") + $job.Args
    Write-Host "Running $($job.Script) $($job.Args -join ' ')"
    & $Python @jobArgs
    if ($LASTEXITCODE -ne 0) { throw "Search failed: $($job.Script). Preserve its output and checkpoint." }
}
Write-Host 'These finite follow-up families completed. Their negative results do not prove the puzzle has no solution.'
node (Join-Path $followup 'refresh-post-pair-ledger.cjs')
if ($LASTEXITCODE -ne 0) { throw 'Could not validate the result ledger.' }
