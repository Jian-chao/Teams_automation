"""
Teams Push Job Message Forwarder

Main entry point for the application.
Monitors Teams chats for push job requests and forwards them to a designated group.
"""
import asyncio
import sys
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import load_config
from .graph_client import create_graph_client
from .chat_fetcher import ChatFetcher
from .message_monitor import MessageMonitor
from .message_detector import RegexMessageDetector
from .duplicate_checker import DuplicateChecker
from .forwarder import forward_message, add_reaction_to_message
from .persistence import PollStatePersistence, ForwardedHistoryPersistence


async def check_and_forward(
    config: dict,
    graph_client,
    detector,
    checker: DuplicateChecker,
    poll_persistence: PollStatePersistence,
    forwarded_persistence: ForwardedHistoryPersistence
) -> None:
    """
    Main check and forward logic.
    
    1. Fetches all user chats
    2. Gets new messages based on chat type
    3. Detects push job requests
    4. Checks for duplicates
    5. Forwards non-duplicate requests
    """
    print(f"[{datetime.now().isoformat()}] Starting check cycle...")
    
    try:
        # Get all chats dynamically
        fetcher = ChatFetcher(graph_client)
        all_chats = await fetcher.get_all_chats()
        print(f"  Found {len(all_chats)} chats")
        
        # Initialize monitor
        monitor = MessageMonitor(
            graph_client,
            config["my_display_name"],
            poll_persistence
        )
        
        forwarded_count = 0
        
        for chat in all_chats:
            # Skip the target push job group itself
            if chat.chat_id == config["target_push_chat_id"]:
                continue
            
            # Get new messages from this chat
            new_messages = await monitor.get_new_messages(
                chat, 
                include_self=config.get("include_self", False)
            )
            
            for chat_id, msg in new_messages:
                # Get message content
                content = msg.body.content if msg.body else ""
                attachments = msg.attachments or []
                
                # Detect if this is a push request
                result = detector.detect(content, attachments)
                
                if result.is_push_request:
                    print(f"  Found push request: {result.job_id or 'unknown job'}")
                    
                    # Check for duplicates
                    is_dup = await checker.is_duplicate(msg.id, result.job_id)
                    
                    if not is_dup:
                        # Forward the message
                        try:
                            forwarded_id = await forward_message(
                                graph_client,
                                source_chat_id=chat_id,
                                message_id=msg.id,dk3d
                                target_chat_id=config["target_push_chat_id"]
                            )
                            
                            # Mark as forwarded
                            forwarded_persistence.mark_forwarded(
                                msg.id,
                                result.job_id,
                                forwarded_id
                            )
                            
                            forwarded_count += 1
                            print(f"  ✓ Forwarded message {msg.id} (Job: {result.job_id})")
                            
                            # Add reaction if configured
                            if config.get("add_reaction_after_forward", False):
                                try:
                                    success = await add_reaction_to_message(
                                        graph_client,
                                        chat_id,
                                        msg.id
                                    )
                                    if success:
                                        print(f"  ✓ Added reaction to original message")
                                except Exception as e:
                                    print(f"  ⚠ Failed to add reaction: {e}")
                            
                        except Exception as e:
                            print(f"  ✗ Failed to forward: {e}")
                    else:
                        print(f"  - Skipped (duplicate): {result.job_id}")
        
        print(f"  Cycle complete. Forwarded {forwarded_count} messages.")
        
    except Exception as e:
        print(f"  Error during check cycle: {e}")


def main():
    """
    Application entry point.
    
    Initializes components and starts the scheduler.
    """
    print("=" * 50)
    print("Teams Push Job Message Forwarder")
    print("=" * 50)
    
    # Load configuration
    try:
        config = load_config("config.json")
        print(f"✓ Configuration loaded")
        print(f"  - Target chat: {config['target_push_chat_id']}")
        print(f"  - Poll interval: {config['poll_interval_seconds']} seconds")
        print(f"  - User: {config['my_display_name']}")
        print(f"  - Patterns: {len(config['patterns'])} configured")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Create Graph client (will prompt for login if needed)
    try:
        print("\nInitializing MS Graph client...")
        print("  (Browser may open for authentication)")
        graph_client = create_graph_client(config)
        print("✓ Graph client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize Graph client: {e}")
        sys.exit(1)
    
    # Initialize components
    detector = RegexMessageDetector(config["patterns"])
    poll_persistence = PollStatePersistence()
    forwarded_persistence = ForwardedHistoryPersistence()
    checker = DuplicateChecker(
        graph_client,
        config["target_push_chat_id"],
        forwarded_persistence
    )
    
    print("✓ Components initialized")
    
    # Set up scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_and_forward,
        'interval',
        seconds=config["poll_interval_seconds"],
        args=[
            config,
            graph_client,
            detector,
            checker,
            poll_persistence,
            forwarded_persistence
        ],
        next_run_time=datetime.now()  # Run immediately on start
    )
    
    # Start scheduler
    scheduler.start()
    print(f"\n✓ Scheduler started (every {config['poll_interval_seconds']} seconds)")
    print("  Press Ctrl+C to stop\n")
    
    # Run event loop
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        scheduler.shutdown()
        print("Goodbye!")


if __name__ == "__main__":
    main()
