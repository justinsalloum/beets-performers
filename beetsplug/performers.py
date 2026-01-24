"""Beets plugin to use performer information as artist tags.

This plugin extracts performer information from MusicBrainz recording relationships
and uses it to populate the artist field instead of the albumartist. This is
particularly useful for soundtracks, musicals, and classical music where the album
artist (composer/creator) differs from the actual performers.

Example: For "Rent" by Jonathan Larson, tracks will be tagged with the
actual vocalists (e.g., Adam Pascal, Anthony Rapp) instead of Jonathan Larson.
"""

from beets.plugins import BeetsPlugin
from beets import config
from collections import defaultdict


class PerformersPlugin(BeetsPlugin):
    """Plugin to use performer credits as artist tags."""

    def __init__(self):
        super(PerformersPlugin, self).__init__()

        # Default configuration
        self.config.add({
            'use_performers': True,
            'always_include_vocals': True,
            'include_instruments': False,
            'instrument_roles': [],  # List of specific instruments to include (e.g., ['guitar', 'piano'])
            'fallback_to_artist_credit': True,  # Use artist-credit if no performers found
            'prefer_vocals': True,  # Prefer vocal performers over instrumental
            'separator': ', ',
            'max_artists': 0,  # 0 = no limit
            'vocals_only': False,  # Only use vocals, ignore other performers
        })

        # Register listener for MusicBrainz track extraction
        self.register_listener('mb_track_extract', self.mb_track_extract)
        self._log.debug('Performers plugin initialized')

    def mb_track_extract(self, data, **kwargs):
        """Extract performer information from raw MusicBrainz recording data.

        This hook is called when beets extracts track metadata from MusicBrainz.
        We use it to access the raw recording relationships which contain
        performer information.

        Args:
            data: Dict containing the raw MusicBrainz recording data
            **kwargs: Additional arguments (info, track, etc.)

        Returns:
            Dict of additional fields to add to the TrackInfo object
        """
        if not self.config['use_performers'].get(bool):
            return {}

        # Get the recording object from MusicBrainz data
        recording = data.get('recording', {})

        # Extract performers from relationships
        performers = self._extract_performers_from_recording(recording)

        if performers:
            # Store performers for later use
            self._log.debug(
                'Performers: Found {0} performer(s): {1}',
                len(performers), ', '.join(performers)
            )
            # Return dict to override the artist field
            return {'artist': self._format_performers(performers)}
        elif self.config['fallback_to_artist_credit'].get(bool):
            # Use artist-credit from the recording
            artist_credit = recording.get('artist-credit', [])
            if artist_credit:
                artists = self._extract_artist_credit(artist_credit)
                if artists:
                    self._log.debug(
                        'Performers: Using artist-credit: {0}',
                        ', '.join(artists)
                    )
                    return {'artist': self._format_performers(artists)}

        return {}

    def _extract_performers_from_recording(self, recording):
        """Extract performer names from MusicBrainz recording relationships.

        Args:
            recording: MusicBrainz recording object with relationships

        Returns:
            List of performer names
        """
        performers = []
        vocals = []
        instruments = []

        # Get relationship data
        relations = recording.get('artist-rels', []) or recording.get('relations', [])

        if not relations:
            self._log.debug('Performers: No relationships found in recording')
            return []

        always_vocals = self.config['always_include_vocals'].get(bool)
        include_instruments = self.config['include_instruments'].get(bool)
        instrument_roles = self.config['instrument_roles'].get(list)
        vocals_only = self.config['vocals_only'].get(bool)

        # Process each relationship
        for rel in relations:
            # Get relationship type and attributes
            rel_type = rel.get('type', '')
            attributes = rel.get('attributes', []) or rel.get('attribute-values', {}).keys()

            # Get artist information
            artist = rel.get('artist', {})
            artist_name = artist.get('name', '')

            if not artist_name:
                continue

            # Check if this is a vocal performance
            is_vocal = (
                rel_type in ['vocal', 'vocals', 'performance'] and
                any(attr in ['vocal', 'vocals', 'lead vocals', 'background vocals',
                           'choir vocals', 'spoken vocals']
                    for attr in (attributes if isinstance(attributes, list) else []))
            ) or 'vocal' in str(attributes).lower()

            # Check if this is an instrument performance
            is_instrument = (
                rel_type in ['instrument', 'performer', 'performance'] and
                not is_vocal
            )

            # Categorize the performer
            if is_vocal:
                vocals.append(artist_name)
                self._log.debug(
                    'Performers: Found vocalist: {0} (type: {1}, attrs: {2})',
                    artist_name, rel_type, attributes
                )
            elif is_instrument and not vocals_only:
                # Check if we should include this instrument
                if include_instruments or instrument_roles:
                    if not instrument_roles or any(
                        role.lower() in str(attributes).lower()
                        for role in instrument_roles
                    ):
                        instruments.append(artist_name)
                        self._log.debug(
                            'Performers: Found instrumentalist: {0} (type: {1}, attrs: {2})',
                            artist_name, rel_type, attributes
                        )

        # Combine performers based on preferences
        if self.config['prefer_vocals'].get(bool) and vocals:
            performers = vocals
        elif vocals_only:
            performers = vocals
        else:
            # Vocals first, then instruments
            performers = vocals + instruments

        # Remove duplicates while preserving order
        seen = set()
        unique_performers = []
        for p in performers:
            if p not in seen:
                seen.add(p)
                unique_performers.append(p)

        return unique_performers

    def _extract_artist_credit(self, artist_credit):
        """Extract artist names from artist-credit field.

        Args:
            artist_credit: List of artist-credit objects from MusicBrainz

        Returns:
            List of artist names
        """
        artists = []
        for credit in artist_credit:
            artist = credit.get('artist', {})
            # Use the credited name, or fall back to artist name
            name = credit.get('name') or artist.get('name', '')
            if name:
                artists.append(name)
        return artists

    def _format_performers(self, performers):
        """Format list of performers into artist string.

        Args:
            performers: List of performer names

        Returns:
            Formatted artist string
        """
        # Limit number of artists if configured
        max_artists = self.config['max_artists'].get(int)
        if max_artists > 0 and len(performers) > max_artists:
            performers = performers[:max_artists]

        # Join with configured separator
        separator = self.config['separator'].get(str)
        return separator.join(performers)

    def commands(self):
        """Provide commands for the plugin."""
        # Could add a command to re-tag existing items
        return []
