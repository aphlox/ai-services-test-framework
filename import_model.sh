#!/bin/bash

# Ollama Model Import Script
# This script helps import externally downloaded models into Ollama

MODELS_DIR="/home/rhox/lama_test/ollama_models"
CONTAINER_NAME="ollama-phi4"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Ollama Model Import Script ===${NC}"
echo

# Function to show usage
show_usage() {
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 <model-file> <model-name>"
    echo "  $0 list                          # List available model files"
    echo "  $0 setup                         # Setup directory structure"
    echo
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 phi-4-mini.gguf phi4-mini     # Import phi-4-mini.gguf as 'phi4-mini'"
    echo "  $0 llama3.2-1b.gguf llama3.2:1b  # Import with version tag"
    echo "  $0 setup                         # Create directories and show instructions"
}

# Function to setup directory structure
setup_directories() {
    echo -e "${BLUE}Setting up model directory structure...${NC}"
    
    # Create directories
    mkdir -p "$MODELS_DIR/gguf"
    mkdir -p "$MODELS_DIR/modelfiles"
    mkdir -p "$MODELS_DIR/downloaded"
    
    echo -e "${GREEN}Created directories:${NC}"
    echo "  $MODELS_DIR/gguf/       - Place .gguf model files here"
    echo "  $MODELS_DIR/modelfiles/ - Place Modelfile configurations here"
    echo "  $MODELS_DIR/downloaded/ - Place complete ollama downloads here"
    echo
    
    # Create example Modelfile
    cat > "$MODELS_DIR/modelfiles/example-modelfile" << 'EOF'
FROM /shared/gguf/your-model.gguf

TEMPLATE """{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
{{ end }}<|assistant|>
"""

PARAMETER stop "<|end|>"
PARAMETER stop "<|system|>"
PARAMETER stop "<|user|>"
PARAMETER stop "<|assistant|>"

SYSTEM """You are a helpful AI assistant."""
EOF
    
    echo -e "${GREEN}Created example Modelfile at:${NC} $MODELS_DIR/modelfiles/example-modelfile"
    echo
    
    # Create instructions file
    cat > "$MODELS_DIR/INSTRUCTIONS.md" << 'EOF'
# Ollama Model Import Instructions

## Directory Structure
- `gguf/` - Place .gguf model files here
- `modelfiles/` - Place Modelfile configurations here  
- `downloaded/` - Place complete ollama downloads here

## Download Models Externally

### Option 1: Direct .gguf Downloads
1. Visit Hugging Face: https://huggingface.co/models
2. Search for your desired model (e.g., "Microsoft/Phi-4")
3. Download the .gguf file
4. Place in `gguf/` directory
5. Run: `./import_model.sh your-model.gguf model-name`

### Option 2: Use Windows Ollama
1. Install Ollama on Windows: https://ollama.com/download
2. Download model: `ollama pull phi4`
3. Copy model files from Windows to WSL2
4. Import using this script

### Option 3: Direct Downloads with wget/curl
```bash
# Example: Download TinyLlama
cd gguf/
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf

# Import
cd ..
./import_model.sh gguf/Phi-3-mini-4k-instruct-q4.gguf phi3-mini
```

## Supported Formats
- .gguf files (recommended)
- Ollama model directories
- Custom Modelfiles

## Common Models to Try
- TinyLlama: ~637MB - Good for testing
- Phi-3 Mini: ~2.3GB - Microsoft's efficient model
- Llama 3.2 1B: ~1.3GB - Meta's latest small model
- CodeLlama: Various sizes - Coding assistant
EOF
    
    echo -e "${GREEN}Created instructions at:${NC} $MODELS_DIR/INSTRUCTIONS.md"
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Download a model file to $MODELS_DIR/gguf/"
    echo "2. Run: $0 <model-file> <model-name>"
    echo "3. Access via: docker exec $CONTAINER_NAME ollama run <model-name>"
}

# Function to list available models
list_models() {
    echo -e "${BLUE}Available model files in $MODELS_DIR:${NC}"
    echo
    
    if [ -d "$MODELS_DIR/gguf" ] && [ "$(ls -A "$MODELS_DIR/gguf" 2>/dev/null)" ]; then
        echo -e "${GREEN}GGUF Files:${NC}"
        ls -la "$MODELS_DIR/gguf"/*.gguf 2>/dev/null || echo "  No .gguf files found"
        echo
    fi
    
    if [ -d "$MODELS_DIR/modelfiles" ] && [ "$(ls -A "$MODELS_DIR/modelfiles" 2>/dev/null)" ]; then
        echo -e "${GREEN}Modelfiles:${NC}"
        ls -la "$MODELS_DIR/modelfiles"/* 2>/dev/null || echo "  No modelfiles found"
        echo
    fi
    
    echo -e "${BLUE}Installed models in Ollama:${NC}"
    docker exec "$CONTAINER_NAME" ollama list 2>/dev/null || echo "  Container not running or no models installed"
}

# Function to import a model
import_model() {
    local model_file="$1"
    local model_name="$2"
    local full_path="$MODELS_DIR/$model_file"
    
    # Check if file exists
    if [ ! -f "$full_path" ]; then
        echo -e "${RED}Error: Model file not found: $full_path${NC}"
        echo "Available files:"
        list_models
        exit 1
    fi
    
    # Check if container is running
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${YELLOW}Starting Ollama container...${NC}"
        cd /home/rhox/lama_test
        docker-compose up -d
        sleep 10
    fi
    
    echo -e "${BLUE}Importing model: $model_file as '$model_name'${NC}"
    echo
    
    # Copy file to container's shared directory
    echo -e "${YELLOW}Copying model file to container...${NC}"
    
    # Create Modelfile for the import
    local modelfile_path="$MODELS_DIR/modelfiles/import-$model_name"
    cat > "$modelfile_path" << EOF
FROM /shared/$model_file

TEMPLATE """{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
{{ end }}<|assistant|>
"""

PARAMETER stop "<|end|>"
PARAMETER temperature 0.7
PARAMETER top_p 0.9

SYSTEM """You are a helpful AI assistant."""
EOF
    
    echo -e "${YELLOW}Creating model in Ollama...${NC}"
    
    # Import the model
    if docker exec "$CONTAINER_NAME" ollama create "$model_name" -f "/shared/modelfiles/import-$model_name"; then
        echo
        echo -e "${GREEN}✅ Model '$model_name' imported successfully!${NC}"
        echo
        echo -e "${YELLOW}Test the model with:${NC}"
        echo "  docker exec -it $CONTAINER_NAME ollama run $model_name"
        echo
        echo -e "${YELLOW}Or via API:${NC}"
        echo "  curl http://localhost:11434/api/generate -d '{\"model\":\"$model_name\",\"prompt\":\"Hello!\"}'"
    else
        echo -e "${RED}❌ Failed to import model${NC}"
        exit 1
    fi
}

# Main script logic
case "${1:-}" in
    "setup")
        setup_directories
        ;;
    "list")
        list_models
        ;;
    "")
        show_usage
        ;;
    *)
        if [ $# -ne 2 ]; then
            echo -e "${RED}Error: Invalid arguments${NC}"
            show_usage
            exit 1
        fi
        import_model "$1" "$2"
        ;;
esac