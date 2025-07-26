# Network reset for WSL issues
# Run this in PowerShell as Administrator on Windows

Write-Host "Performing network reset for WSL..." -ForegroundColor Yellow

# Reset WSL network
Write-Host "1. Shutting down WSL..." -ForegroundColor Cyan
wsl --shutdown

# Reset network components
Write-Host "2. Resetting network components..." -ForegroundColor Cyan
netsh winsock reset
netsh int ip reset
netsh int tcp reset
ipconfig /flushdns

# Restart WSL networking
Write-Host "3. Restarting WSL networking..." -ForegroundColor Cyan
Restart-Service -Name "LxssManager" -Force -ErrorAction SilentlyContinue

Write-Host "`nNetwork reset complete. Please restart your computer." -ForegroundColor Green
Write-Host "After restart, WSL networking should be refreshed." -ForegroundColor Yellow