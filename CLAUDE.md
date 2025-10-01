# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Python bot that integrates with Zulip Server to facilitate foosball matchmaking through a queue system. Users can join a queue, and when 2 players are available, they are automatically matched and notified.

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
4. Commands are dispatched to handlers via the `commands` dictionary (bot.py:14-18)
5. `QueueManager` maintains in-memory queue state and handles matchmaking logic

### Core Components

**bot.py** (`FoosballBot` class)
- Handles message routing and command dispatch
- Manages Zulip client connection and message sending
- Implements three commands: `/queue`, `/unqueue`, `/status`
- Sends private message notifications to matched users

**queue_manager.py** (`QueueManager` class)
- Simple in-memory list-based queue (bot.py:9)
- `add_user()` prevents duplicate queuing
- `check_for_match()` automatically dequeues and returns first 2 users when available
- State is lost on bot restart (no persistence)

**config.py** (`Config` class)
- Loads environment variables with validation
- Provides message templates via `messages` property
- Returns Zulip client configuration dict

### Key Implementation Details
- Bot listens to ALL messages but only processes private messages or stream messages where bot is mentioned (bot.py:25)
- Matchmaking triggers immediately when 2nd user queues (bot.py:49-56)
- Both matched users are removed from queue automatically (queue_manager.py:32-36)
- Invalid commands (starting with `/`) receive error message; other text is ignored (bot.py:37-39)

## Testing Commands
Since this bot has no automated tests, manual testing is done by:
1. Running the bot with `python main.py`
2. Sending commands via Zulip interface (private message or @mention in stream)
3. Checking bot logs in console output
4. Verifying message responses in Zulip

## State Management
The queue is completely in-memory with no persistence. Restarting the bot clears all queued users.
