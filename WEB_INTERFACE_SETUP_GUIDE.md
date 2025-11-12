# Web Interface Setup Guide

## Issue Fixed

✅ **Resolved Fernet key error**: "Fernet key must be 32 url-safe base64-encoded bytes"

The web interface now properly generates and handles Fernet encryption keys.

## Installation

### 1. Install Required Dependencies

The web interface requires additional Python packages:

```bash
# If you're in a virtual environment (recommended)
pip install aiohttp aiohttp-cors aiohttp-session cryptography

# If not in a virtual environment
pip3 install --user aiohttp aiohttp-cors aiohttp-session cryptography
```

### 2. Verify Installation

```bash
python3 -c "from cryptography.fernet import Fernet; from aiohttp_session.cookie_storage import EncryptedCookieStorage; print('✓ All dependencies available')"
```

## Usage

### Development Mode (Auto-generated key)

```bash
codegenie web start
```

The system will:
- Auto-generate a secure Fernet key
- Display a warning about using a generated key
- Start the web interface on http://localhost:8080

### Production Mode (With environment variable)

1. Generate a secure key:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

2. Set the environment variable:
```bash
export CODEGENIE_SECRET_KEY="your-generated-key-here"
```

3. Start the web interface:
```bash
codegenie web start
```

### Custom Port and Host

```bash
# Custom port
codegenie web start --port 8000

# Custom host (for network access)
codegenie web start --host 0.0.0.0 --port 8080

# With project path
codegenie web start --project-path /path/to/project
```

## Configuration

### Environment Variables

- `CODEGENIE_SECRET_KEY`: Fernet encryption key for session storage (required for production)

### Docker/Production Deployment

Add to your `.env` file:
```env
CODEGENIE_SECRET_KEY=cQItfMYmVGWDtVbtnyvYbICMcVM37l5wIDiR_RkHIy4=
```

Or in docker-compose.yml:
```yaml
services:
  codegenie:
    environment:
      - CODEGENIE_SECRET_KEY=cQItfMYmVGWDtVbtnyvYbICMcVM37l5wIDiR_RkHIy4=
```

## Troubleshooting

### Error: "Fernet key must be 32 url-safe base64-encoded bytes"

✅ **Fixed in latest version**. Update your code:
```bash
git pull origin main
```

### Error: "ModuleNotFoundError: No module named 'aiohttp_session'"

Install the missing dependencies:
```bash
pip install aiohttp aiohttp-cors aiohttp-session cryptography
```

### Error: "externally-managed-environment"

You're using a system Python. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows

# Then install dependencies
pip install aiohttp aiohttp-cors aiohttp-session cryptography
```

### Web interface not accessible from other machines

Use `--host 0.0.0.0` to bind to all interfaces:
```bash
codegenie web start --host 0.0.0.0 --port 8080
```

## Security Best Practices

1. **Development**: Auto-generated keys are fine for local testing
2. **Production**: Always set `CODEGENIE_SECRET_KEY` environment variable
3. **Key Rotation**: Generate new keys periodically
4. **Key Storage**: Never commit keys to version control
5. **HTTPS**: Use HTTPS in production (reverse proxy recommended)

## Features

The web interface provides:
- 📊 Real-time workflow visualization
- 🔄 Live progress updates via WebSocket
- 📝 Interactive code diff viewer
- ✅ Approval interface for file operations
- 📈 Progress dashboard and metrics
- 🎯 Command output streaming
- 🔍 Project context visualization

## API Endpoints

Once started, the web interface exposes:
- `GET /` - Main dashboard
- `GET /api/status` - Server status
- `GET /api/workflows` - List active workflows
- `POST /api/workflows` - Create new workflow
- `WS /ws` - WebSocket for real-time updates

## Next Steps

1. Install dependencies (see Installation section)
2. Start the web interface: `codegenie web start`
3. Open http://localhost:8080 in your browser
4. Explore the interactive features

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the main README.md
- Check the GitHub issues page

---

**Status**: ✅ Web interface ready to use with proper Fernet key handling
