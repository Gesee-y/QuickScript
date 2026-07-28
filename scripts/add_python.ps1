# Sript used to add python to a computer

Write-Host "[🐍] Installing python..."

$python_location = "C:\Python"

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    & "./configure_winget.ps1"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    winget install --id Python.Python.3.14 --location $python_location --silent --accept-source-agreements --accept-package-agreements

    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $env:Path = "$MachinePath;$UserPath"
}

$PythonCmd = Get-Command python -CommandType Application -ErrorAction SilentlyContinue

if ($PythonCmd) { 
    Write-Host "[✅] Python successfuly installed!"
}
else {
    Write-Host "[⚙️] Python folder missing from PATH. Adding it now..."

    $path = [Environment]::GetEnvironmentVariable("Path", "User")
    $python_bin = Join-Path $python_location "bin"
    $python_scripts = Join-Path $python_location "pythoncore-3.14-64/Scripts"
    [Environment]::SetEnvironmentVariable("Path", "$path;$python_bin;$python_location;$python_scripts", "User")
}