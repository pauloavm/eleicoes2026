$baseDir = Get-Location
$root = Join-Path $baseDir "eleicoes2026"

$directories = @(
    "data",
    "data\raw",
    "data\processed",
    "data\config",
    "src",
    "src\data",
    "src\model",
    "src\view"
)

$files = @(
    "src\data\01_coletor.py",
    "src\data\02_pipeline.py",
    "src\model\03_modelo.py",
    "src\view\04_painel.py",
    "src\view\05_graficos.py",
    "requirements.txt",
    "README.md"
)

# Cria a pasta raiz e as subpastas
New-Item -ItemType Directory -Path $root -Force | Out-Null

foreach ($directory in $directories) {
    $path = Join-Path $root $directory
    New-Item -ItemType Directory -Path $path -Force | Out-Null
}

# Cria arquivos vazios somente quando ainda não existem
foreach ($file in $files) {
    $path = Join-Path $root $file

    if (-not (Test-Path -LiteralPath $path)) {
        New-Item -ItemType File -Path $path | Out-Null
    }
}

Write-Host "Estrutura criada em: $root"