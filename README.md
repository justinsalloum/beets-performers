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

### Install from GitHub

```bash
pip install git+https://github.com/justinsalloum/beets-performers.git
```

### Install from source (for development)

```bash
git clone https://github.com/justinsalloum/beets-performers.git
cd beets-performers

# Install Poetry if you don't have it
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies and the plugin
poetry install

# Set up git hooks (runs tests before push)
./setup-hooks.sh
```

### Install via pip (when published to PyPI)

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

  # Use credited name instead of canonical artist name (default: true)
  # When true: uses "Ship's Chorus" instead of "[Disney]"
  use_credited_name: true

  # Use albumartist if no performers found (default: true)
  fallback_to_albumartist: true

  # Character replacements for normalizing unicode to ASCII (default: {})
  # Example: replace unicode apostrophes and quotes with ASCII equivalents
  replacements:
    ''': "'"   # Unicode apostrophe → ASCII apostrophe
    '"': '"'   # Unicode left quote → ASCII quote
    '"': '"'   # Unicode right quote → ASCII quote
    '–': '-'   # En dash → ASCII hyphen
    '—': '-'   # Em dash → ASCII hyphen

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

# Preview changes without saving (dry-run mode)
beet performers -p artist:Larson

# Only include vocal performers (override config)
beet performers -v artist:Larson

# Force re-fetch even if artist is already set
beet performers -f artist:Larson

# Use "and" before the last performer
beet performers -a artist:Larson

# Use credited artist names (override config)
beet performers -c artist:Moana

# Combine flags: preview forced re-fetch with vocals only
beet performers -fpv artist:Larson

# Combine flags: vocals only with "and" separator
beet performers -va artist:Larson

# Combine flags: credited names with natural formatting
beet performers -ca artist:Moana
```

**Command Flags:**
- `-f`, `--force`: Re-fetch performers even if artist is already set
- `-p`, `--pretend`: Preview changes without updating the database (dry-run)
- `-v`, `--vocal-only`: Only include vocal performers, ignore instrumentalists (overrides config)
- `-a`, `--and-last`: Use "and" before the last performer (e.g., "A, B and C" instead of "A, B, C")
- `-c`, `--use-credited-name`: Use credited artist names instead of canonical names (overrides config)

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

**Note**: For more natural formatting with the `-a/--and-last` flag, you can use:
```bash
# This will format as "Kristen Bell and Idina Menzel" instead of "Kristen Bell, Idina Menzel"
beet performers -va artist:Frozen
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

### Example 5: Use canonical artist names

For consistency across different releases, use canonical artist names:

```yaml
performers:
  auto: true
  use_credited_name: false  # Use canonical names like "[Disney]" instead of "Ship's Chorus"
```

This is useful when you want:
- Consistent artist names across different releases
- Standard artist entities for better library organization
- Integration with other tools that expect canonical names

### Example 6: Normalize unicode characters to ASCII

Replace unicode characters with ASCII equivalents for better compatibility:

```yaml
performers:
  auto: true
  replacements:
    ''': "'"   # Unicode apostrophe (U+2019) → ASCII apostrophe
    '"': '"'   # Unicode left quote (U+201C) → ASCII quote
    '"': '"'   # Unicode right quote (U+201D) → ASCII quote
    '–': '-'   # En dash (U+2013) → ASCII hyphen
    '—': '-'   # Em dash (U+2014) → ASCII hyphen
```

This is useful when:
- You prefer ASCII-only text in your music library
- Your music player or device has issues with unicode characters
- You want consistent character encoding across all metadata
- Similar to using the `beets-importreplace` plugin for other fields

**Example transformations:**
- `O'Brien` → `O'Brien`
- `"The Boss"` → `"The Boss"`
- `Jean–Luc` → `Jean-Luc`

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
   - **Credited name** (`use_credited_name: true`): How the artist is credited on this specific release (e.g., "Ship's Chorus", "Cast")
   - **Canonical name** (`use_credited_name: false`): The standardized artist name in MusicBrainz (e.g., "[Disney]", "Various Artists")
2. **artist-relation-list**: Performer relationships (if artist-credit is not available)
   - Filtered by `performer_types` configuration
   - Can include vocals, instruments, or both

### Credited vs Canonical Names

MusicBrainz distinguishes between:
- **Credited name**: How the artist appears in the credits of a specific release (flexible, can be creative)
- **Canonical name**: The official standardized name for the artist entity (consistent across releases)

**Example from Moana soundtrack:**
- Credited as: "Ship's Chorus" (what you see on the album)
- Canonical artist: "[Disney]" (the MusicBrainz entity)

By default, this plugin uses **credited names** (`use_credited_name: true`) because they match what you see on the physical release and are more descriptive for compilations and soundtracks.

You can override this behavior on a per-command basis using the `-c/--use-credited-name` flag:
```bash
# Use credited names for this run (even if config says otherwise)
beet performers -c artist:Moana
```

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

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/justinsalloum/beets-performers.git
cd beets-performers

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Set up git hooks (runs tests before push)
./setup-hooks.sh
```

### Running Tests

The plugin includes a comprehensive test suite. Use Poetry's poe tasks:

```bash
# Run tests
poetry run poe test

# Run tests with coverage (HTML and terminal reports)
poetry run poe test-with-coverage

# View coverage report
open htmlcov/index.html
```

Or use pytest directly:

```bash
# Run tests
poetry run pytest -v

# Run tests with coverage
poetry run pytest --cov=beetsplug.performers --cov-report=html
```

### Code Quality

Format and lint code using Ruff:

```bash
# Check formatting
poetry run poe format-check

# Auto-format code
poetry run poe format

# Run linter
poetry run poe lint
```

### Git Hooks

This project uses a pre-push hook to ensure code quality:

```bash
# Set up hooks (run once after cloning)
./setup-hooks.sh
```

The pre-push hook automatically:
- Runs the full test suite before pushing
- Prevents pushing broken code
- Can be bypassed with `git push --no-verify` (not recommended)

### Continuous Integration

GitHub Actions automatically runs on every push and pull request:

**Test Job:**
- Tests on Python 3.9, 3.10, 3.11, and 3.12
- Runs full test suite
- Uploads coverage to Codecov (Python 3.11 only)

**Lint Job:**
- Checks code formatting with Ruff
- Runs linting checks

All tests and checks must pass before code can be merged.

## Contributing

Contributions are welcome! Here's how to contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests to ensure they pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

Please ensure:
- All tests pass
- Code follows the existing style
- New features include tests
- Documentation is updated

## License

MIT License - See LICENSE file for details

## Credits

Built for the [beets](https://beets.io/) music library manager.

Uses [python-musicbrainzngs](https://python-musicbrainzngs.readthedocs.io/) for MusicBrainz API access.

## Related Plugins

- **ftintitle**: Moves featured artists from artist field to title
- **discogs**: Alternative metadata source with artist variations
- **musicbrainz**: Core beets plugin for MusicBrainz integration (required)
