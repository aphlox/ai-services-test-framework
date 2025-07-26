#!/bin/bash

# Enable SSH on WSL2 Ubuntu
echo "=== Enabling SSH on WSL2 Ubuntu ==="

# Check if SSH is installed
if ! command -v sshd &> /dev/null; then
    echo "SSH server not found. Please install with:"
    echo "sudo apt update && sudo apt install openssh-server"
    exit 1
fi

echo "✅ SSH server is installed"

# Create SSH host keys if they don't exist
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    echo "🔑 Generating SSH host keys..."
    sudo ssh-keygen -A
fi

# Configure SSH for WSL2
echo "⚙️ Configuring SSH..."

# Backup original config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup 2>/dev/null || true

# Configure SSH settings
sudo tee /etc/ssh/sshd_config.d/wsl2.conf > /dev/null << 'EOF'
# WSL2 SSH Configuration
Port 22
PermitRootLogin yes
PasswordAuthentication yes
PubkeyAuthentication yes
X11Forwarding yes
AllowUsers rhox root
EOF

echo "✅ SSH configuration updated"

# Start SSH service
echo "🚀 Starting SSH service..."
sudo service ssh start

# Check SSH status
if sudo service ssh status | grep -q "running"; then
    echo "✅ SSH service is running"
else
    echo "❌ SSH service failed to start"
    sudo service ssh status
    exit 1
fi

# Get WSL2 IP address
WSL_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "🌐 SSH server is ready!"
echo "📍 WSL2 IP Address: $WSL_IP"
echo "🔗 Connect with: ssh rhox@$WSL_IP"
echo "🔗 Or from Windows: ssh rhox@$WSL_IP"
echo ""
echo "📝 To connect from Windows:"
echo "   1. Open Command Prompt or PowerShell"
echo "   2. Run: ssh rhox@$WSL_IP"
echo "   3. Enter your Ubuntu password"
echo ""
echo "🔒 To set up key-based authentication:"
echo "   ssh-keygen -t rsa -b 4096"
echo "   ssh-copy-id rhox@$WSL_IP"
echo ""

# Show how to make SSH start automatically
echo "🚀 To start SSH automatically on WSL2 boot:"
echo "   Add to ~/.bashrc or ~/.profile:"
echo "   sudo service ssh start"
echo ""

# Test SSH locally
echo "🧪 Testing SSH connection locally..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes rhox@localhost exit 2>/dev/null; then
    echo "✅ SSH is working locally"
else
    echo "⚠️  SSH test failed - you may need to set up keys or check firewall"
fi