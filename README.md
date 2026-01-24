# beets-performers

A [beets](https://beets.io/) plugin that fetches performer credits from MusicBrainz and uses them to populate the artist field instead of the albumartist. This is particularly useful for soundtracks, musicals, and classical music where the album artist (composer/creator) differs from the actual performers.

## The Problem

When importing albums like soundtracks or musicals into beets, the albumartist is often the composer or creator (e.g., "Jonathan Larson" for the musical "Rent"), but you might want individual tracks tagged with the actual performers (e.g., "Adam Pascal; Anthony Rapp" for specific songs).

MusicBrainz contains detailed performer relationship data, but beets doesn't use this information by default. This plugin bridges that gap by querying MusicBrainz for each track's performer credits.

## Example

For the album [Rent](https://musicbrainz.org/release/ac802446-a6f9-4624-8487-db8fafef7ee5) by Jonathan Larson:

**Without this plugin:**
- Track 1 "Tune Up #1" → Artist: Jonathan Larson

**With this plugin:**
- Track 1 "Tune Up #1" → Artist: Adam Pascal; Anthony Rapp

## Installation

### Install from source

```bash
git clone https://github.com/justinsalloum/beets-performers.git
cd beets-performers
pip install -e .
```

### Install via pip (when published)

```bash
pip install beets-performers
```

## Configuration

Add `performers` to your plugins list in your beets configuration file (`~/.config/beets/config.yaml`):

```yaml
plugins: performers

performers:
  # Automatically fetch performers during import (default: true)
  auto: true

  # Re-fetch even if artist is already set (default: false)
  force: false

  # Separator for multiple performers (default: '; ')
  separator: '; '

  # Only include vocal performers (default: false)
  vocal_only: false

  # Use albumartist if no performers found (default: true)
  fallback_to_albumartist: true

  # Types of performer relationships to include
  performer_types:
    - vocal
    - performer
    - instrument
    - vocals
```

## Usage

### Automatic Import

By default, the plugin automatically fetches performer information when you import new music:

```bash
beet import /path/to/music
```

The plugin will:
1. Query MusicBrainz for each track's recording ID
2. Extract performer credits from the artist-credit field
3. Update the artist tag with the performers
4. Fall back to albumartist if no performers are found (if configured)

### Manual Command

You can also manually fetch performers for existing tracks in your library:

```bash
# Fetch performers for all tracks
beet performers

# Fetch performers for specific tracks
beet performers artist:Larson

# Force re-fetch even if artist is already set
beet performers -f artist:Larson
```

## Configuration Examples

### Example 1: Vocals only (for musicals/soundtracks)

Perfect for musicals and soundtracks where you want the singers:

```yaml
performers:
  auto: true
  vocal_only: true
  separator: ', '
  fallback_to_albumartist: true
```

### Example 2: All performers

Include everyone who performed on the track:

```yaml
performers:
  auto: true
  vocal_only: false
  performer_types:
    - vocal
    - performer
    - instrument
  separator: '; '
```

### Example 3: Specific instruments only

For classical music where you want featured soloists:

```yaml
performers:
  auto: true
  vocal_only: false
  performer_types:
    - guitar
    - piano
    - drums
  separator: ', '
```

### Example 4: Manual mode

Only fetch performers when you explicitly request it:

```yaml
performers:
  auto: false
  force: false
```

Then run manually:
```bash
beet performers [query]
```

## How It Works

1. **During or after import**, the plugin processes each track
2. **For each track with a MusicBrainz recording ID**, it queries the MusicBrainz API
3. **Performer credits are extracted** from the `artist-credit` field (the track's credited artists on MusicBrainz)
4. **If no artist-credit exists**, it falls back to extracting from `artist-relation-list` (performer relationships)
5. **The artist field is updated** with the formatted list of performers
6. **Rate limiting is applied** (1 request per second) to comply with MusicBrainz API guidelines

## MusicBrainz Data Structure

The plugin extracts data in this order:

1. **artist-credit**: The primary credited artists for the track (what shows as track artists on MusicBrainz)
2. **artist-relation-list**: Performer relationships (if artist-credit is not available)
   - Filtered by `performer_types` configuration
   - Can include vocals, instruments, or both

## Performance Considerations

**Important**: This plugin makes additional API calls to MusicBrainz for each track. For large imports:

- The plugin respects MusicBrainz rate limits (1 request per second)
- Importing a 15-track album will take approximately 15 seconds
- Consider using `auto: false` and running the command manually on specific albums

## Troubleshooting

### No performers found

If the plugin doesn't find performers, it could be because:

1. **The track doesn't have a MusicBrainz recording ID**
   - Make sure the track was matched to MusicBrainz during import
   - Check with: `beet ls -f '$artist - $title (MBID: $mb_trackid)'`

2. **The MusicBrainz recording lacks performer relationships**
   - Check the [MusicBrainz recording page](https://musicbrainz.org/) for your track
   - Look for the "Relationships" section or artist-credit
   - If no performers are listed, you can add them to MusicBrainz

3. **Fallback is disabled**
   - Set `fallback_to_albumartist: true` to use albumartist when no performers exist

4. **Performer roles don't match your filters**
   - Check your `performer_types` configuration
   - Try setting `vocal_only: false` to include all performer types

### Debug logging

Enable debug logging in beets to see what the plugin is doing:

```bash
beet -v import /path/to/music
# or
beet -v performers [query]
```

Look for log lines from the performers plugin to see what data it found.

### Rate limiting

The plugin automatically rate-limits requests to 1 per second. If you see errors about rate limiting:
- Wait a few minutes before retrying
- Consider processing smaller batches of tracks

## Use Cases

### Musicals & Soundtracks
Tag tracks with the actual singers instead of the composer:
- **Rent**, **Hamilton**, **Les Misérables**, etc.
- Use `vocal_only: true`

### Classical Music
Tag with the performing orchestra, conductor, or soloists:
- Set `vocal_only: false` and specify instrument types in `performer_types`

### Jazz & Big Bands
Include featured instrumentalists:
- Configure specific instruments in `performer_types`: `['saxophone', 'trumpet', 'piano']`

### Compilation Albums
Use track-level artist credits instead of "Various Artists"

### Re-tagging Existing Libraries
Use the manual command to update existing tracks:
```bash
beet performers -f albumartist:"Various Artists"
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - See LICENSE file for details

## Credits

Built for the [beets](https://beets.io/) music library manager.

Uses [python-musicbrainzngs](https://python-musicbrainzngs.readthedocs.io/) for MusicBrainz API access.

## Related Plugins

- **ftintitle**: Moves featured artists from artist field to title
- **discogs**: Alternative metadata source with artist variations
- **musicbrainz**: Core beets plugin for MusicBrainz integration (required)
