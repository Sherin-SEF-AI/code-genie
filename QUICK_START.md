# 🚀 CodeGenie Quick Start

## Fixed Issues ✅

1. ✅ Added missing `aiohttp-cors` dependency to requirements.txt
2. ✅ Fixed syntax warning in `web_interface.py` (escape sequence)

## Run CodeGenie Now!

### Option 1: Automated Quick Start (Easiest)

```bash
./quick_start.sh
```

This script will:
- Create virtual environment (if needed)
- Install all dependencies
- Let you choose which demo to run

### Option 2: Manual Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run a demo
python test_app.py
```

### Option 3: Run Specific Demos

```bash
# Activate venv first
source venv/bin/activate

# Then run any demo:
python test_app.py                      # Interactive testing
python run_demo_auto.py                 # Full automated demo
python demo_terminal_integration.py     # Terminal features
python demo_nlp_programming.py          # NLP features
python demo_predictive_assistant.py     # Predictive features
python demo_advanced_integration.py     # Multi-agent demo
```

## What Was Fixed

### 1. Missing Dependency
**File**: `requirements.txt`
**Fix**: Added `aiohttp-cors>=0.7.0`

### 2. Syntax Warning
**File**: `src/codegenie/ui/web_interface.py` (line 1105)
**Issue**: Invalid escape sequence `\w` in string
**Fix**: Changed to `\\w` (proper escaping)

## System Requirements

- ✅ Python 3.9+ (You have 3.12.3)
- ✅ Ollama installed (You have 0.11.4)
- ✅ 8GB+ RAM (You have 16GB)
- ✅ 10GB+ disk space (You have 93.3GB)

## Recommended First Run

```bash
./quick_start.sh
# Choose option 1 (Interactive Test App)
```

This gives you a menu to explore all features interactively.

## Troubleshooting

### If you see "externally-managed-environment"
Use the virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### If Ollama is not running
```bash
ollama serve &
```

### If models are missing
```bash
ollama pull llama3.1:8b
ollama pull codellama:7b
```

## Next Steps

1. Run `./quick_start.sh`
2. Choose option 1 (Interactive Test App)
3. Explore the menu options
4. Check documentation in `docs/`

## Support

- Documentation: `docs/USER_GUIDE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- FAQ: `docs/FAQ.md`

---

**Ready to go!** Run `./quick_start.sh` to start exploring CodeGenie! 🧞
