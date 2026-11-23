# =============================================================================
#  HIDE & SAUSAGE - 5FTC2067 Artificial Intelligence Principles Mini Project
#  Student Name : Kenzo Jonathan Harapan Ji      Student ID : 4234QLMV
#
#  build.ps1 - builds the "published game": a single Windows .exe that runs
#  without Python installed.  Output: dist\HideAndSausage.exe
#  Usage (PowerShell):  .\build.ps1
# =============================================================================

$python = ".\.venv\Scripts\python.exe"
$addData = @("assets\images;assets\images", "assets\sounds;assets\sounds", "assets\fonts;assets\fonts")
if (Test-Path "results") { $addData += "results;results" }

# (Testing Mode is my private test tool, so it's left out of the real game)
$pyArgs = @("-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
            "--name", "HideAndSausage", "--icon", "assets\icon.ico",
            "--exclude-module", "hide_and_sausage.ui.scenes_testing")
foreach ($item in $addData) { $pyArgs += @("--add-data", $item) }
$pyArgs += "main.py"

& $python @pyArgs
Write-Host "Built: dist\HideAndSausage.exe"

# Testing Mode on its own, as a second .exe, only for me (it's not handed in,
# so this part is skipped when testing_mode.py isn't there)
if (-not (Test-Path "testing_mode.py")) { exit }
$pyArgs2 = @("-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
             "--name", "DogfatherTestingMode", "--icon", "assets\icon.ico")
foreach ($item in $addData) { $pyArgs2 += @("--add-data", $item) }
$pyArgs2 += "testing_mode.py"
& $python @pyArgs2
Write-Host "Built: dist\DogfatherTestingMode.exe"
