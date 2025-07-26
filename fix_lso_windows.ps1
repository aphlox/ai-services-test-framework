# Fix Large Send Offload for WSL Network Adapter
# Run this in PowerShell as Administrator on Windows

Write-Host "Fixing Large Send Offload for WSL network adapter..." -ForegroundColor Yellow

# Get WSL network adapter
$wslAdapter = Get-NetAdapter | Where-Object {$_.Name -like "*WSL*" -or $_.InterfaceDescription -like "*WSL*"}

if ($wslAdapter) {
    Write-Host "Found WSL adapter: $($wslAdapter.Name)" -ForegroundColor Green
    
    # Disable LSO v2 for IPv4
    try {
        Set-NetAdapterAdvancedProperty -Name $wslAdapter.Name -RegistryKeyword "*LsoV2IPv4" -RegistryValue 0
        Write-Host "Disabled LSO v2 IPv4" -ForegroundColor Green
    } catch {
        Write-Host "Could not disable LSO v2 IPv4: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Disable LSO v2 for IPv6
    try {
        Set-NetAdapterAdvancedProperty -Name $wslAdapter.Name -RegistryKeyword "*LsoV2IPv6" -RegistryValue 0
        Write-Host "Disabled LSO v2 IPv6" -ForegroundColor Green
    } catch {
        Write-Host "Could not disable LSO v2 IPv6: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Show current LSO settings
    Write-Host "`nCurrent LSO settings:" -ForegroundColor Cyan
    Get-NetAdapterAdvancedProperty -Name $wslAdapter.Name | Where-Object {$_.RegistryKeyword -like "*Lso*"} | Format-Table
    
} else {
    Write-Host "WSL network adapter not found. Listing all adapters:" -ForegroundColor Red
    Get-NetAdapter | Format-Table Name, InterfaceDescription, Status
}

Write-Host "`nAfter making changes, restart WSL with: wsl --shutdown" -ForegroundColor Yellow