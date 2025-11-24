"""
Small Flask app to receive the OAuth2 redirect (code) and exchange for tokens.
Run: .venv/bin/python3 app/oauth_callback.py
Then visit the authorization URL (created by oauth_pkce.py).
This will print tokens and write them to oauth_tokens.env (do NOT commit).
"""
from flask import Flask, request, redirect
import os, requests, urllib.parse
from dotenv import load_dotenv
import json

load_dotenv(dotenv_path=".env")
CLIENT_ID = os.getenv("TW_CLIENT_ID")
# If your portal provided a client secret AND the flow requires it, set it in .env as TW_CLIENT_SECRET. For PKCE it's optional.
CLIENT_SECRET = os.getenv("TW_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("TW_REDIRECT_URI", "http://127.0.0.1:5000/callback")
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

app = Flask(__name__)

# Replace this with the actual verifier you saved from oauth_pkce.py if you stored it elsewhere.
# For convenience, if you printed verifier you can paste it into environment variable TW_CODE_VERIFIER.
CODE_VERIFIER = os.getenv("TW_CODE_VERIFIER")  # set before exchange

@app.route("/")
def index():
    return "OAuth callback server. Use /callback to finish the flow."

@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        return f"Error from provider: {error}", 400
    code = request.args.get("code")
    state = request.args.get("state")
    if not code:
        return "No code found in request", 400
    # ensure we have the verifier
    verifier = CODE_VERIFIER
    if not verifier:
        return ("TW_CODE_VERIFIER not set in environment. "
                "Set TW_CODE_VERIFIER to the code_verifier value that oauth_pkce.py printed."), 500

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    # Use HTTP Basic Auth with client_id and client_secret
    auth = (CLIENT_ID, CLIENT_SECRET) if CLIENT_SECRET else None
    resp = requests.post(TOKEN_URL, data=data, headers=headers, auth=auth)
    if resp.status_code != 200:
        return f"Token exchange failed: {resp.status_code}\n{resp.text}", 500

    token_data = resp.json()
    # token_data contains: access_token, token_type, expires_in, refresh_token, scope
    # Save tokens securely to a file (do not commit)
    out_file = "oauth_tokens.env"
    with open(out_file, "w") as f:
        f.write(f'OAUTH2_USER_ACCESS_TOKEN={token_data.get("access_token")}\n')
        f.write(f'OAUTH2_USER_REFRESH_TOKEN={token_data.get("refresh_token")}\n')
        f.write(f'OAUTH2_TOKEN_EXPIRES_IN={token_data.get("expires_in")}\n')
        f.write(f'OAUTH2_SCOPE={token_data.get("scope")}\n')
    print("Tokens written to", out_file)
    pretty = json.dumps(token_data, indent=2)
    return f"Success! Token exchange complete. Save the tokens securely.\n\n{pretty}"

if __name__ == "__main__":
    port = int(os.getenv("OAUTH_PORT", "5001"))  # Use 5001 as default
    print(f"Starting OAuth callback server on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
