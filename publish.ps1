# Push docs/ to GitHub Pages. First run also creates the repo, enables Pages and makes the install QR.
# Usage: .\publish.ps1 "Add Day 2"
param([string]$Message = "Update")
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
Set-Location $PSScriptRoot
$repo = "toeic800"

$user = gh api user --jq .login
if ($LASTEXITCODE -ne 0) { Write-Host "Not logged in. Run: gh auth login"; exit 1 }
$url = "https://$user.github.io/$repo/"

if (-not (git remote)) {
    gh repo create $repo --public --source . --remote origin
    if ($LASTEXITCODE -ne 0) { exit 1 }
}
if (-not (Test-Path docs\qr.png)) { & tools\python\python.exe make_qr.py $url }

git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { git commit -q -m $Message }
git push -q -u origin main
if ($LASTEXITCODE -ne 0) { exit 1 }

$null = cmd /c "gh api repos/$user/$repo/pages --silent 2>nul"
if ($LASTEXITCODE -ne 0) {
    gh api -X POST "repos/$user/$repo/pages" -f "source[branch]=main" -f "source[path]=/docs" --silent
}
Write-Host "App URL: $url  (live in 1-2 minutes)"
