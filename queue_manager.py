import logging
import time
from typing import List, Optional, Tuple, Dict

class QueueManager:
    def __init__(self):
        self.queue = []
        self.pending_matches = {}  # user_id -> {'match_id': str, 'partner_id': str, 'partner_name': str, 'timestamp': float}
        self.logger = logging.getLogger(__name__)
    
    def add_user(self, user_id: str, user_name: str) -> bool:
        if self.is_user_in_queue(user_id):
            return False
        
        self.queue.append({'user_id': user_id, 'user_name': user_name})
        self.logger.info(f"Added user {user_name} ({user_id}) to queue")
        return True
    
    def remove_user(self, user_id: str) -> bool:
        for i, user in enumerate(self.queue):
            if user['user_id'] == user_id:
                removed_user = self.queue.pop(i)
                self.logger.info(f"Removed user {removed_user['user_name']} ({user_id}) from queue")
                return True
        return False
    
    def is_user_in_queue(self, user_id: str) -> bool:
        return any(user['user_id'] == user_id for user in self.queue)
    
    def get_queue_size(self) -> int:
        return len(self.queue)
    
    def check_for_match(self) -> Optional[Tuple[dict, dict]]:
        if len(self.queue) >= 2:
            user1 = self.queue.pop(0)
            user2 = self.queue.pop(0)
            self.logger.info(f"Potential match found: {user1['user_name']} vs {user2['user_name']}")

            # Create pending match
            match_id = f"{user1['user_id']}_{user2['user_id']}_{int(time.time())}"
            timestamp = time.time()

            self.pending_matches[user1['user_id']] = {
                'match_id': match_id,
                'partner_id': user2['user_id'],
                'partner_name': user2['user_name'],
                'timestamp': timestamp,
                'initiator': False,
                'accepted': False
            }
            self.pending_matches[user2['user_id']] = {
                'match_id': match_id,
                'partner_id': user1['user_id'],
                'partner_name': user1['user_name'],
                'timestamp': timestamp,
                'initiator': True,
                'accepted': False
            }

            return user1, user2
        return None

    def accept_match(self, user_id: str) -> Optional[Dict]:
        """Accept a pending match. Returns match info with 'both_accepted' flag."""
        if user_id not in self.pending_matches:
            return None

        match_info = self.pending_matches[user_id]
        partner_id = match_info['partner_id']

        # Check if partner still has pending match
        if partner_id not in self.pending_matches:
            # Partner already declined or timed out
            del self.pending_matches[user_id]
            return None

        # Mark this user as accepted
        self.pending_matches[user_id]['accepted'] = True

        # Check if partner has also accepted
        partner_info = self.pending_matches[partner_id]
        both_accepted = partner_info['accepted']

        if both_accepted:
            # Both have accepted, remove from pending and confirm match
            del self.pending_matches[user_id]
            del self.pending_matches[partner_id]
            self.logger.info(f"Match confirmed between {user_id} and {partner_id}")
        else:
            self.logger.info(f"{user_id} accepted match, waiting for {partner_id}")

        return {
            'user_id': user_id,
            'partner_id': partner_id,
            'partner_name': match_info['partner_name'],
            'both_accepted': both_accepted
        }

    def decline_match(self, user_id: str) -> Optional[str]:
        """Decline a pending match. Returns partner_id if successful."""
        if user_id not in self.pending_matches:
            return None

        match_info = self.pending_matches[user_id]
        partner_id = match_info['partner_id']

        # Remove both from pending matches and return partner to queue
        del self.pending_matches[user_id]
        if partner_id in self.pending_matches:
            partner_name = self.pending_matches[partner_id]['partner_name']
            del self.pending_matches[partner_id]
            # Return partner to front of queue
            self.queue.insert(0, {'user_id': partner_id, 'user_name': partner_name})

        self.logger.info(f"Match declined by {user_id}")
        return partner_id

    def has_pending_match(self, user_id: str) -> bool:
        """Check if user has a pending match."""
        return user_id in self.pending_matches

    def get_pending_match(self, user_id: str) -> Optional[Dict]:
        """Get pending match info for user."""
        return self.pending_matches.get(user_id)

    def cleanup_expired_matches(self, timeout_seconds: int = 120) -> List[str]:
        """Remove matches that have expired. Returns list of expired user_ids."""
        current_time = time.time()
        expired_users = []

        for user_id, match_info in list(self.pending_matches.items()):
            if current_time - match_info['timestamp'] > timeout_seconds:
                expired_users.append(user_id)

        # Remove expired matches
        for user_id in expired_users:
            if user_id in self.pending_matches:
                del self.pending_matches[user_id]

        if expired_users:
            self.logger.info(f"Expired matches for users: {expired_users}")

        return expired_users
    
    def get_queue_status(self) -> List[dict]:
        return self.queue.copy()
    
    def clear_queue(self):
        self.queue.clear()
        self.logger.info("Queue cleared")