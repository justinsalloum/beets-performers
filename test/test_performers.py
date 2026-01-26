"""Unit tests for the performers plugin."""

import unittest
from unittest.mock import patch

from beetsplug.performers import PerformersPlugin
from test import TestHelper


class PerformersPluginTest(TestHelper):
    """Test cases for the PerformersPlugin class."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.plugin = PerformersPlugin()

    def test_plugin_initialization(self):
        """Test that the plugin initializes correctly."""
        self.assertIsNotNone(self.plugin)
        self.assertEqual(self.plugin.config['auto'].get(bool), True)
        self.assertEqual(self.plugin.config['separator'].get(str), '; ')
        self.assertEqual(self.plugin.config['vocal_only'].get(bool), False)

    def test_plugin_configuration(self):
        """Test plugin configuration options."""
        # Test default values
        self.assertEqual(self.plugin.config['force'].get(bool), False)
        self.assertEqual(self.plugin.config['fallback_to_albumartist'].get(bool), True)
        self.assertTrue(isinstance(self.plugin.config['performer_types'].get(list), list))

    def test_extract_performers_with_artist_credit(self):
        """Test that artist-credit is used when available."""
        recording = {
            'artist-credit': [
                {'name': 'Adam Pascal', 'artist': {'name': 'Adam Pascal'}},
                {'name': 'Anthony Rapp', 'artist': {'name': 'Anthony Rapp'}},
            ]
        }

        performers = self.plugin._extract_performers(recording)

        self.assertEqual(len(performers), 2)
        self.assertIn('Adam Pascal', performers)
        self.assertIn('Anthony Rapp', performers)

    def test_extract_performers_with_relationships(self):
        """Test extracting performers from artist relationships."""
        recording = {
            'artist-relation-list': [
                {'type': 'vocal', 'artist': {'name': 'John Doe'}, 'attributes': ['lead vocals']},
                {'type': 'performer', 'artist': {'name': 'Jane Smith'}, 'attributes': ['guitar']},
            ]
        }

        performers = self.plugin._extract_performers(recording)

        # Should include both since vocal_only is False by default
        self.assertGreater(len(performers), 0)
        self.assertIn('John Doe', performers)

    def test_extract_performers_vocal_only(self):
        """Test vocal-only filtering."""
        # Configure plugin for vocal-only
        self.plugin.config['vocal_only'] = True

        recording = {
            'artist-relation-list': [
                {'type': 'vocal', 'artist': {'name': 'Singer'}, 'attributes': ['vocals']},
                {'type': 'performer', 'artist': {'name': 'Guitarist'}, 'attributes': ['guitar']},
            ]
        }

        performers = self.plugin._extract_performers(recording)

        # Should only include vocalist
        self.assertIn('Singer', performers)
        self.assertNotIn('Guitarist', performers)

    def test_fetch_performers_skip_without_mbid(self):
        """Test that items without MusicBrainz ID are skipped."""
        item = self.add_test_item(mb_trackid=None)

        # Should return without error and not change artist
        original_artist = item.artist
        self.plugin.fetch_performers(item)

        # Artist should remain unchanged
        self.assertEqual(item.artist, original_artist)

    def test_fetch_performers_skip_when_artist_set(self):
        """Test that items with artist set are skipped when force=False."""
        item = self.add_test_item(
            artist='Custom Artist', albumartist='Album Artist', mb_trackid='test-mbid-123'
        )

        original_artist = item.artist

        # Should skip because artist is already set
        self.plugin.fetch_performers(item, force=False)

        # Artist should remain unchanged
        self.assertEqual(item.artist, original_artist)

    @patch('beetsplug.performers.musicbrainzngs.get_recording_by_id')
    def test_fetch_performers_updates_artist(self, mock_get_recording):
        """Test that fetch_performers updates artist field."""
        # Mock MusicBrainz response
        mock_get_recording.return_value = {
            'recording': {
                'artist-credit': [
                    {'name': 'Performer 1', 'artist': {'name': 'Performer 1'}},
                    {'name': 'Performer 2', 'artist': {'name': 'Performer 2'}},
                ]
            }
        }

        item = self.add_test_item(
            artist='Album Artist',  # Same as albumartist, so should be updated
            albumartist='Album Artist',
            mb_trackid='test-mbid-123',
        )

        self.plugin.fetch_performers(item, force=True)

        # Artist should be updated to performers
        self.assertIn('Performer 1', item.artist)
        self.assertIn('Performer 2', item.artist)

    @patch('beetsplug.performers.musicbrainzngs.get_recording_by_id')
    def test_fetch_performers_pretend_mode(self, mock_get_recording):
        """Test that pretend mode doesn't save changes."""
        mock_get_recording.return_value = {
            'recording': {
                'artist-credit': [{'name': 'New Artist', 'artist': {'name': 'New Artist'}}]
            }
        }

        item = self.add_test_item(
            artist='Old Artist', albumartist='Old Artist', mb_trackid='test-mbid-123'
        )

        original_artist = item.artist

        # Run in pretend mode
        self.plugin.fetch_performers(item, force=True, pretend=True)

        # Artist should NOT be changed
        self.assertEqual(item.artist, original_artist)

    def test_commands_registration(self):
        """Test that the plugin registers its commands."""
        commands = self.plugin.commands()

        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0].name, 'performers')

    @patch('beetsplug.performers.time.sleep')
    @patch('beetsplug.performers.musicbrainzngs.get_recording_by_id')
    def test_rate_limiting(self, mock_get_recording, mock_sleep):
        """Test that API calls are rate-limited."""
        mock_get_recording.return_value = {'recording': {}}

        self.plugin._fetch_recording('test-mbid')

        # Should have slept for rate limiting
        mock_sleep.assert_called_once_with(1.0)

    @patch('beetsplug.performers.musicbrainzngs.get_recording_by_id')
    def test_vocal_only_flag_overrides_config(self, mock_get_recording):
        """Test that vocal_only flag overrides config setting."""
        # Mock MusicBrainz response with both vocal and instrumental performers
        mock_get_recording.return_value = {
            'recording': {
                'artist-relation-list': [
                    {'type': 'vocal', 'artist': {'name': 'Singer'}, 'attributes': ['vocals']},
                    {
                        'type': 'performer',
                        'artist': {'name': 'Guitarist'},
                        'attributes': ['guitar'],
                    },
                ]
            }
        }

        # Set config to include all performers
        self.plugin.config['vocal_only'] = False

        item = self.add_test_item(
            artist='Album Artist', albumartist='Album Artist', mb_trackid='test-mbid-123'
        )

        # Fetch with vocal_only=True flag (should override config)
        self.plugin.fetch_performers(item, force=True, vocal_only=True)

        # Should only include singer, not guitarist
        self.assertIn('Singer', item.artist)
        self.assertNotIn('Guitarist', item.artist)

    @patch('beetsplug.performers.musicbrainzngs.get_recording_by_id')
    def test_vocal_only_flag_restores_config(self, mock_get_recording):
        """Test that config is restored after processing with vocal_only flag."""
        mock_get_recording.return_value = {
            'recording': {
                'artist-credit': [{'name': 'Test Artist', 'artist': {'name': 'Test Artist'}}]
            }
        }

        # Set initial config value
        self.plugin.config['vocal_only'] = False
        original_value = self.plugin.config['vocal_only'].get(bool)

        item = self.add_test_item(
            artist='Album Artist', albumartist='Album Artist', mb_trackid='test-mbid-123'
        )

        # Fetch with vocal_only flag
        self.plugin.fetch_performers(item, force=True, vocal_only=True)

        # Config should be restored to original value
        self.assertEqual(self.plugin.config['vocal_only'].get(bool), original_value)

    @patch('beetsplug.performers.musicbrainzngs.get_recording_by_id')
    def test_vocal_only_flag_restores_config_on_error(self, mock_get_recording):
        """Test that config is restored even if an error occurs."""
        # Mock an error during processing
        mock_get_recording.side_effect = Exception('Test error')

        # Set initial config value
        self.plugin.config['vocal_only'] = False
        original_value = self.plugin.config['vocal_only'].get(bool)

        item = self.add_test_item(
            artist='Album Artist', albumartist='Album Artist', mb_trackid='test-mbid-123'
        )

        # Fetch with vocal_only flag (should not raise exception)
        self.plugin.fetch_performers(item, force=True, vocal_only=True)

        # Config should still be restored despite error
        self.assertEqual(self.plugin.config['vocal_only'].get(bool), original_value)

    @patch('beetsplug.performers.musicbrainzngs.get_recording_by_id')
    def test_vocal_only_flag_none_uses_config(self, mock_get_recording):
        """Test that vocal_only=None uses the config value."""
        mock_get_recording.return_value = {
            'recording': {
                'artist-relation-list': [
                    {'type': 'vocal', 'artist': {'name': 'Singer'}, 'attributes': ['vocals']},
                    {
                        'type': 'performer',
                        'artist': {'name': 'Guitarist'},
                        'attributes': ['guitar'],
                    },
                ]
            }
        }

        # Set config to vocal_only=True
        self.plugin.config['vocal_only'] = True

        item = self.add_test_item(
            artist='Album Artist', albumartist='Album Artist', mb_trackid='test-mbid-123'
        )

        # Fetch with vocal_only=None (should use config)
        self.plugin.fetch_performers(item, force=True, vocal_only=None)

        # Should only include singer based on config
        self.assertIn('Singer', item.artist)
        self.assertNotIn('Guitarist', item.artist)

    def test_command_has_vocal_only_option(self):
        """Test that the command registers the vocal-only option."""
        commands = self.plugin.commands()
        cmd = commands[0]

        # Check that the option was registered
        # Get all option strings from all options
        all_option_strings = []
        for opt in cmd.parser.option_list:
            all_option_strings.extend(opt._short_opts)
            all_option_strings.extend(opt._long_opts)

        self.assertIn('-v', all_option_strings)
        self.assertIn('--vocal-only', all_option_strings)


class ExtractPerformersTest(unittest.TestCase):
    """Test cases specifically for _extract_performers method."""

    def setUp(self):
        """Set up test fixtures."""
        self.plugin = PerformersPlugin()

    def test_empty_recording(self):
        """Test with empty recording data."""
        performers = self.plugin._extract_performers({})
        self.assertEqual(len(performers), 0)

    def test_duplicate_performers(self):
        """Test that duplicate performers are removed."""
        recording = {
            'artist-credit': [
                {'name': 'Artist A', 'artist': {'name': 'Artist A'}},
                {'name': 'Artist A', 'artist': {'name': 'Artist A'}},  # Duplicate
                {'name': 'Artist B', 'artist': {'name': 'Artist B'}},
            ]
        }

        performers = self.plugin._extract_performers(recording)

        # Should only include each artist once
        self.assertEqual(len(performers), 2)
        self.assertEqual(performers.count('Artist A'), 1)


if __name__ == '__main__':
    unittest.main()
