# Registry-based LSO fix for WSL network adapter
# Run this in PowerShell as Administrator on Windows

Write-Host "Applying registry-based LSO fix for WSL..." -ForegroundColor Yellow

# Find WSL network adapter registry keys
$networkAdapters = Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}" -ErrorAction SilentlyContinue

foreach ($adapter in $networkAdapters) {
    $driverDesc = Get-ItemProperty -Path $adapter.PSPath -Name "DriverDesc" -ErrorAction SilentlyContinue
    
    if ($driverDesc -and ($driverDesc.DriverDesc -like "*Hyper-V*" -or $driverDesc.DriverDesc -like "*WSL*")) {
        Write-Host "Found WSL/Hyper-V adapter: $($driverDesc.DriverDesc)" -ForegroundColor Green
        
        try {
            # Disable LSO v2 IPv4
            Set-ItemProperty -Path $adapter.PSPath -Name "*LsoV2IPv4" -Value "0" -ErrorAction SilentlyContinue
            Write-Host "  - Disabled LSO v2 IPv4" -ForegroundColor Green
            
            # Disable LSO v2 IPv6  
            Set-ItemProperty -Path $adapter.PSPath -Name "*LsoV2IPv6" -Value "0" -ErrorAction SilentlyContinue
            Write-Host "  - Disabled LSO v2 IPv6" -ForegroundColor Green
            
            # Additional TCP optimization
            Set-ItemProperty -Path $adapter.PSPath -Name "*TCPChecksumOffloadIPv4" -Value "0" -ErrorAction SilentlyContinue
            Set-ItemProperty -Path $adapter.PSPath -Name "*TCPChecksumOffloadIPv6" -Value "0" -ErrorAction SilentlyContinue
            Write-Host "  - Disabled TCP checksum offload" -ForegroundColor Green
            
        } catch {
            Write-Host "  - Error applying settings: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host "`nRegistry changes applied. Please restart your computer for full effect." -ForegroundColor Yellow
Write-Host "Or at minimum: wsl --shutdown && restart network adapter" -ForegroundColor Yellow