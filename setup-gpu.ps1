# Prepare the pinned, MIT-licensed GPU dependency with the two local fixes.
# Run from any directory: powershell -ExecutionPolicy Bypass -File .\setup-gpu.ps1
$ErrorActionPreference = 'Stop'
$repoRoot = $PSScriptRoot
$dependency = Join-Path $repoRoot 'bip39-gpu-review'
$patch = Join-Path $repoRoot 'patches\bip39-gpu-fixes.patch'
$revision = '08f189d3ade6a18e18acc82f18a7bfb576c6e86f'

if (Test-Path -LiteralPath $dependency) {
    throw "Dependency directory already exists: $dependency. Inspect it before rerunning setup."
}

git clone https://github.com/AlexMelanFromRingo/BIP39-GPU.git $dependency
if ($LASTEXITCODE -ne 0) { throw 'Could not clone BIP39-GPU.' }
git -C $dependency checkout --detach $revision
if ($LASTEXITCODE -ne 0) { throw 'Could not check out the pinned BIP39-GPU revision.' }
git -C $dependency apply --check $patch
if ($LASTEXITCODE -ne 0) { throw 'Local GPU patch does not apply cleanly.' }
git -C $dependency apply $patch
if ($LASTEXITCODE -ne 0) { throw 'Could not apply the local GPU patch.' }
python -m pip install -r (Join-Path $repoRoot 'requirements-gpu.txt')
if ($LASTEXITCODE -ne 0) { throw 'Could not install Python dependencies.' }
Write-Host 'GPU dependency and Python packages are ready.'

