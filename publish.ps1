# docs/ 폴더를 GitHub Pages에 올린다. 처음 실행하면 저장소 생성 + Pages 활성화 + QR 생성까지 한다.
# 사용법: .\publish.ps1 "Day 2 추가"
param([string]$Message = "업데이트")
$ErrorActionPreference = "Stop"
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
Set-Location $PSScriptRoot
$repo = "toeic800"

$user = gh api user --jq .login
$url = "https://$user.github.io/$repo/"

if (-not (git remote 2>$null | Select-String origin)) {
    gh repo create $repo --public --source . --remote origin | Out-Null
}
if (-not (Test-Path docs\qr.png)) { & tools\python\python.exe make_qr.py $url }

git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) { git commit -q -m $Message }
git push -q -u origin main

gh api "repos/$user/$repo/pages" --silent 2>$null
if ($LASTEXITCODE -ne 0) {
    gh api -X POST "repos/$user/$repo/pages" -f "source[branch]=main" -f "source[path]=/docs" --silent
}
Write-Host "앱 주소: $url  (반영까지 1~2분)"
