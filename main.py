#!/usr/bin/env python3

import logging
from bot import FoosballBot
from config import Config

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        config = Config()
        bot = FoosballBot(config)
        
        logger.info("Starting Zulip Foosball Matchmaking Bot...")
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}")
        raise

if __name__ == "__main__":
    main()