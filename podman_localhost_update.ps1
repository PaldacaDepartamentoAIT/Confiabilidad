# Script para actualizar el puente de puertos de Podman / WSL en Windows
# Ejecutar este script en PowerShell como Administrador

# 1. Obtener la IP actual de la máquina virtual de WSL
$wslIpOutput = wsl -d podman-machine-default ip addr show eth0
$ipMatch = [regex]::Match($wslIpOutput, 'inet\s+(\d+\.\d+\.\d+\.\d+)')

if (-not $ipMatch.Success) {
    Write-Error "No se pudo obtener la IP de la máquina virtual de Podman. Asegúrate de que esté encendida."
    exit
}

$currentIp = $ipMatch.Groups[1].Value
Write-Host "IP actual detectada de Podman: $currentIp" -ForegroundColor Green

# 2. Puertos que deseas mapear (puedes agregar o quitar según necesites)
$ports = @(5173, 8000)

foreach ($port in $ports) {
    # Limpiar regla anterior si existe para evitar duplicados
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=127.0.0.1 2>$null

    # Crear la nueva regla de reenvío
    netsh interface portproxy add v4tov4 listenport=$port listenaddress=127.0.0.1 connectport=$port connectaddress=$currentIp
    
    Write-Host "Puente configurado: localhost:$port -> $currentIp:$port" -ForegroundColor Cyan
}

Write-Host "`¡Red configurada con éxito! Ya puedes usar localhost." -ForegroundColor Green