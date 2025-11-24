# OAuth2 PKCE Flow Setup Guide

This guide walks through setting up OAuth2 authentication for the Twitter API using PKCE (Proof Key for Code Exchange).

## Prerequisites

1. **Twitter Developer Portal Access**: Go to https://developer.twitter.com/en/portal/dashboard
2. **App Created**: Create an app if you haven't already
3. **OAuth2 Enabled**: Ensure your app has OAuth2 authentication enabled
4. **Client ID**: Get your `Client ID` from the Developer Portal
5. **Redirect URI**: Set `http://127.0.0.1:5000/callback` as an authorized redirect URI in your app settings

## Step 1: Get Your Client ID

1. Go to https://developer.twitter.com/en/portal/dashboard
2. Select your app
3. Go to "Settings" → "Authentication Settings"
4. Scroll to "OAuth2.0 Client ID and Client Secret"
5. Copy your **Client ID**
6. Add it to `.env`:
   ```
   TW_CLIENT_ID=your_client_id_here
   ```

## Step 2: Generate Authorization URL

Run the PKCE generator to create an authorization URL:

```bash
.venv/bin/python3 app/oauth_pkce.py
```

This will print:
- **PKCE code_verifier** (a random string) - **Save this!** You'll need it in the next step.
- **Authorization URL** - A long URL to open in your browser

Example output:
```
PKCE code_verifier (save this securely):
 Ke9p...GhJw

Open this URL in your browser (login as the bot account):

https://twitter.com/i/oauth2/authorize?response_type=code&client_id=...&code_challenge=...
```

## Step 3: Authorize in Browser

1. Copy the printed authorization URL
2. Open it in your browser
3. Log in as your **bot account** (the account that will post tweets)
4. Click "Authorize" to approve the app
5. You'll be redirected to `http://127.0.0.1:5000/callback?code=...&state=...`

## Step 4: Exchange Code for Tokens

Before running the callback server, set the code verifier:

```bash
export TW_CODE_VERIFIER="Ke9p...GhJw"  # Paste the verifier from Step 2
```

Or add it to `.env`:
```
TW_CODE_VERIFIER=Ke9p...GhJw
```

Then start the Flask callback server:

```bash
.venv/bin/python3 app/oauth_callback.py
```

The browser will redirect automatically (since you authorized in Step 3), and:
- The Flask server will receive the code
- Exchange it for OAuth tokens
- Print the tokens in console
- Write tokens to `oauth_tokens.env` (a new file in the repo root)

Example console output:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 7200,
  "refresh_token": "...",
  "scope": "tweet.read tweet.write users.read offline.access"
}
```

## Step 5: Copy Tokens to .env

From the console output or `oauth_tokens.env`, copy the tokens to your `.env`:

```
OAUTH2_USER_ACCESS_TOKEN=eyJhbGc...
OAUTH2_USER_REFRESH_TOKEN=...
OAUTH2_TOKEN_EXPIRES_IN=7200
OAUTH2_SCOPE=tweet.read tweet.write users.read offline.access
```

## Step 6: Update Bot to Use OAuth2

Update `app/config.py` and `app/main.py` to load and use these OAuth2 tokens instead of API key/secret.

## Troubleshooting

### "TW_CLIENT_ID not set" error
- Make sure `TW_CLIENT_ID` is in your `.env` file
- Run `python3 -c "from dotenv import load_dotenv; import os; load_dotenv('.env'); print(os.getenv('TW_CLIENT_ID'))"` to verify it's loaded

### "TW_CODE_VERIFIER not set" error in Step 4
- You didn't set the code verifier before starting the callback server
- Export it first: `export TW_CODE_VERIFIER="..."`
- Or add it to `.env` and restart the callback server

### "Redirect URI mismatch" error
- Make sure `http://127.0.0.1:5000/callback` is registered in your Twitter app settings
- Or change `TW_REDIRECT_URI` in `.env` to match what you registered

### Tokens not working after using them
- OAuth2 access tokens expire (typically after 2 hours)
- Use the `refresh_token` to get a new access token
- Implement token refresh logic in the bot

## Files Created

- `app/oauth_pkce.py` - Generates authorization URL + PKCE verifier
- `app/oauth_callback.py` - Flask server to receive the code and exchange for tokens
- `oauth_tokens.env` - Generated file (added to .gitignore) containing tokens
