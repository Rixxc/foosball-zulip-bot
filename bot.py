import logging
import zulip
from queue_manager import QueueManager
from config import Config

class FoosballBot:
    def __init__(self, config: Config):
        self.config = config
        self.queue_manager = QueueManager()
        self.logger = logging.getLogger(__name__)
        
        self.client = zulip.Client(**config.get_zulip_config())
        
        self.commands = {
            '/queue': self._handle_queue_command,
            '/unqueue': self._handle_unqueue_command,
            '/status': self._handle_status_command,
            '/help': self._handle_help_command
        }
    
    def run(self):
        self.logger.info("Bot is running and listening for messages...")
        self.client.call_on_each_message(self._handle_message)
    
    def _handle_message(self, msg):
        if msg['type'] == 'private' or (msg['type'] == 'stream' and self._is_bot_mentioned(msg)):
            content = msg['content'].strip()
            sender_id = str(msg['sender_id'])
            sender_name = msg['sender_full_name']
            
            self.logger.info(f"Received message from {sender_name}: {content}")
            
            command = content.split()[0].lower() if content else ""
            
            if command in self.commands:
                response = self.commands[command](sender_id, sender_name)
                self._send_response(msg, response)
            elif content.startswith('/'):
                response = self.config.messages['invalid_command']
                self._send_response(msg, response)
    
    def _is_bot_mentioned(self, msg):
        bot_email = self.config.zulip_email
        return f"@**{bot_email}**" in msg['content'] or f"@{bot_email}" in msg['content']
    
    def _handle_queue_command(self, user_id: str, user_name: str) -> str:
        if not self.queue_manager.add_user(user_id, user_name):
            return self.config.messages['already_queued']
        
        match = self.queue_manager.check_for_match()
        if match:
            user1, user2 = match
            match_message = self.config.messages['match_found'].format(
                user1['user_name'], user2['user_name']
            )
            self._notify_users([user1, user2], match_message)
            return ""  # Don't send response since both users already notified privately
        else:
            return self.config.messages['queued']
    
    def _handle_unqueue_command(self, user_id: str, user_name: str) -> str:
        if self.queue_manager.remove_user(user_id):
            return self.config.messages['unqueued']
        else:
            return self.config.messages['not_in_queue']
    
    def _handle_status_command(self, user_id: str, user_name: str) -> str:
        queue_size = self.queue_manager.get_queue_size()

        if queue_size == 0:
            return self.config.messages['queue_status_empty']
        elif queue_size == 1:
            return self.config.messages['queue_status_single']
        else:
            return self.config.messages['queue_status_multiple'].format(queue_size)

    def _handle_help_command(self, user_id: str, user_name: str) -> str:
        return self.config.messages['help']

    def _send_response(self, original_msg, response: str):
        if original_msg['type'] == 'private':
            request = {
                'type': 'private',
                'to': [original_msg['sender_id']],
                'content': response
            }
        else:
            request = {
                'type': 'stream',
                'to': original_msg['display_recipient'],
                'subject': original_msg['subject'],
                'content': response
            }
        
        result = self.client.send_message(request)
        if result['result'] != 'success':
            self.logger.error(f"Failed to send message: {result}")
    
    def _notify_users(self, users: list, message: str):
        for user in users:
            request = {
                'type': 'private',
                'to': [int(user['user_id'])],
                'content': message
            }
            result = self.client.send_message(request)
            if result['result'] != 'success':
                self.logger.error(f"Failed to notify user {user['user_name']}: {result}")