# #################################################### Test Runner #################################################### #

$srcFiles = Get-ChildItem -Path "src" -Filter *.c -Recurse | Select-Object -ExpandProperty FullName
$failure = 0
$count = 0

Get-ChildItem -Path "tests" -Filter *.c | For-Each-Object {
    $outputExe = "bin\$($_.BaseName).exe"
    gcc $srcFiles $_.FullName -o $outputExe

    if ($LASTEXITCODE -eq 0) {
        & $outputExe
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] $($_.BaseName)" -ForegroundColor Green
        } else {
            $failure++
            Write-Host "  [FAILURE] $($_.BaseName)" -ForegroundColor Red
        }
    }
    else {
        $failure++
        Write-Host "  [COMPILATION ERROR] $($_.BaseName)" -ForegroundColor Red
    }


    $count++
}

Write-Host ""
Write-Host "$($count - $failure)/$count Tests passed !"

if ($failure -gt 0) {
    exit 1
}
else {
    exit 0
}