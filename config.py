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
            'has_pending_match': "You already have a pending match! Use /accept or /decline first.",
            'unqueued': "You've been removed from the foosball queue.",
            'not_in_queue': "You're not currently in the queue.",
            'match_proposal': "🏓 {} wants to play foosball with you!\n\nUse `/accept` to play or `/decline` to pass.\n⏱️ You have 2 minutes to respond.",
            'match_proposal_sent': "Match proposal sent to {}! Waiting for their response...",
            'match_confirmed': "🎉 Match confirmed! {} and {} - time to play foosball!",
            'match_accepted_waiting': "You've accepted the match! Waiting for {} to accept...",
            'match_declined_by_you': "You've declined the match. {} has been returned to the queue.",
            'match_declined_by_partner': "{} declined the match. You've been returned to the queue.",
            'match_expired': "Your match with {} expired after 2 minutes. You've been removed from the queue.",
            'no_pending_match': "You don't have a pending match to accept/decline.",
            'partner_already_responded': "The other player has already declined or the match expired.",
            'queue_status_empty': "The foosball queue is currently empty.",
            'queue_status_single': "There is 1 player in the foosball queue.",
            'queue_status_multiple': "There are {} players in the foosball queue.",
            'help': """**Foosball Bot** 🏓

I help you find foosball opponents! Join the queue and when matched, you can accept or decline.

**Commands:**
• `/queue` - Join the foosball queue
• `/unqueue` - Leave the foosball queue
• `/accept` - Accept a match proposal
• `/decline` - Decline a match proposal
• `/status` - Check how many players are in the queue
• `/help` - Show this help message

When 2 players are in the queue, you'll both receive a match proposal. Both players must accept within 2 minutes to confirm the match!"""
        }