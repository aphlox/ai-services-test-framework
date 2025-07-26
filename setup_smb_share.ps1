# Setup SMB Share for Ollama Models
# Run this in PowerShell as Administrator on Windows

param(
    [string]$SharePath = "C:\OllamaModels",
    [string]$ShareName = "OllamaModels"
)

Write-Host "Setting up SMB share for external Ollama model downloads..." -ForegroundColor Yellow

# Create the directory if it doesn't exist
if (!(Test-Path $SharePath)) {
    New-Item -ItemType Directory -Path $SharePath -Force
    Write-Host "Created directory: $SharePath" -ForegroundColor Green
} else {
    Write-Host "Directory already exists: $SharePath" -ForegroundColor Green
}

# Remove existing share if it exists
$existingShare = Get-SmbShare -Name $ShareName -ErrorAction SilentlyContinue
if ($existingShare) {
    Remove-SmbShare -Name $ShareName -Force
    Write-Host "Removed existing share: $ShareName" -ForegroundColor Yellow
}

# Create SMB share
try {
    New-SmbShare -Name $ShareName -Path $SharePath -FullAccess "Everyone"
    Write-Host "Created SMB share: \\localhost\$ShareName -> $SharePath" -ForegroundColor Green
} catch {
    Write-Host "Error creating SMB share: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Set permissions
try {
    Grant-SmbShareAccess -Name $ShareName -AccountName "Everyone" -AccessRight Full -Force
    Write-Host "Granted full access to Everyone" -ForegroundColor Green
} catch {
    Write-Host "Warning: Could not set share permissions: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Create models subdirectory structure
$modelsPath = Join-Path $SharePath "models"
if (!(Test-Path $modelsPath)) {
    New-Item -ItemType Directory -Path $modelsPath -Force
    Write-Host "Created models directory: $modelsPath" -ForegroundColor Green
}

# Create download instructions file
$instructionsPath = Join-Path $SharePath "DOWNLOAD_INSTRUCTIONS.txt"
$instructions = @"
SMB Share Setup Complete!

Share Location: \\localhost\$ShareName
Local Path: $SharePath

DOWNLOAD INSTRUCTIONS:
======================

1. Download Ollama models manually to this folder:
   - Visit: https://ollama.com/library
   - Download .gguf files directly or use ollama CLI on Windows
   
2. For Phi-4 model specifically:
   - Model file should be named: phi-4.gguf or similar
   - Place in: $SharePath\models\
   
3. Supported model formats:
   - .gguf files (Hugging Face format)
   - Ollama blob files
   - Model directories with Modelfile
   
4. After downloading, the WSL2 Docker container will access models via:
   /shared/models/

5. To import downloaded models into Ollama:
   docker exec ollama-phi4 ollama create <model-name> -f /shared/models/<model-file>

TROUBLESHOOTING:
================
- Ensure Windows SMB services are running
- Check Windows Firewall settings for SMB (port 445)
- Verify WSL2 can access Windows drives
- Use 'net use' command to test SMB access

Created: $(Get-Date)
"@

Set-Content -Path $instructionsPath -Value $instructions
Write-Host "Created instructions file: $instructionsPath" -ForegroundColor Green

# Show share information
Write-Host "`nSMB Share Information:" -ForegroundColor Cyan
Get-SmbShare -Name $ShareName | Format-List

Write-Host "`nSetup complete! You can now:" -ForegroundColor Green
Write-Host "1. Access the share at: \\localhost\$ShareName" -ForegroundColor White
Write-Host "2. Download models manually to: $SharePath" -ForegroundColor White
Write-Host "3. Models will be accessible to Docker via /shared/models/" -ForegroundColor White