#!/usr/bin/env python3
"""
Russ - The Chip Warden Agent

Watches for new G-code files, manages versions, and keeps your shop organized.
Named after Russ, the lead machinist who never scrapped a part.
"""

import os
import sys
import time
import yaml
import asyncio
import logging
from pathlib import Path
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from gcode_parser import GCodeParser, GCodeMetadata
from file_manager import FileManager
from telegram_bot import TelegramNotifier, load_telegram_token, TELEGRAM_AVAILABLE


class GCodeFileHandler(FileSystemEventHandler):
    """Handles new G-code files posted by Fusion 360"""

    def __init__(
        self,
        parser: GCodeParser,
        file_manager: FileManager,
        telegram: Optional[TelegramNotifier],
        config: dict
    ):
        self.parser = parser
        self.file_manager = file_manager
        self.telegram = telegram
        self.config = config
        self.logger = logging.getLogger('russ')

        # Track processed files to avoid duplicates
        self.processed_files = set()

    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return

        # Only process .nc and .gcode files
        file_path = Path(event.src_path)
        if file_path.suffix.lower() not in ['.nc', '.gcode']:
            return

        # Avoid processing the same file multiple times
        if file_path in self.processed_files:
            return

        # Wait a moment for file to finish writing
        time.sleep(0.5)

        self.logger.info(f"📥 New file detected: {file_path.name}")
        self.process_file(file_path)

    def process_file(self, file_path: Path):
        """Process a new G-code file"""
        try:
            # Mark as processed
            self.processed_files.add(file_path)

            # Parse metadata
            self.logger.info(f"🔍 Parsing metadata from {file_path.name}")
            metadata = self.parser.parse_file(str(file_path))

            if not metadata:
                self.logger.warning(f"⚠️ No Chip Warden metadata found in {file_path.name}")
                self.logger.warning("   File not processed. Is the post processor modified?")
                return

            self.logger.info(f"✅ Parsed: {metadata.project} / {metadata.part}")
            self.logger.info(f"   Setup: {metadata.setup}")
            self.logger.info(f"   Machine: {metadata.machine}")
            self.logger.info(f"   Tools: {metadata.tool_count}, Operations: {metadata.operations}")

            # Check for changes compared to previous version
            warnings = []
            existing_versions = self.file_manager.get_existing_versions(
                metadata.project,
                metadata.part
            )

            if existing_versions:
                # Parse previous version for comparison
                prev_metadata = self.parser.parse_file(str(existing_versions[0]))
                if prev_metadata:
                    changes = self.parser.compare_metadata(prev_metadata, metadata)
                    if changes['warnings']:
                        warnings.extend(changes['warnings'])
                        for warning in changes['warnings']:
                            self.logger.warning(f"   {warning}")

            # Archive to git
            self.logger.info(f"📦 Archiving to parts repository...")
            archived_path, version = self.file_manager.archive_gcode(
                str(file_path),
                metadata,
                commit=self.config.get('git', {}).get('auto_commit', True)
            )

            # Copy to FTP directory
            self.logger.info(f"📤 Copying to FTP directory...")
            ftp_path = self.file_manager.copy_to_ftp(
                archived_path,
                metadata,
                version
            )

            # Clean up old FTP files
            keep_count = self.config.get('file_management', {}).get('keep_versions_in_ftp', 2)
            self.file_manager.cleanup_old_ftp_files(keep_count=keep_count)

            # Send Telegram notification
            if self.telegram and self.config.get('telegram', {}).get('notify_on_post', True):
                self.logger.info(f"📱 Sending Telegram notification...")
                asyncio.run(self.telegram.notify_new_file(
                    project=metadata.project,
                    part=metadata.part,
                    version=version,
                    setup=metadata.setup,
                    machine=metadata.machine,
                    tools=metadata.tool_count,
                    warnings=warnings
                ))

            # Delete original file from fusion output directory
            file_path.unlink()
            self.logger.info(f"✅ Processed and removed original file")

            self.logger.info(f"🎉 {metadata.part} v{version} ready on FTP!")

        except Exception as e:
            self.logger.error(f"❌ Error processing {file_path.name}: {e}", exc_info=True)
            if self.telegram:
                asyncio.run(self.telegram.notify_error(f"Error processing {file_path.name}: {e}"))


class Russ:
    """Main Chip Warden agent"""

    def __init__(self, config_path: str = "russ/config/config.yml"):
        """
        Initialize Russ

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self.load_config()
        self.setup_logging()
        self.logger = logging.getLogger('russ')

        # Initialize components
        self.parser = GCodeParser()
        self.file_manager = FileManager(
            self.config['directories']['parts_archive'],
            self.config['directories']['ftp_share']
        )

        # Initialize Telegram if configured
        self.telegram = None
        if TELEGRAM_AVAILABLE and self.config.get('telegram', {}).get('enabled', False):
            token = load_telegram_token(self.config['directories'].get('config', 'russ/config'))
            chat_id = self.config.get('telegram', {}).get('chat_id')

            if token and chat_id:
                try:
                    self.telegram = TelegramNotifier(token, str(chat_id))
                    self.logger.info("✅ Telegram notifications enabled")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to initialize Telegram: {e}")
            else:
                self.logger.warning("⚠️ Telegram enabled but token/chat_id not configured")

        # File watcher
        self.observer = None
        self.handler = None

    def load_config(self) -> dict:
        """Load configuration from YAML file"""
        config_path = Path(self.config_path)

        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            print(f"   Copy config.example.yml to config.yml and customize")
            sys.exit(1)

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        log_level = log_config.get('level', 'INFO')
        log_dir = Path(self.config['directories'].get('logs', 'russ/logs'))
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'russ.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def start(self):
        """Start watching for files"""
        self.logger.info("🤖 Russ (Chip Warden) starting...")
        self.logger.info(f"   Watching: {self.config['directories']['fusion_output']}")
        self.logger.info(f"   Archive: {self.config['directories']['parts_archive']}")
        self.logger.info(f"   FTP: {self.config['directories']['ftp_share']}")

        # Create watched directory if it doesn't exist
        watch_dir = Path(self.config['directories']['fusion_output'])
        watch_dir.mkdir(parents=True, exist_ok=True)

        # Setup file watcher
        self.handler = GCodeFileHandler(
            self.parser,
            self.file_manager,
            self.telegram,
            self.config
        )

        self.observer = Observer()
        self.observer.schedule(
            self.handler,
            str(watch_dir),
            recursive=False
        )

        self.observer.start()
        self.logger.info("✅ Russ is running. Watching for new G-code files...")
        self.logger.info("   Press Ctrl+C to stop")

        # Send startup notification
        if self.telegram and self.config.get('telegram', {}).get('enabled'):
            try:
                asyncio.run(self.telegram.send_message(
                    "🤖 *Russ is online*\n\n"
                    "Chip Warden started - watching for new programs.\n\n"
                    "_In Russ we trust._"
                ))
            except Exception as e:
                self.logger.warning(f"⚠️ Could not send startup notification: {e}")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("⏹️  Stopping Russ...")
            self.observer.stop()

        self.observer.join()
        self.logger.info("👋 Russ stopped")

    def process_existing_files(self):
        """Process any existing files in the fusion output directory"""
        watch_dir = Path(self.config['directories']['fusion_output'])
        nc_files = list(watch_dir.glob("*.nc")) + list(watch_dir.glob("*.gcode"))

        if nc_files:
            self.logger.info(f"📂 Found {len(nc_files)} existing files to process")
            for nc_file in nc_files:
                self.handler.process_file(nc_file)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Russ - The Chip Warden Agent"
    )
    parser.add_argument(
        '--config',
        default='russ/config/config.yml',
        help='Path to config file'
    )
    parser.add_argument(
        '--process-existing',
        action='store_true',
        help='Process existing files in fusion output directory before watching'
    )

    args = parser.parse_args()

    # Create and start Russ
    russ = Russ(config_path=args.config)

    if args.process_existing:
        russ.process_existing_files()

    russ.start()


if __name__ == "__main__":
    main()
