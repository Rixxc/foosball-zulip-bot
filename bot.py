import logging
import zulip
import threading
import time
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
            '/help': self._handle_help_command,
            '/accept': self._handle_accept_command,
            '/decline': self._handle_decline_command
        }

        # Start timeout checker thread
        self._running = True
        self._timeout_thread = threading.Thread(target=self._check_expired_matches, daemon=True)
        self._timeout_thread.start()

    def run(self):
        self.logger.info("Bot is running and listening for messages...")
        self.client.call_on_each_message(self._handle_message)

    def stop(self):
        """Stop the bot and cleanup threads."""
        self._running = False

    def _check_expired_matches(self):
        """Background thread that checks for expired matches every 10 seconds."""
        while self._running:
            time.sleep(10)  # Check every 10 seconds
            expired_users = self.queue_manager.cleanup_expired_matches(timeout_seconds=120)

            for user_id in expired_users:
                # Get match info before it's removed
                match_info = self.queue_manager.get_pending_match(user_id)
                if match_info:
                    partner_name = match_info['partner_name']
                    # Notify user their match expired
                    expired_msg = self.config.messages['match_expired'].format(partner_name)
                    self._send_private_message(user_id, expired_msg)
    
    def _handle_message(self, msg):
        # Ignore messages from the bot itself
        if msg['sender_email'] == self.config.zulip_email:
            return

        if msg['type'] == 'private' or (msg['type'] == 'stream' and self._is_bot_mentioned(msg)):
            content = msg['content'].strip()
            sender_id = str(msg['sender_id'])
            sender_name = msg['sender_full_name']

            self.logger.info(f"Received message from {sender_name}: {content}")

            command = content.split()[0].lower() if content else ""

            if command in self.commands:
                response = self.commands[command](sender_id, sender_name)
                self._send_response(msg, response)
            else:
                # Send help for any unrecognized message
                response = self.config.messages['help']
                self._send_response(msg, response)
    
    def _is_bot_mentioned(self, msg):
        bot_email = self.config.zulip_email
        return f"@**{bot_email}**" in msg['content'] or f"@{bot_email}" in msg['content']
    
    def _handle_queue_command(self, user_id: str, user_name: str) -> str:
        # Check if user has pending match
        if self.queue_manager.has_pending_match(user_id):
            return self.config.messages['has_pending_match']

        if not self.queue_manager.add_user(user_id, user_name):
            return self.config.messages['already_queued']

        match = self.queue_manager.check_for_match()
        if match:
            user1, user2 = match
            # Send match proposal to user1 (first in queue)
            proposal_msg = self.config.messages['match_proposal'].format(user2['user_name'])
            self._send_private_message(user1['user_id'], proposal_msg)

            # Let user2 (who just queued) know a proposal was sent
            return self.config.messages['match_proposal_sent'].format(user1['user_name'])
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

    def _handle_accept_command(self, user_id: str, user_name: str) -> str:
        match_info = self.queue_manager.accept_match(user_id)

        if match_info is None:
            pending = self.queue_manager.get_pending_match(user_id)
            if pending:
                return self.config.messages['partner_already_responded']
            return self.config.messages['no_pending_match']

        partner_id = match_info['partner_id']
        partner_name = match_info['partner_name']
        both_accepted = match_info['both_accepted']

        if both_accepted:
            # Both users have accepted - confirm the match
            confirmed_msg = self.config.messages['match_confirmed'].format(user_name, partner_name)
            self._send_private_message(user_id, confirmed_msg)
            self._send_private_message(partner_id, confirmed_msg)
            return ""
        else:
            # This user accepted, but waiting for partner
            return self.config.messages['match_accepted_waiting'].format(partner_name)

    def _handle_decline_command(self, user_id: str, user_name: str) -> str:
        partner_id = self.queue_manager.decline_match(user_id)

        if partner_id is None:
            return self.config.messages['no_pending_match']

        # Get partner info from pending match before it's removed
        pending = self.queue_manager.get_pending_match(partner_id)
        partner_name = pending['partner_name'] if pending else "the other player"

        # Notify partner that match was declined
        decline_msg = self.config.messages['match_declined_by_partner'].format(user_name)
        self._send_private_message(partner_id, decline_msg)

        return self.config.messages['match_declined_by_you'].format(partner_name)

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

    def _send_private_message(self, user_id: str, message: str):
        """Send a private message to a specific user."""
        request = {
            'type': 'private',
            'to': [int(user_id)],
            'content': message
        }
        result = self.client.send_message(request)
        if result['result'] != 'success':
            self.logger.error(f"Failed to send private message to {user_id}: {result}")