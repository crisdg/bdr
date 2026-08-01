# Corre el cruce C12 -> C13 y lo valida contra el archivo de referencia.
#
#   .\probar.ps1                  # usa los archivos del caso C12/C13
#   .\probar.ps1 -Archivos "C:\otra\carpeta"

param(
    [string]$Archivos = "C:\Cris\archivos\BDR C12-C13\BDR C12-C13\para PPM",
    [string]$N        = "LEADER C12 2026.XLSX",
    [string]$N1       = "LEADER C13 2026.XLSX",
    [string]$Ref      = "LEADER C12 2026 con cod c13.xlsx",
    [string]$Salida   = "salida\LEADER C12 2026 con cod c13 - generado.xlsx"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = Join-Path $PSScriptRoot "src"

$rutaN   = Join-Path $Archivos $N
$rutaN1  = Join-Path $Archivos $N1
$rutaRef = Join-Path $Archivos $Ref

foreach ($ruta in @($rutaN, $rutaN1)) {
    if (-not (Test-Path $ruta)) {
        Write-Error "No se encuentra: $ruta"
    }
}

$argumentos = @("-m", "bdr_leader_merge.cli", "--n", $rutaN, "--n1", $rutaN1, "--out", $Salida)
if (Test-Path $rutaRef) {
    $argumentos += @("--reference", $rutaRef)
} else {
    Write-Host "Sin referencia ($Ref): se omite la validacion." -ForegroundColor Yellow
}

& python @argumentos
