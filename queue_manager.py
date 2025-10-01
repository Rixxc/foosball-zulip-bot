import logging
from typing import List, Optional, Tuple

class QueueManager:
    def __init__(self):
        self.queue = []
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
            self.logger.info(f"Match found: {user1['user_name']} vs {user2['user_name']}")
            return user1, user2
        return None
    
    def get_queue_status(self) -> List[dict]:
        return self.queue.copy()
    
    def clear_queue(self):
        self.queue.clear()
        self.logger.info("Queue cleared")