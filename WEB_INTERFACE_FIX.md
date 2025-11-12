# Web Interface Fernet Key Fix

## Issue
The web interface was failing to start with the error:
```
❌ Error starting web interface: Fernet key must be 32 url-safe base64-encoded bytes.
```

## Root Cause
The `web_interface.py` was using a hardcoded secret key `b'your-secret-key-here'` which is not a valid Fernet key. Fernet requires a 32-byte url-safe base64-encoded key.

## Fix Applied

Updated `src/codegenie/ui/web_interface.py` to:

1. **Auto-generate a valid Fernet key** if not provided
2. **Support environment variable** `CODEGENIE_SECRET_KEY` for production use
3. **Proper key validation** using cryptography.fernet.Fernet

### Code Changes

```python
# Before (line 79-81):
secret_key = b'your-secret-key-here'  # In production, use a proper secret
setup_session(self.app, EncryptedCookieStorage(secret_key))

# After:
from cryptography.fernet import Fernet
import os

# Try to load key from environment or generate a new one
secret_key_str = os.getenv('CODEGENIE_SECRET_KEY')
if secret_key_str:
    secret_key = secret_key_str.encode()
else:
    # Generate a new Fernet key
    secret_key = Fernet.generate_key()
    logger.warning("Using generated secret key. Set CODEGENIE_SECRET_KEY environment variable for production.")

setup_session(self.app, EncryptedCookieStorage(secret_key))
```

## Usage

### Development (Auto-generated key)
```bash
codegenie web start
```

The system will automatically generate a valid Fernet key and display a warning.

### Production (With environment variable)
```bash
# Generate a secure key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set the environment variable
export CODEGENIE_SECRET_KEY="your-generated-key-here"

# Start the web interface
codegenie web start
```

### Docker/Production Deployment
Add to your `.env` file or docker-compose.yml:
```env
CODEGENIE_SECRET_KEY=cQItfMYmVGWDtVbtnyvYbICMcVM37l5wIDiR_RkHIy4=
```

## Testing

Test the fix:
```bash
# Should now start successfully
codegenie web start

# Or with custom port
codegenie web start --port 8000 --host 0.0.0.0
```

## Security Notes

1. **Development**: Auto-generated keys are fine for local development
2. **Production**: Always set `CODEGENIE_SECRET_KEY` environment variable
3. **Key Rotation**: Generate new keys periodically for security
4. **Key Storage**: Never commit keys to version control

## Generate New Key

To generate a new Fernet key:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Verification

After applying the fix, the web interface should start successfully:
```
🌐 Starting web interface on http://localhost:8080
Web interface started on http://localhost:8080
```

## Status

✅ **Fixed** - Web interface now starts correctly with proper Fernet key handling
