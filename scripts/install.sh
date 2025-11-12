#!/bin/bash

# CodeGenie Installation Script
# This script automates the installation and setup of CodeGenie

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Check Python version
check_python() {
    print_info "Checking Python installation..."
    
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python not found. Please install Python 3.9 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        print_error "Python 3.9 or higher required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    print_info "Python $PYTHON_VERSION found ✓"
}

# Check Ollama installation
check_ollama() {
    print_info "Checking Ollama installation..."
    
    if ! command_exists ollama; then
        print_warning "Ollama not found."
        read -p "Would you like to install Ollama? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_ollama
        else
            print_error "Ollama is required. Please install it from https://ollama.ai/"
            exit 1
        fi
    else
        print_info "Ollama found ✓"
    fi
}

# Install Ollama
install_ollama() {
    OS=$(detect_os)
    
    print_info "Installing Ollama for $OS..."
    
    if [ "$OS" == "linux" ] || [ "$OS" == "macos" ]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        print_error "Please install Ollama manually from https://ollama.ai/"
        exit 1
    fi
    
    print_info "Ollama installed ✓"
}

# Start Ollama service
start_ollama() {
    print_info "Starting Ollama service..."
    
    if ! pgrep -x "ollama" > /dev/null; then
        ollama serve > /dev/null 2>&1 &
        sleep 3
        print_info "Ollama service started ✓"
    else
        print_info "Ollama service already running ✓"
    fi
}

# Install AI models
install_models() {
    print_info "Installing AI models..."
    
    echo "Which models would you like to install?"
    echo "1) Minimal (llama3.1:8b) - ~5GB"
    echo "2) Recommended (llama3.1:8b + codellama:7b) - ~9GB"
    echo "3) Full (llama3.1:8b + codellama:7b + llama3.1:70b) - ~49GB"
    echo "4) Skip model installation"
    
    read -p "Enter choice (1-4): " choice
    
    case $choice in
        1)
            print_info "Installing llama3.1:8b..."
            ollama pull llama3.1:8b
            ;;
        2)
            print_info "Installing llama3.1:8b..."
            ollama pull llama3.1:8b
            print_info "Installing codellama:7b..."
            ollama pull codellama:7b
            ;;
        3)
            print_info "Installing llama3.1:8b..."
            ollama pull llama3.1:8b
            print_info "Installing codellama:7b..."
            ollama pull codellama:7b
            print_info "Installing llama3.1:70b (this may take a while)..."
            ollama pull llama3.1:70b
            ;;
        4)
            print_warning "Skipping model installation. You'll need to install models manually."
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    print_info "Models installed ✓"
}

# Create virtual environment
create_venv() {
    print_info "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Remove and recreate? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
        else
            return
        fi
    fi
    
    $PYTHON_CMD -m venv venv
    print_info "Virtual environment created ✓"
}

# Activate virtual environment
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        print_error "Could not find virtual environment activation script"
        exit 1
    fi
}

# Install CodeGenie
install_codegenie() {
    print_info "Installing CodeGenie..."
    
    if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        # Development installation
        pip install --upgrade pip
        pip install -e .
    else
        # PyPI installation
        pip install --upgrade pip
        pip install codegenie
    fi
    
    print_info "CodeGenie installed ✓"
}

# Create configuration
create_config() {
    print_info "Creating configuration..."
    
    CONFIG_DIR="$HOME/.config/codegenie"
    mkdir -p "$CONFIG_DIR"
    
    if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
        cat > "$CONFIG_DIR/config.yaml" << EOF
# CodeGenie Configuration

# Model preferences
models:
  default: "llama3.1:8b"
  code_generation: "codellama:7b"
  reasoning: "llama3.1:8b"
  
# Ollama configuration
ollama:
  url: "http://localhost:11434"
  timeout: 300
  
# UI preferences
ui:
  theme: "dark"
  show_reasoning: true
  auto_approve_safe: false
  
# Execution settings
execution:
  sandbox_mode: true
  auto_backup: true
  max_file_size: "10MB"
  parallel_execution: true
  max_concurrent_tasks: 4
  
# Learning preferences
learning:
  save_corrections: true
  adapt_style: true
  remember_patterns: true
  
# Cache settings
cache:
  enabled: true
  ttl: 3600
  max_size: "1GB"
  
# Autonomous mode
autonomous:
  enabled: true
  intervention_points: true
  max_steps: 50
  
# Logging
logging:
  level: "INFO"
  file: "~/.codegenie/logs/codegenie.log"
EOF
        print_info "Configuration created at $CONFIG_DIR/config.yaml ✓"
    else
        print_info "Configuration already exists ✓"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."
    
    # Check CodeGenie command
    if command_exists codegenie; then
        print_info "CodeGenie command available ✓"
    else
        print_warning "CodeGenie command not found in PATH"
    fi
    
    # Check Ollama connection
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_info "Ollama service accessible ✓"
    else
        print_warning "Cannot connect to Ollama service"
    fi
    
    # Check models
    MODELS=$(ollama list 2>/dev/null | tail -n +2 | wc -l)
    if [ "$MODELS" -gt 0 ]; then
        print_info "AI models installed ($MODELS models) ✓"
    else
        print_warning "No AI models installed"
    fi
}

# Print next steps
print_next_steps() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}✓ CodeGenie installation complete!${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Start CodeGenie:"
    echo "   codegenie"
    echo ""
    echo "3. Or start in a specific project:"
    echo "   codegenie /path/to/your/project"
    echo ""
    echo "4. Read the documentation:"
    echo "   - User Guide: docs/USER_GUIDE.md"
    echo "   - Tutorials: docs/TUTORIALS.md"
    echo "   - API Reference: docs/API_REFERENCE.md"
    echo ""
    echo "5. Get help:"
    echo "   codegenie --help"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Main installation flow
main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  CodeGenie Installation Script"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    check_python
    check_ollama
    start_ollama
    install_models
    create_venv
    activate_venv
    install_codegenie
    create_config
    verify_installation
    print_next_steps
}

# Run main installation
main
