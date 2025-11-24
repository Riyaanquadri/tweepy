import signal
import threading
from .scheduler import BotScheduler
from .logger import logger
from .config import Config
from app.src.db import init_db
from .rate_limit import signal_shutdown

stop_event = threading.Event()


def main():
    # Ensure the lite audit DB used by helper utilities is initialized.
    init_db()
    # Validate configuration before startup
    if not Config.validate():
        logger.error('Configuration validation failed. Please check your .env file or secret store.')
        exit(1)
    
    logger.info('Starting Crypto AI Twitter Bot')
    logger.info(f'Bot handle: {Config.BOT_HANDLE}')
    logger.info(f'Project keywords: {Config.PROJECT_KEYWORDS}')
    logger.info(f'DRY_RUN mode: {Config.DRY_RUN}')
    
    sched = BotScheduler()
    sched.start()

    def _stop(signum=None, frame=None):
        logger.info('Shutting down...')
        signal_shutdown()  # Wake up any rate limit sleeps
        stop_event.set()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    # Wait until stop_event is set (Ctrl+C or external signal)
    # Use a timeout to make the wait loop responsive to signals
    try:
        while not stop_event.is_set():
            stop_event.wait(timeout=0.5)  # Check every 0.5 seconds
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received')
        signal_shutdown()
    finally:
        sched.shutdown()

if __name__ == '__main__':
    main()
