# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Python bot that integrates with Zulip Server to facilitate foosball matchmaking through a queue system with match acceptance. Users can join a queue, and when 2 players are available, they both receive match proposals. Both players must accept within 2 minutes to confirm the match.

## Running the Bot

### Setup
1. Copy `.env.example` to `.env` and configure with your Zulip bot credentials
2. Install dependencies: `pip install -r requirements.txt`
3. Run the bot: `python main.py`

### Configuration
Environment variables required in `.env`:
- `ZULIP_EMAIL`: Bot's email address on Zulip server
- `ZULIP_API_KEY`: Bot's API key from Zulip
- `ZULIP_SITE`: Full URL to your Zulip server

## Architecture

### Message Flow
1. `main.py` initializes `Config` and `FoosballBot`, then starts the event loop
2. `bot.py` receives messages via `client.call_on_each_message()` callback
3. Bot responds to private messages or stream messages that mention the bot
4. Commands are dispatched to handlers via the `commands` dictionary (bot.py:16-23)
5. `QueueManager` maintains in-memory queue state, pending matches, and handles matchmaking logic
6. Background thread in `bot.py` checks for expired matches every 10 seconds

### Core Components

**bot.py** (`FoosballBot` class)
- Handles message routing and command dispatch
- Manages Zulip client connection and message sending
- Implements six commands: `/queue`, `/unqueue`, `/accept`, `/decline`, `/status`, `/help`
- Sends private message notifications for match proposals, confirmations, and declines
- Runs background thread to check for expired matches (2-minute timeout)

**queue_manager.py** (`QueueManager` class)
- In-memory list-based queue and pending matches dictionary (bot.py:11)
- `add_user()` prevents duplicate queuing and checks for pending matches
- `check_for_match()` creates pending match when 2 users are available
- `accept_match()` tracks individual acceptances; match confirmed only when both accept
- `decline_match()` returns declined partner to front of queue
- `cleanup_expired_matches()` removes matches after 120 seconds
- State is lost on bot restart (no persistence)

**config.py** (`Config` class)
- Loads environment variables with validation
- Provides message templates via `messages` property
- Returns Zulip client configuration dict

### Key Implementation Details
- Bot listens to ALL messages but only processes private messages or stream messages where bot is mentioned (bot.py:54)
- Match proposal triggers when 2nd user queues (bot.py:56-64)
  - First user receives match proposal notification
  - Second user is notified that proposal was sent
- Both users must `/accept` within 2 minutes to confirm match (bot.py:113-134)
- Either user can `/decline`, which returns partner to front of queue (bot.py:136-145)
- Matches expire after 2 minutes; both users are notified and removed (bot.py:38-51)
- Any unrecognized message triggers help response (bot.py:66-69)

## Testing Commands
Since this bot has no automated tests, manual testing is done by:
1. Running the bot with `python main.py`
2. Sending commands via Zulip interface (private message or @mention in stream)
3. Checking bot logs in console output
4. Verifying message responses in Zulip

## State Management
The queue and pending matches are completely in-memory with no persistence. Restarting the bot clears all queued users and pending matches.

## Match Acceptance Flow
1. User A joins queue with `/queue`
2. User B joins queue with `/queue`
3. User A receives match proposal with User B's name
4. User B is notified that proposal was sent to User A
5. Both users have 2 minutes to `/accept` or `/decline`
6. If both accept: match is confirmed, both receive confirmation message
7. If one accepts: they receive waiting message until partner accepts or timeout
8. If one declines: match is cancelled, partner returns to front of queue
9. If 2 minutes pass: both users are notified of expiration and removed from queue
