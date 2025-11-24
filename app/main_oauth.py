"""
Twitter bot with OAuth2 user context authentication.

This version uses OAuth2 bearer token for authentication via direct HTTP requests
instead of Tweepy's OAuth1 client (Tweepy v4 requires consumer key/secret for initialization).
"""
import logging
import signal
import sys
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from app.config import Config
from app.logger import logger
from app.scheduler import BotScheduler
from app.quota import QuotaManager
from app.src.db import init_db

class OAuth2Client:
    """Wrapper for Twitter API v2 using OAuth2 bearer token."""
    
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.headers = {"Authorization": f"Bearer {bearer_token}"}
        self.base_url = "https://api.twitter.com/2"
    
    def get_me(self):
        """Get authenticated user info."""
        response = requests.get(f"{self.base_url}/users/me", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_mentions(self, max_results=10, user_id=None):
        """Get mentions for the authenticated user."""
        if not user_id:
            me = self.get_me()
            user_id = me['data']['id']
        
        params = {
            'max_results': max_results,
            'expansions': 'author_id,in_reply_to_user_id',
            'tweet.fields': 'created_at,public_metrics,author_id',
            'user.fields': 'username,public_metrics'
        }
        response = requests.get(
            f"{self.base_url}/users/{user_id}/mentions",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

def signal_handler(sig, frame):
    """Handle graceful shutdown."""
    logger.info('Received shutdown signal, stopping scheduler...')
    sys.exit(0)

def main():
    """Initialize and run the bot with OAuth2 authentication."""
    
    # Initialize database
    init_db()
    
    logger.info('Starting Crypto AI Twitter Bot (OAuth2 mode)')
    logger.info(f'Bot handle: {Config.BOT_HANDLE}')
    logger.info(f'Project keywords: {Config.PROJECT_KEYWORDS}')
    logger.info(f'DRY_RUN mode: {Config.DRY_RUN}')
    
    # Validate OAuth2 credentials
    if not Config.OAUTH2_USER_ACCESS_TOKEN:
        logger.error('OAUTH2_USER_ACCESS_TOKEN not set in .env')
        logger.error('Run: .venv/bin/python3 app/oauth_pkce.py && oauth_callback.py to get tokens')
        sys.exit(1)
    
    # Create OAuth2 client
    try:
        oauth_client = OAuth2Client(Config.OAUTH2_USER_ACCESS_TOKEN)
        me = oauth_client.get_me()
        logger.info(f'✓ OAuth2 authentication successful: @{me["data"]["username"]}')
    except Exception as e:
        logger.error(f'✗ OAuth2 authentication failed: {e}')
        sys.exit(1)
    
    # Initialize quota manager
    quota_manager = QuotaManager()
    
    # Initialize scheduler (still uses Tweepy for now, but with OAuth2 support coming)
    # For now, use the original OAuth1 client if available
    from tweepy import Client
    
    try:
        if Config.X_API_KEY and Config.X_API_SECRET:
            # Fall back to OAuth1 if OAuth2 client doesn't support all endpoints yet
            client = Client(
                bearer_token=Config.X_BEARER_TOKEN,
                consumer_key=Config.X_API_KEY,
                consumer_secret=Config.X_API_SECRET,
                access_token=Config.X_ACCESS_TOKEN,
                access_token_secret=Config.X_ACCESS_SECRET
            )
            logger.info('Using OAuth1 client for scheduler')
        else:
            logger.error('OAuth1 credentials not available, scheduler needs update for OAuth2')
            sys.exit(1)
            
    except Exception as e:
        logger.error(f'Failed to initialize Twitter client: {e}')
        sys.exit(1)
    
    scheduler = BotScheduler(
        twitter_client=client,
        quota_manager=quota_manager
    )
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info('Scheduler started')
        scheduler.start()
        # Keep running
        while True:
            signal.pause()
    except KeyboardInterrupt:
        logger.info('Bot interrupted')
    finally:
        scheduler.shutdown()
        logger.info('Bot stopped')

if __name__ == '__main__':
    main()
