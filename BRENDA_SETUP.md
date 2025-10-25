# BRENDA SOAP API Setup

## Quick Start

### 1. Create Credentials File

Copy the template and edit with your credentials:

```bash
cp brenda_credentials.txt.template brenda_credentials.txt
# Now edit brenda_credentials.txt with your password manager
```

The file should have exactly 2 lines:
```
your.email@example.com
YourVeryComplicatedP@ssw0rd!#$
```

**Important:** You can copy/paste your password from your password manager directly into this file!

### 2. Run the Test

```bash
source venv/bin/activate
python test_brenda_soap_config.py
```

### 3. Expected Results

**If credentials are active (✅):**
```
✅ SUCCESS!
Your BRENDA credentials are ACTIVE and working!
```

**If credentials are pending (⏳):**
```
❌ SOAP FAULT
Error: authentication failed
Possible reasons:
  1. Credentials not yet activated (wait 1-2 business days)
```

## BRENDA Registration

1. Register: https://www.brenda-enzymes.org/register.php
2. Confirm email (arrives within minutes)
3. **Wait 1-2 business days** for admin approval ⏰
4. Then credentials become active

## Files

- `brenda_credentials.txt.template` - Template to copy
- `brenda_credentials.txt` - Your actual credentials (**NEVER COMMIT**)
- `test_brenda_soap_config.py` - Test script
- `.gitignore` - Already ignores `brenda_credentials.txt`

## Security

The credentials file is automatically ignored by git, so it will never be committed to the repository.

## Why Not Just Email Like NCBI?

Unfortunately, BRENDA requires **both email AND password** authentication. This is different from NCBI which only needs email for rate limit notifications.

BRENDA uses SOAP API with SHA256 password hashing for security.
