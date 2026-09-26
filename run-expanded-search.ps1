param(
    [string]$Python = 'python',
    [ValidateRange(0,32)][int]$Radius = 8,
    [ValidateSet('Focused','Broad')][string]$Shapes = 'Focused',
    [string]$Indices = '0',
    [int]$Platform = 1,
    [ValidateRange(0,4)][int]$WholeChapterEdits = 0,
    [switch]$SkipWallets
)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot

function Invoke-Search([string[]]$SearchArguments) {
    & $Python @SearchArguments
    if ($LASTEXITCODE -ne 0) { throw "Search failed with exit code $LASTEXITCODE" }
    $found = Get-ChildItem -LiteralPath (Join-Path $taskRoot 'expanded-2026-09-26') -Filter 'FOUND-*' -File
    if ($found) { throw 'A verified witness is present in expanded-2026-09-26. Inspect it before continuing.' }
}

Push-Location -LiteralPath $taskRoot
try {
    Write-Host "Marked-letter radius: $Radius; whole-chapter boundary edits: $WholeChapterEdits; shapes: $Shapes; indices: $Indices"
    if (-not $SkipWallets) {
        Invoke-Search @('expanded-2026-09-26/historical-wallets.py','--family','both','--platform',"$Platform")
    }
    $starts = @(0)
    $spaces = @('keep')
    if ($Shapes -eq 'Broad') {
        $starts = @(0,1,3)
        $spaces = @('keep','nbsp-space','trim')
    }
    $joins = @(
        @{ Join = 'crlf'; Internal = 'preserve' },
        @{ Join = 'lf'; Internal = 'preserve' },
        @{ Join = 'crlf'; Internal = 'match' }
    )
    foreach ($start in $starts) {
        foreach ($space in $spaces) {
            foreach ($join in $joins) {
                if ($WholeChapterEdits -gt 0) {
                    Invoke-Search @('expanded-2026-09-26/chapter-subsets.py',
                        '--positions','all-boundaries','--minimum-edits',"$WholeChapterEdits",
                        '--join',$join.Join,'--internal-newlines',$join.Internal,
                        '--start-paragraph',"$start",'--spaces',$space,
                        '--radius',"$WholeChapterEdits",'--indices',$Indices,'--platform',"$Platform")
                }
                Invoke-Search @('expanded-2026-09-26/chapter-subsets.py',
                    '--join',$join.Join,'--internal-newlines',$join.Internal,
                    '--start-paragraph',"$start",'--spaces',$space,
                    '--radius',"$Radius",'--indices',$Indices,'--platform',"$Platform")
            }
        }
    }
} finally {
    Pop-Location
}
