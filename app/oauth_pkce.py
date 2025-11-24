"""
Generate a PKCE code_verifier / code_challenge and print the Authorization URL.
Run this, copy the printed URL into your browser, login as the bot account and accept.
You will be redirected to your redirect_uri with ?code=... which the callback server captures.
"""
import base64
import hashlib
import os
import secrets
import urllib.parse
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

CLIENT_ID = os.getenv("TW_CLIENT_ID")  # add to .env
REDIRECT_URI = os.getenv("TW_REDIRECT_URI", "http://127.0.0.1:5000/callback")
SCOPES = "tweet.read tweet.write users.read offline.access"

def generate_pkce_pair():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("utf-8")
    # compute challenge
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("utf-8")
    return verifier, challenge

if __name__ == "__main__":
    verifier, challenge = generate_pkce_pair()
    # store the verifier locally for later exchange
    print("PKCE code_verifier (save this securely):\n", verifier)
    state = secrets.token_urlsafe(16)
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        # optionally set "prompt" or other params if needed
    }
    url = "https://twitter.com/i/oauth2/authorize?" + urllib.parse.urlencode(params)
    print("\nOpen this URL in your browser (login as the bot account):\n")
    print(url)
    print("\nNOTE: copy the code_verifier above (you will use it in the token exchange).")
