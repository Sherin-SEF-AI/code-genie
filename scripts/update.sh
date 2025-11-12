#!/bin/bash

# CodeGenie Update Script
# Safely updates CodeGenie to the latest version

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if CodeGenie is installed
check_installation() {
    if ! command -v codegenie &> /dev/null; then
        print_error "CodeGenie is not installed"
        exit 1
    fi
    
    CURRENT_VERSION=$(codegenie --version 2>/dev/null | awk '{print $2}')
    print_info "Current version: $CURRENT_VERSION"
}

# Backup current installation
backup_installation() {
    print_info "Creating backup..."
    
    BACKUP_DIR="$HOME/.codegenie/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup configuration
    if [ -d "$HOME/.config/codegenie" ]; then
        cp -r "$HOME/.config/codegenie" "$BACKUP_DIR/config"
    fi
    
    # Backup sessions
    if [ -d "$HOME/.codegenie/sessions" ]; then
        cp -r "$HOME/.codegenie/sessions" "$BACKUP_DIR/sessions"
    fi
    
    # Backup cache (optional)
    if [ -d "$HOME/.cache/codegenie" ]; then
        print_warning "Skipping cache backup (can be regenerated)"
    fi
    
    print_info "Backup created at: $BACKUP_DIR"
    echo "$BACKUP_DIR" > "$HOME/.codegenie/last_backup"
}

# Update CodeGenie
update_codegenie() {
    print_info "Updating CodeGenie..."
    
    if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then
        # Development installation
        git pull origin main
        pip install --upgrade -e .
    else
        # PyPI installation
        pip install --upgrade codegenie
    fi
    
    NEW_VERSION=$(codegenie --version 2>/dev/null | awk '{print $2}')
    print_info "Updated to version: $NEW_VERSION"
}

# Run migrations
run_migrations() {
    print_info "Running migrations..."
    
    if [ -f "$HOME/.codegenie/migrations/pending" ]; then
        codegenie migrate || print_warning "Migration failed, but continuing..."
    else
        print_info "No migrations needed"
    fi
}

# Update Ollama models
update_models() {
    print_info "Checking for model updates..."
    
    read -p "Update Ollama models? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        MODELS=$(ollama list | tail -n +2 | awk '{print $1}')
        for model in $MODELS; do
            print_info "Updating $model..."
            ollama pull "$model" || print_warning "Failed to update $model"
        done
    fi
}

# Verify update
verify_update() {
    print_info "Verifying update..."
    
    # Check version
    if command -v codegenie &> /dev/null; then
        print_info "CodeGenie command available ✓"
    else
        print_error "CodeGenie command not found"
        return 1
    fi
    
    # Check configuration
    if [ -f "$HOME/.config/codegenie/config.yaml" ]; then
        print_info "Configuration intact ✓"
    else
        print_warning "Configuration file missing"
    fi
    
    # Test basic functionality
    if codegenie --help &> /dev/null; then
        print_info "Basic functionality working ✓"
    else
        print_error "Basic functionality test failed"
        return 1
    fi
}

# Rollback if needed
rollback() {
    print_error "Update failed. Rolling back..."
    
    if [ -f "$HOME/.codegenie/last_backup" ]; then
        BACKUP_DIR=$(cat "$HOME/.codegenie/last_backup")
        
        if [ -d "$BACKUP_DIR" ]; then
            # Restore configuration
            if [ -d "$BACKUP_DIR/config" ]; then
                rm -rf "$HOME/.config/codegenie"
                cp -r "$BACKUP_DIR/config" "$HOME/.config/codegenie"
            fi
            
            # Restore sessions
            if [ -d "$BACKUP_DIR/sessions" ]; then
                rm -rf "$HOME/.codegenie/sessions"
                cp -r "$BACKUP_DIR/sessions" "$HOME/.codegenie/sessions"
            fi
            
            print_info "Rollback complete"
        else
            print_error "Backup directory not found"
        fi
    else
        print_error "No backup found"
    fi
}

# Print update summary
print_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}✓ CodeGenie update complete!${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Previous version: $CURRENT_VERSION"
    echo "Current version: $NEW_VERSION"
    echo ""
    echo "Backup location: $(cat $HOME/.codegenie/last_backup 2>/dev/null || echo 'N/A')"
    echo ""
    echo "What's new:"
    echo "  - Check CHANGELOG.md for details"
    echo "  - Visit https://github.com/your-org/codegenie/releases"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Main update flow
main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  CodeGenie Update Script"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    check_installation
    backup_installation
    
    if update_codegenie && run_migrations && verify_update; then
        update_models
        print_summary
    else
        rollback
        print_error "Update failed and was rolled back"
        exit 1
    fi
}

# Run main update
main
