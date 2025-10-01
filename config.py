import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
        self.zulip_email = os.getenv('ZULIP_EMAIL')
        self.zulip_api_key = os.getenv('ZULIP_API_KEY') 
        self.zulip_site = os.getenv('ZULIP_SITE')
        
        self._validate_config()
    
    def _validate_config(self):
        required_vars = ['ZULIP_EMAIL', 'ZULIP_API_KEY', 'ZULIP_SITE']
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def get_zulip_config(self):
        return {
            'email': self.zulip_email,
            'api_key': self.zulip_api_key,
            'site': self.zulip_site
        }
    
    @property
    def messages(self):
        return {
            'queued': "You've been added to the foosball queue! 🏓",
            'already_queued': "You're already in the queue! Use /unqueue to leave.",
            'unqueued': "You've been removed from the foosball queue.",
            'not_in_queue': "You're not currently in the queue.",
            'match_found': "🎉 Match found! {} and {} - time to play foosball!",
            'invalid_command': "Invalid command. Use /queue to join or /unqueue to leave.",
            'queue_status_empty': "The foosball queue is currently empty.",
            'queue_status_single': "There is 1 player in the foosball queue.",
            'queue_status_multiple': "There are {} players in the foosball queue.",
            'help': """**Foosball Bot** 🏓

I help you find foosball opponents! Join the queue and get automatically matched with another player.

**Commands:**
• `/queue` - Join the foosball queue
• `/unqueue` - Leave the foosball queue
• `/status` - Check how many players are in the queue
• `/help` - Show this help message

When 2 players are in the queue, you'll be automatically matched and notified via private message!"""
        }