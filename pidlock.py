#!/usr/bin/env python3
"""
PID lock management for ensuring single instance execution.
"""

import os
import psutil
import signal
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class PidLock:
    """Manages PID lock file to prevent multiple instances."""

    def __init__(self, lock_file: str = "gti-listings.pid"):
        """Initialize PID lock manager.

        Args:
            lock_file: Path to the PID lock file
        """
        self.lock_file = Path(lock_file)
        self.current_pid = os.getpid()
        self._cleanup_registered = False

    def acquire(self) -> bool:
        """
        Acquire the PID lock, checking for existing instances.

        Returns:
            True if lock acquired successfully, False if another instance exists
        """
        if self.lock_file.exists():
            existing_pid = self._read_existing_pid()
            if existing_pid:
                if self._is_our_process_running(existing_pid):
                    logger.info(f"🔒 GTI Listings is already running (PID {existing_pid}). Current process PID: {self.current_pid}. Exiting.")
                    return False
                elif self._is_process_running(existing_pid):
                    logger.warning(f"⚠️ PID {existing_pid} exists but doesn't appear to be GTI Listings")
                    logger.warning("🚨 ANOTHER PROCESS IS USING OUR PID FILE - ABORTING FOR SAFETY")
                    return False
                else:
                    logger.info(f"🧹 Stale PID file found (PID {existing_pid} not running), cleaning up")
                    self._remove_lock_file()

        # Create new lock file
        return self._create_lock_file()

    def release(self):
        """Release the PID lock by removing the lock file."""
        if self.lock_file.exists():
            try:
                # Verify this is our lock file before removing
                existing_pid = self._read_existing_pid()
                if existing_pid == self.current_pid:
                    self._remove_lock_file()
                    logger.info(f"🔓 Released PID lock (PID {self.current_pid})")
                else:
                    logger.warning(f"⚠️ Lock file PID mismatch: expected {self.current_pid}, found {existing_pid}")
            except Exception as e:
                logger.error(f"Error releasing PID lock: {e}")

    def register_cleanup(self):
        """Register signal handlers for automatic cleanup."""
        if self._cleanup_registered:
            return

        def cleanup_handler(signum, frame):
            print(f"Received signal {signum}, cleaning up...")
            logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
            self.release()
            logger.info("👋 GTI Listings shutdown complete")
            exit(0)

        # Register signal handlers
        signal.signal(signal.SIGINT, cleanup_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, cleanup_handler)  # Termination signal

        # Also register atexit for normal shutdown
        import atexit
        atexit.register(self.release)

        self._cleanup_registered = True
        logger.debug("🛡️ Signal handlers and cleanup registered")

    def _read_existing_pid(self) -> Optional[int]:
        """Read PID from existing lock file."""
        try:
            with open(self.lock_file, 'r') as f:
                return int(f.read().strip())
        except (ValueError, FileNotFoundError, PermissionError) as e:
            logger.debug(f"Could not read PID from lock file: {e}")
            return None

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running."""
        try:
            return psutil.pid_exists(pid)
        except Exception as e:
            logger.debug(f"Error checking if PID {pid} exists: {e}")
            return False

    def _is_our_process_running(self, pid: int) -> bool:
        """Check if the process looks like our GTI Listings app."""
        try:
            if not psutil.pid_exists(pid):
                return False

            process = psutil.Process(pid)
            cmdline = process.cmdline()

            # Check if command line contains our app indicators
            cmdline_str = ' '.join(cmdline).lower()
            our_indicators = ['app.py', 'gti-listings', 'flask']

            return any(indicator in cmdline_str for indicator in our_indicators)

        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
            logger.debug(f"Error checking process {pid}: {e}")
            return False

    def _create_lock_file(self) -> bool:
        """Create the PID lock file."""
        try:
            with open(self.lock_file, 'w') as f:
                f.write(str(self.current_pid))
            logger.debug(f"🔒 Created PID lock file with PID {self.current_pid}")
            return True
        except Exception as e:
            logger.error(f"Failed to create PID lock file: {e}")
            return False

    def _remove_lock_file(self):
        """Remove the PID lock file."""
        try:
            self.lock_file.unlink()
            logger.debug(f"🗑️ Removed PID lock file")
        except FileNotFoundError:
            pass  # Already gone
        except Exception as e:
            logger.error(f"Error removing PID lock file: {e}")
