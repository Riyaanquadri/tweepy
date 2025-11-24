# How to Run the OAuth2 PKCE Flow

This document provides step-by-step instructions for running the OAuth2 PKCE authentication flow to get valid tokens for the Twitter bot.

## Prerequisites

✓ Flask installed (already done: `pip install flask`)
✓ Client ID from Twitter Developer Portal
✓ Redirect URI registered in your app settings

## Complete Workflow

### Step 1: Generate Authorization URL + PKCE Verifier

Run the PKCE generator:

```bash
.venv/bin/python3 app/oauth_pkce.py
```

**Output:**
```
PKCE code_verifier (save this securely):
 AbCdEfGhIjKlMnOpQrStUvWxYz123456789_AbCdEfGhIjK

Open this URL in your browser (login as the bot account):

https://twitter.com/i/oauth2/authorize?response_type=code&client_id=YOUR_CLIENT_ID&...
```

**⚠️ Important:** Copy and save the `code_verifier` value — you'll need it in the next step.

---

### Step 2: Set the Code Verifier in Environment

Before starting the callback server, export the verifier:

**On macOS/Linux:**
```bash
export TW_CODE_VERIFIER="AbCdEfGhIjKlMnOpQrStUvWxYz123456789_AbCdEfGhIjK"
```

**On Windows (PowerShell):**
```powershell
$env:TW_CODE_VERIFIER = "AbCdEfGhIjKlMnOpQrStUvWxYz123456789_AbCdEfGhIjK"
```

**Or add to `.env` permanently:**
```
TW_CODE_VERIFIER=AbCdEfGhIjKlMnOpQrStUvWxYz123456789_AbCdEfGhIjK
```

---

### Step 3: Start the Callback Server

```bash
.venv/bin/python3 app/oauth_callback.py
```

**Output:**
```
Starting OAuth callback server on http://127.0.0.1:5000
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

The server is now listening for the OAuth callback.

---

### Step 4: Open Authorization URL in Browser

1. Copy the authorization URL from Step 1
2. Open it in your browser
3. **Make sure you're logged in as `OnChainSlueth`** (or your bot account)
4. Click **"Authorize"** to approve the app
5. Twitter will redirect to `http://127.0.0.1:5000/callback?code=...&state=...`

---

### Step 5: Callback Server Receives & Exchanges Code

The Flask server automatically receives the redirect with the authorization code:

**Console output:**
```
Tokens written to oauth_tokens.env
Success! Token exchange complete. Save the tokens securely.

{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 7200,
  "refresh_token": "...",
  "scope": "tweet.read tweet.write users.read offline.access"
}
```

**Browser shows:**
```
Success! Token exchange complete. Save the tokens securely.

{
  "access_token": "...",
  "token_type": "Bearer",
  ...
}
```

---

### Step 6: Copy Tokens to `.env`

A new file `oauth_tokens.env` is created in the repo root. Copy these to your `.env`:

```dotenv
OAUTH2_USER_ACCESS_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
OAUTH2_USER_REFRESH_TOKEN=...
OAUTH2_TOKEN_EXPIRES_IN=7200
OAUTH2_SCOPE=tweet.read tweet.write users.read offline.access
```

**⚠️ Important:** `oauth_tokens.env` is in `.gitignore` — do NOT commit real tokens to Git.

---

## Optional: Using ngrok for Public HTTPS URL

If you need a public HTTPS URL (e.g., testing from a different machine):

### Install ngrok
```bash
brew install ngrok  # macOS
# or download from https://ngrok.com/download
```

### Start ngrok tunnel
```bash
ngrok http 5000
```

**Output:**
```
Forwarding    https://abc123.ngrok.io -> http://localhost:5000
```

### Update Redirect URI

1. In `.env`, update:
   ```
   TW_REDIRECT_URI=https://abc123.ngrok.io/callback
   ```

2. In Twitter Developer Portal, add `https://abc123.ngrok.io/callback` as authorized redirect URI

3. Generate new authorization URL:
   ```bash
   .venv/bin/python3 app/oauth_pkce.py
   ```

4. Follow Steps 2-6 as above (ngrok will forward traffic to your local callback server)

---

## Troubleshooting

### ❌ "TW_CODE_VERIFIER not set in environment"

**Cause:** You didn't set the verifier before starting the callback server.

**Fix:**
```bash
export TW_CODE_VERIFIER="your_verifier_here"
.venv/bin/python3 app/oauth_callback.py
```

Or add to `.env` and restart.

---

### ❌ "Token exchange failed: 400"

**Cause:** Bad request to Twitter API. Check:
- `TW_CLIENT_ID` is correct
- `TW_REDIRECT_URI` matches what's registered in Developer Portal
- `TW_CODE_VERIFIER` is exactly what oauth_pkce.py printed

**Fix:** Regenerate authorization URL and try again.

---

### ❌ "Redirect URI mismatch"

**Cause:** The redirect URI doesn't match what's registered.

**Fix:**
1. Go to Twitter Developer Portal
2. Find your app settings
3. Add `http://127.0.0.1:5000/callback` (or your ngrok URL + /callback) as authorized redirect URI
4. Regenerate authorization URL and try again

---

### ❌ Browser shows error during authorization

**Examples:** "Invalid client_id", "Invalid redirect_uri", "Invalid scope"

**Fix:**
1. Check `TW_CLIENT_ID` in `.env` is correct
2. Make sure app type supports OAuth2
3. Verify all redirect URIs are registered in Developer Portal
4. Regenerate authorization URL with new `.env` values:
   ```bash
   .venv/bin/python3 app/oauth_pkce.py
   ```

---

### ❌ Tokens expire (401 errors after 2 hours)

**Cause:** OAuth2 access tokens expire after ~2 hours.

**Fix:** Implement token refresh in the bot:
```python
from app.config import Config
import requests

def refresh_oauth_token():
    data = {
        "grant_type": "refresh_token",
        "refresh_token": Config.OAUTH2_USER_REFRESH_TOKEN,
        "client_id": Config.TW_CLIENT_ID,
    }
    resp = requests.post("https://api.twitter.com/2/oauth2/token", data=data)
    new_tokens = resp.json()
    # Update Config with new access_token and expires_in
```

---

## Next Steps

After obtaining tokens in `oauth_tokens.env`:

1. Copy tokens to `.env`
2. Update `app/config.py` to load OAuth2 tokens
3. Update `app/main.py` or Twitter client initialization to use OAuth2 bearer token instead of API key/secret
4. Test the bot with new authentication:
   ```bash
   .venv/bin/python3 app/main.py
   ```

---

## Files Involved

- `app/oauth_pkce.py` - Generates authorization URL + PKCE verifier
- `app/oauth_callback.py` - Flask server to receive code and exchange for tokens
- `oauth_tokens.env` - Generated file (NOT committed) with access/refresh tokens
- `.env` - Your main config file where you copy the tokens
