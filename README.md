# beets-performers

A [beets](https://beets.io/) plugin that extracts performer information from MusicBrainz and uses it to populate the artist field instead of the albumartist. This is particularly useful for soundtracks, musicals, and classical music where the album artist (composer/creator) differs from the actual performers.

## The Problem

When importing albums like soundtracks or musicals into beets, the albumartist is often the composer or creator (e.g., "Jonathan Larson" for the musical "Rent"), but you might want individual tracks tagged with the actual performers (e.g., "Adam Pascal, Anthony Rapp" for specific songs).

MusicBrainz contains detailed performer relationship data, but beets doesn't use this information by default. This plugin bridges that gap.

## Example

For the album [Rent](https://musicbrainz.org/release/ac802446-a6f9-4624-8487-db8fafef7ee5) by Jonathan Larson:

**Without this plugin:**
- Track 1 "Tune Up #1" → Artist: Jonathan Larson

**With this plugin:**
- Track 1 "Tune Up #1" → Artist: Adam Pascal, Anthony Rapp

## Installation

### Option 1: Install from source

```bash
git clone https://github.com/justinsalloum/beets-performers.git
cd beets-performers
pip install -e .
```

### Option 2: Install via pip (when published)

```bash
pip install beets-performers
```

## Configuration

Add `performers` to your plugins list in your beets configuration file:

```yaml
plugins: performers

performers:
  # Enable/disable the plugin
  use_performers: true

  # Always include vocal performers
  always_include_vocals: true

  # Include instrumental performers
  include_instruments: false

  # Only use vocal performers (ignore instruments)
  vocals_only: false

  # Specific instrument roles to include (only if include_instruments is true)
  # Examples: guitar, piano, drums, bass, violin, etc.
  instrument_roles: []

  # Fall back to artist-credit if no performers found
  fallback_to_artist_credit: true

  # Prefer vocal performers over instrumental (when both exist)
  prefer_vocals: true

  # Separator for multiple artists
  separator: ', '

  # Maximum number of artists to include (0 = no limit)
  max_artists: 0
```

## Configuration Examples

### Example 1: Vocals only (default behavior)

Perfect for musicals and soundtracks where you want the singers:

```yaml
performers:
  vocals_only: true
  always_include_vocals: true
```

### Example 2: Include specific instruments

For classical music where you want featured soloists:

```yaml
performers:
  include_instruments: true
  instrument_roles:
    - violin
    - piano
    - cello
  prefer_vocals: false
```

### Example 3: All performers

Include everyone who performed on the track:

```yaml
performers:
  include_instruments: true
  vocals_only: false
  max_artists: 5  # Limit to avoid too many names
```

### Example 4: Limit artist count

When tracks have many performers:

```yaml
performers:
  max_artists: 3
  separator: ' & '
```

## How It Works

1. **During import**, beets fetches metadata from MusicBrainz
2. **The plugin hooks** into the `mb_track_extract` event to access raw MusicBrainz data
3. **Performer relationships** are extracted from the recording's relationship data
4. **Performers are filtered** based on your configuration (vocals, instruments, etc.)
5. **The artist field** is set to the formatted list of performers

## MusicBrainz Data Structure

The plugin extracts data from MusicBrainz recording relationships:

- **Relationship types**: `vocal`, `vocals`, `performance`, `instrument`, `performer`
- **Attributes**: Specific roles like `lead vocals`, `guitar`, `piano`, etc.

## Troubleshooting

### No performers found

If the plugin doesn't find performers, it could be because:

1. **The MusicBrainz recording lacks performer relationships**
   - Check the [MusicBrainz recording page](https://musicbrainz.org/) for your track
   - Look for the "Relationships" section
   - If no performers are listed, you can add them to MusicBrainz

2. **Fallback is disabled**
   - Set `fallback_to_artist_credit: true` to use artist-credit when no performers exist

3. **Performer roles don't match your filters**
   - Check your `instrument_roles` configuration
   - Try setting `include_instruments: true` to see all performers

### Debug logging

Enable debug logging in beets to see what the plugin is doing:

```bash
beet -v import /path/to/music
```

Look for log lines starting with "Performers:" to see what the plugin found.

## Use Cases

### Musicals & Soundtracks
Tag tracks with the actual singers instead of the composer:
- **Rent**, **Hamilton**, **Les Misérables**, etc.

### Classical Music
Tag with the performing orchestra, conductor, or soloists:
- Set `include_instruments: true` and specify roles like `violin`, `piano`

### Jazz & Big Bands
Include featured instrumentalists:
- Configure specific instruments in `instrument_roles`

### Compilation Albums
Use track-level artist credits instead of "Various Artists"

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - See LICENSE file for details

## Credits

Built for the [beets](https://beets.io/) music library manager.

## Related Plugins

- **ftintitle**: Moves featured artists from artist field to title
- **discogs**: Alternative metadata source with artist variations
- **musicbrainz**: Core beets plugin for MusicBrainz integration (required)
