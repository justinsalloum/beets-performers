"""Test configuration and utilities for beets-performers plugin tests."""

import os
import shutil
import tempfile
from unittest import TestCase

from beets import config
from beets.library import Library


class TestHelper(TestCase):
    """Base test class with helper methods for beets plugin testing."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test library
        self.temp_dir = tempfile.mkdtemp()
        self.libdir = os.path.join(
            self.temp_dir, b'libdir' if isinstance(self.temp_dir, bytes) else 'libdir'
        )
        os.makedirs(self.libdir)

        # Set up test database
        self.db_path = os.path.join(
            self.temp_dir, b'library.db' if isinstance(self.temp_dir, bytes) else 'library.db'
        )

        # Configure beets for testing - load defaults but not user config
        config.clear()
        config.read(user=False, defaults=True)

        # Set required config values for testing
        config['timeout'] = 5.0
        config['library'] = self.db_path
        config['directory'] = self.libdir

        # Initialize library
        self.lib = Library(self.db_path, self.libdir)

    def tearDown(self):
        """Clean up test environment."""
        # Close library connection
        if hasattr(self, 'lib'):
            self.lib._close()

        # Remove temporary directory
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        # Clear config
        config.clear()

    def add_test_item(self, **kwargs):
        """Add a test item to the library with given attributes."""
        from beets.library import Item

        # Default values
        defaults = {
            'title': 'Test Track',
            'artist': 'Test Artist',
            'albumartist': 'Test Album Artist',
            'album': 'Test Album',
            'path': os.path.join(
                self.libdir, b'test.mp3' if isinstance(self.libdir, bytes) else 'test.mp3'
            ),
        }
        defaults.update(kwargs)

        item = Item(**defaults)
        item.add(self.lib)
        return item
