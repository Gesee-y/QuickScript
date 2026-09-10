param(
    [Parameter(Mandatory=$true)]
    [string]$initDir
)

git init $initDir

New-Item -ItemType Directory -Path (
    (Join-Path $initDir "includes"),
    (Join-Path $initDir "src"),
    (Join-Path $initDir "tests"),
    (Join-Path $initDir "bin")
) -Force | Out-Null

Copy-Item -Path "C:\Users\HPµ\Documents\GitHub\QuickScript\scripts\ctest_runner.ps1" -Destination $initDir
Set-Location -Path $initDir

$gitignorePath = Join-Path $initDir ".gitignore"
$ignoredItems = @(
    "bin/",
    "*.exe",
    "*.o"
)

Add-Content -Path $gitignorePath -Value $ignoredItems

git add .
git commit -m "Initial commit"