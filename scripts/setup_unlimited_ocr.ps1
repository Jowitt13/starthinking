$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$ThirdParty = Join-Path $Root "third_party"
$OcrDir = Join-Path $ThirdParty "Unlimited-OCR"
$Venv = Join-Path $Root ".venv-ocr"
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (!(Test-Path $ThirdParty)) {
  New-Item -ItemType Directory -Path $ThirdParty | Out-Null
}

if (!(Test-Path $OcrDir)) {
  git clone https://github.com/baidu/Unlimited-OCR.git $OcrDir
}

if (!(Test-Path $BundledPython)) {
  throw "Cannot find Python 3.12 runtime at $BundledPython"
}

uv venv $Venv --python $BundledPython
$Python = Join-Path $Venv "Scripts\python.exe"

$SglangOk = $true
uv pip install --python $Python (Join-Path $OcrDir "wheel\sglang-0.0.0.dev11416+g92e8bb79e-py3-none-any.whl")
if ($LASTEXITCODE -ne 0) {
  $SglangOk = $false
  Write-Warning "SGLang failed to install on native Windows. This is expected because sglang-kernel has no win_amd64 wheel. StartThinking will use qwen3.5:4b vision OCR fallback unless you run Unlimited-OCR inside WSL/Linux."
}
uv pip install --python $Python kernels==0.11.7 pymupdf==1.27.2.2 requests
if ($LASTEXITCODE -ne 0) {
  throw "Failed to install PyMuPDF/requests fallback dependencies."
}

Write-Host ""
if ($SglangOk) {
  Write-Host "Unlimited-OCR environment is ready."
} else {
  Write-Host "Fallback OCR environment is ready. Full Unlimited-OCR still needs WSL/Linux."
}
Write-Host "Python: $Python"
Write-Host "infer.py: $(Join-Path $OcrDir 'infer.py')"
