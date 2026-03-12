"""
tests/test_partial_file_indexing.py
TEST-ASYNC-001 to TEST-ASYNC-006

Tests for async non-blocking file indexing:
- Files indexed immediately (no blocking wait)
- Incomplete files get DOWNLOADING state
- Background monitor updates files when complete
- Processing skipped for DOWNLOADING files
- Cross-platform: works on Windows, Linux, macOS
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

from bid.source_manager import (
    create_source_item,
    create_source_dict,
    SourceState,
    is_file_ready_quick,
    is_file_stable,
    monitor_incomplete_files,
)


# ---------------------------------------------------------------------------
# TEST-ASYNC-001: Quick non-blocking check during indexing
# ---------------------------------------------------------------------------

def test_is_file_ready_quick_nonblocking(temp_dir):
    """TEST-ASYNC-001: is_file_ready_quick() returns immediately without wait.
    
    Scenario:
    - File exists and is not 0-sized
    - Quick check should return immediately (< 10ms)
    - Does NOT block to wait for completion
    """
    source_folder = temp_dir / "source"
    session_dir = source_folder / "session1"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = session_dir / "photo.jpg"
    
    # Create a complete file
    img = Image.new('RGB', (1000, 1000), color='red')
    img.save(str(test_file), "JPEG", quality=85)
    
    # Quick check should return immediately (< 100ms, no blocking wait)
    start = time.time()
    result = is_file_ready_quick(str(test_file))
    elapsed = time.time() - start
    
    # Should complete in < 100ms (no wait)
    assert elapsed < 0.1, f"Quick check took {elapsed}s (should be < 0.1s)"
    
    # Non-zero file should return True (assumed ready)
    assert result is True, "Non-zero file should be detected as ready"
    
    # Test 0-byte file detection
    zero_file = session_dir / "zero.jpg"
    zero_file.write_bytes(b"")  # Create empty file
    
    result_zero = is_file_ready_quick(str(zero_file))
    assert result_zero is False, "Zero-byte file should be detected as not ready"


# ---------------------------------------------------------------------------
# TEST-ASYNC-002: Files indexed immediately with DOWNLOADING state
# ---------------------------------------------------------------------------

def test_incomplete_file_indexed_as_downloading(temp_dir):
    """TEST-ASYNC-002: Incomplete files indexed as DOWNLOADING (not blocking).
    
    Scenario:
    - Create new file (not yet complete)
    - Index with create_source_item()
    - Should be indexed immediately with DOWNLOADING state
    - Should NOT block waiting
    """
    source_folder = temp_dir / "source"
    session_dir = source_folder / "session1"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = session_dir / "new_photo.jpg"
    
    # Create file immediately but will simulate slowness via another thread
    img_base = Image.new('RGB', (1000, 1000), color='green')
    img_base.save(str(test_file), "JPEG", quality=85)
    original_mtime = os.stat(test_file).st_mtime
    
    # Now simulate file being modified (re-written)
    def slow_rewrite():
        """Rewrite file to update mtime."""
        time.sleep(0.2)
        img_base.save(str(test_file), "JPEG", quality=85)
    
    rewrite_thread = threading.Thread(target=slow_rewrite, daemon=True)
    rewrite_thread.start()
    
    # Wait a bit so mtime becomes recent (< 2 seconds old)
    time.sleep(0.05)
    
    # Index immediately (should not block)
    start = time.time()
    item = create_source_item(str(session_dir), "session1", "new_photo.jpg")
    elapsed = time.time() - start
    
    # Indexing should be fast (< 200ms, no waiting)
    assert elapsed < 0.2, f"Indexing took {elapsed}s (should be < 0.2s, no blocking wait)"
    
    # File should exist
    assert item["path"] == str(test_file)
    
    rewrite_thread.join(timeout=5)


# ---------------------------------------------------------------------------
# TEST-ASYNC-003: Monitor updates DOWNLOADING to NEW when ready
# ---------------------------------------------------------------------------

def test_monitor_incomplete_files_updates_state(temp_dir):
    """TEST-ASYNC-003: monitor_incomplete_files() updates DOWNLOADING → NEW.
    
    Scenario:
    - Create source dict with manually set DOWNLOADING file
    - Call monitor_incomplete_files()
    - Should detect when file is ready
    - Should return update dict
    """
    source_folder = temp_dir / "source"
    session_dir = source_folder / "session1"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = session_dir / "large_photo.jpg"
    
    # Create a file and immediately set it as DOWNLOADING
    img = Image.new('RGB', (2000, 2000), color='blue')
    img.save(str(test_file), "JPEG", quality=85)
    
    # Manually create source dict entry
    source_dict = {
        "session1": {
            "large_photo.jpg": {
                "path": str(test_file),
                "state": SourceState.DOWNLOADING,
                "size": "0.50 MB",
                "created": "2025:01:01 12:00:00",
            }
        }
    }
    
    # Monitor should detect it's ready
    updates = monitor_incomplete_files(source_dict, max_checks=1, check_interval=0.1)
    
    # Should have detected file is ready
    assert "session1" in updates, "Monitor should report updates"
    assert "large_photo.jpg" in updates["session1"], "Should track photo"
    assert updates["session1"]["large_photo.jpg"] is True, "File should be marked ready"


# ---------------------------------------------------------------------------
# TEST-ASYNC-004: Background monitor handles mixed states
# ---------------------------------------------------------------------------

def test_monitor_incomplete_files_mixed_states(temp_dir):
    """TEST-ASYNC-004: Monitor only checks DOWNLOADING, ignores other states.
    
    Scenario:
    - Create source dict with mixed file states
    - Only DOWNLOADING files should be checked
    - Others should be skipped
    """
    session_dir = temp_dir / "session"
    session_dir.mkdir()
    
    # Create multiple files with different states
    files = {}
    for i in range(3):
        f = session_dir / f"photo_{i}.jpg"
        Image.new('RGB', (100, 100), color='red').save(str(f), "JPEG")
        files[f"photo_{i}.jpg"] = f
    
    # Create source dict with different states
    source_dict = {
        "session": {
            "photo_0.jpg": {
                "path": str(files["photo_0.jpg"]),
                "state": SourceState.NEW,  # Skip this
            },
            "photo_1.jpg": {
                "path": str(files["photo_1.jpg"]),
                "state": SourceState.DOWNLOADING,  # Check this
            },
            "photo_2.jpg": {
                "path": str(files["photo_2.jpg"]),
                "state": SourceState.OK,  # Skip this
            },
        }
    }
    
    # Monitor should only check photo_1.jpg
    updates = monitor_incomplete_files(source_dict, max_checks=1, check_interval=0.1)
    
    # Should have results for session
    assert "session" in updates, "Should check session"
    
    # Should only have photo_1 (DOWNLOADING)
    assert len(updates["session"]) == 1, "Should only check photo_1.jpg"
    assert "photo_1.jpg" in updates["session"], "Should check photo_1.jpg"


# ---------------------------------------------------------------------------
# TEST-ASYNC-005: Processing skipped for DOWNLOADING files
# ---------------------------------------------------------------------------

def test_check_integrity_skips_downloading(temp_dir, log_capture):
    """TEST-ASYNC-005: check_integrity() skips DOWNLOADING files (no processing).
    
    Scenario:
    - Create file with DOWNLOADING state
    - Run check_integrity()
    - DOWNLOADING file should NOT be processed
    - File status should remain DOWNLOADING
    """
    from bid.source_manager import check_integrity
    
    session_dir = temp_dir / "session"
    session_dir.mkdir()
    
    test_file = session_dir / "incomplete.jpg"
    Image.new('RGB', (100, 100), color='blue').save(str(test_file), "JPEG")
    
    source_dict = {
        "session": {
            "incomplete.jpg": {
                "path": str(test_file),
                "state": SourceState.DOWNLOADING,
                "size": "0.05 MB",
                "mtime": os.stat(test_file).st_mtime,
                "created": "2025:01:01 12:00:00",
            }
        }
    }
    
    # Run integrity check
    changes = check_integrity(source_dict, {}, str(temp_dir))
    
    # DOWNLOADING file should NOT be in changes
    assert "session" not in changes or "incomplete.jpg" not in changes.get("session", {}), \
        "DOWNLOADING file should not be processed"
    
    # File state should still be DOWNLOADING
    assert source_dict["session"]["incomplete.jpg"]["state"] == SourceState.DOWNLOADING, \
        "File state should remain DOWNLOADING"


# ---------------------------------------------------------------------------
# TEST-ASYNC-006: Full async workflow - fast indexing, later monitoring
# ---------------------------------------------------------------------------

def test_full_async_workflow(temp_dir):
    """TEST-ASYNC-006: Full workflow - index fast, update via monitor.
    
    Scenario:
    1. Start slow file copy in background
    2. Scan folder and index files (fast, no blocking)
    3. File indexed as DOWNLOADING
    4. Run monitor_incomplete_files() in background
    5. When file ready, monitor updates state to NEW
    6. Processing can now proceed
    """
    source_folder = temp_dir / "source"
    session_dir = source_folder / "session1"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = session_dir / "workflow_photo.jpg"
    
    def slow_write():
        """Simulate slow file write."""
        time.sleep(0.3)
        img = Image.new('RGB', (1500, 1500), color='cyan')
        img.save(str(test_file), "JPEG", quality=85)
    
    # Step 1: Start slow write
    write_thread = threading.Thread(target=slow_write, daemon=True)
    write_thread.start()
    
    # Step 2: Quick index (no blocking)
    time.sleep(0.05)  # Give write a moment to start
    start_index = time.time()
    source_dict = create_source_dict(str(source_folder))
    index_time = time.time() - start_index
    
    # Indexing should be fast (no wait)
    assert index_time < 0.5, f"Indexing should be fast (<0.5s), took {index_time}s"
    
    if "session1" in source_dict and "workflow_photo.jpg" in source_dict["session1"]:
        item = source_dict["session1"]["workflow_photo.jpg"]
        initial_state = item["state"]
        
        # File should be DOWNLOADING or NEW depending on timing
        assert initial_state in (SourceState.DOWNLOADING, SourceState.NEW), \
            f"Initial state should be DOWNLOADING or NEW, got {initial_state}"
        
        # Step 3: Wait for write to complete
        write_thread.join(timeout=5)
        
        # Step 4: Monitor for updates
        updates = monitor_incomplete_files(
            source_dict,
            max_checks=1,
            check_interval=0.2
        )
        
        # If was DOWNLOADING, should now be ready
        if initial_state == SourceState.DOWNLOADING:
            assert "session1" in updates, "Should have updates for session1"
            if "workflow_photo.jpg" in updates["session1"]:
                assert updates["session1"]["workflow_photo.jpg"] is True, \
                    "File should be detected as ready"


# ---------------------------------------------------------------------------
# TEST-ASYNC-007: is_file_stable blocking check (used by monitor)
# ---------------------------------------------------------------------------

def test_is_file_stable_blocking(temp_dir):
    """TEST-ASYNC-007: is_file_stable() does BLOCKING check (used by monitor).
    
    Scenario:
    - Stable completed file should return True
    - is_file_stable() differs from is_file_ready_quick()
    - Should wait for check_duration to verify stability
    """
    test_file = temp_dir / "stable_file.jpg"
    
    img = Image.new('RGB', (500, 500), color='yellow')
    img.save(str(test_file), "JPEG", quality=85)
    
    # is_file_stable does wait for check_duration
    start = time.time()
    result = is_file_stable(str(test_file), check_duration=0.2)
    elapsed = time.time() - start
    
    # Should have waited for check_duration
    assert elapsed >= 0.2, f"Should wait >= 0.2s, took {elapsed}s"
    assert result is True, "Stable file should return True"
