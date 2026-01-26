"""Beets plugin to fetch performer credits from MusicBrainz and populate artist tags.

This plugin queries MusicBrainz for performer relationships on each track and
replaces the artist field with the performers instead of using the albumartist.
"""

import time

import musicbrainzngs
from beets import ui
from beets.plugins import BeetsPlugin


class PerformersPlugin(BeetsPlugin):
    def __init__(self):
        super().__init__()

        # Configure MusicBrainz client
        musicbrainzngs.set_useragent(
            'beets-performers-plugin', '0.1', 'https://github.com/beetbox/beets'
        )

        # Plugin configuration options
        self.config.add(
            {
                'auto': True,  # Automatically fetch performers during import
                'force': False,  # Re-fetch even if artist is already set
                'separator': '; ',  # Separator for multiple performers
                'vocal_only': False,  # Only include vocal performers
                'fallback_to_albumartist': True,  # Use albumartist if no performers found
                'performer_types': [
                    'vocal',
                    'performer',
                    'instrument',
                    'vocals',
                ],  # Types to include
            }
        )

        # Register as an import stage
        if self.config['auto']:
            self.import_stages = [self.imported]

    def commands(self):
        """Add command for manual performer fetching."""
        cmd = ui.Subcommand('performers', help='fetch performer data for tracks')
        cmd.parser.add_option(
            '-f',
            '--force',
            action='store_true',
            default=False,
            help='re-fetch performers even if already present',
        )
        cmd.parser.add_option(
            '-p',
            '--pretend',
            action='store_true',
            default=False,
            help='preview changes without updating the database',
        )
        cmd.parser.add_option(
            '-v',
            '--vocal-only',
            action='store_true',
            default=False,
            help='only include vocal performers (ignore instrumentalists)',
        )
        cmd.func = self.command_func
        return [cmd]

    def command_func(self, lib, opts, args):
        """Command handler for manual performer fetching."""
        force = opts.force or self.config['force'].get(bool)
        pretend = opts.pretend
        vocal_only = opts.vocal_only if hasattr(opts, 'vocal_only') else None

        # Get items to process
        items = lib.items(ui.decargs(args))

        if pretend:
            self._log.info(
                'PRETEND MODE: Processing {} tracks (no changes will be saved)...', len(items)
            )
        else:
            self._log.info('Processing {} tracks...', len(items))

        for item in items:
            self.fetch_performers(item, force=force, pretend=pretend, vocal_only=vocal_only)

    def imported(self, session, task):
        """Hook called after items are imported."""
        if task.is_album:
            items = task.imported_items()
        else:
            items = [task.item]

        force = self.config['force'].get(bool)

        for item in items:
            self.fetch_performers(item, force=force)

    def fetch_performers(self, item, force=False, pretend=False, vocal_only=None):
        """Fetch performer data for a single item and update artist field.

        Args:
            item: The Item to process
            force: Re-fetch even if artist is already set
            pretend: Preview changes without saving to database
            vocal_only: Override config to only include vocal performers (None = use config)
        """
        # Temporarily override config if vocal_only flag is provided
        original_vocal_only = None
        if vocal_only is not None:
            original_vocal_only = self.config['vocal_only'].get(bool)
            self.config['vocal_only'] = vocal_only

        try:
            # Skip if artist is already set and force is False
            if not force and item.artist and item.artist != item.albumartist:
                self._log.debug('Skipping {}: artist already set', item)
                return

            # Need a MusicBrainz recording ID
            if not item.mb_trackid:
                self._log.debug('Skipping {}: no MB recording ID', item)
                return

            try:
                # Fetch recording data with artist credits
                recording = self._fetch_recording(item.mb_trackid)

                if not recording:
                    self._log.debug('No recording data found for {}', item)
                    return

                # Extract performers
                performers = self._extract_performers(recording)

                if performers:
                    separator = self.config['separator'].get(str)
                    artist_string = separator.join(performers)

                    old_artist = item.artist or ''
                    # Character-level diff highlighting (only changed chars colored)
                    old_colored, new_colored = ui._colordiff(old_artist, artist_string)

                    if pretend:
                        ui.print_(f'Performers [PREVIEW]: {item} | {old_colored} -> {new_colored}')
                    else:
                        ui.print_(f'Performers: {item} | {old_colored} -> {new_colored}')
                        item.artist = artist_string
                        item.store()
                else:
                    self._log.debug('No performers found for {}', item)

                    # Fallback to albumartist if configured
                    if self.config['fallback_to_albumartist'].get(bool):
                        if item.artist != item.albumartist:
                            old_artist = item.artist or ''
                            # Character-level diff highlighting (only changed chars colored)
                            old_colored, new_colored = ui._colordiff(old_artist, item.albumartist)

                            if pretend:
                                ui.print_(
                                    f'Performers [PREVIEW]: {item} | {old_colored} -> {new_colored} (fallback)'
                                )
                            else:
                                ui.print_(
                                    f'Performers: {item} | {old_colored} -> {new_colored} (fallback)'
                                )
                                item.artist = item.albumartist
                                item.store()

            except musicbrainzngs.WebServiceError as e:
                self._log.error('MusicBrainz error for {}: {}', item, e)
            except Exception as e:
                self._log.error('Error processing {}: {}', item, e)
        finally:
            # Restore original config if it was overridden
            if original_vocal_only is not None:
                self.config['vocal_only'] = original_vocal_only

    def _fetch_recording(self, mb_trackid):
        """Fetch recording data from MusicBrainz with rate limiting."""
        try:
            # Rate limiting - MB allows 1 request per second
            time.sleep(1.0)

            # Fetch recording with artist credits and relationships
            result = musicbrainzngs.get_recording_by_id(
                mb_trackid, includes=['artist-credits', 'artist-rels']
            )

            return result.get('recording')

        except musicbrainzngs.ResponseError as e:
            self._log.error('MusicBrainz API error: {}', e)
            return None

    def _extract_performers(self, recording):
        """Extract performer names from recording data."""
        performers = []

        # First, try artist-credits (this is what shows as track artists on MB)
        if 'artist-credit' in recording:
            for credit in recording['artist-credit']:
                if isinstance(credit, dict) and 'artist' in credit:
                    name = credit['artist'].get('name', '')
                    if name and name not in performers:
                        performers.append(name)

        # If no artist credits, try to get performers from relationships
        if not performers and 'artist-relation-list' in recording:
            vocal_only = self.config['vocal_only'].get(bool)
            performer_types = self.config['performer_types'].get(list)

            for relation in recording['artist-relation-list']:
                rel_type = relation.get('type', '').lower()

                # Filter by performer type if configured
                if vocal_only and 'vocal' not in rel_type:
                    continue

                # Check if this relation type is in our configured types
                if performer_types and not any(pt in rel_type for pt in performer_types):
                    continue

                artist = relation.get('artist', {})
                name = artist.get('name', '')

                if name and name not in performers:
                    performers.append(name)

        return performers


# Export the plugin class
__all__ = ['PerformersPlugin']
