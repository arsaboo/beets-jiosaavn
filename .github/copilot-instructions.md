# GitHub Copilot Instructions for beets-jiosaavn

## Project Overview

This is a **beets plugin** that integrates with **JioSaavn** (an Indian music streaming service) to provide music metadata for the [beets music library management system](https://github.com/beetbox/beets). The plugin allows users to automatically tag their music files with metadata retrieved from JioSaavn's catalog.

## Architecture & Code Structure

### Main Components

- **`beetsplug/jiosaavn.py`**: The main plugin implementation
- **`beetsplug/__init__.py`**: Python package initialization
- **`setup.py`**: Package installation configuration
- **`README.md`**: User documentation

### Key Classes & Methods

1. **`JioSaavnPlugin`**: Main plugin class inheriting from `BeetsPlugin`
   - `get_albums()`: Search for albums using JioSaavn API
   - `get_tracks()`: Search for individual tracks
   - `candidates()`: Provide album candidates for autotagger
   - `item_candidates()`: Provide track candidates for autotagger
   - `album_for_id()`: Fetch album by JioSaavn URL/ID
   - `track_for_id()`: Fetch track by JioSaavn URL/ID
   - `get_album_info()`: Convert JioSaavn album data to beets `AlbumInfo`
   - `_get_track()`: Convert JioSaavn track data to beets `TrackInfo`

### Data Flow

1. User runs beets import/update commands
2. Beets calls plugin's search methods (`candidates`, `item_candidates`)
3. Plugin queries JioSaavn API via MusicAPy library
4. Raw JSON responses are converted to beets data structures (`AlbumInfo`, `TrackInfo`)
5. Beets uses this data for autotagging music files

## Development Guidelines

### Code Style
- Follow Python PEP 8 conventions
- Use descriptive variable names
- Maintain existing logging patterns with `self._log.debug()`
- Handle exceptions gracefully with try/catch blocks
- Use regex for query sanitization (remove special characters, disc info)

### Dependencies
- **beets** (>=1.6.0): Core music library management
- **MusicAPy**: Third-party library for JioSaavn API access
- **requests**: HTTP client for image validation
- **pillow**: Image processing for cover art validation

### API Integration
- Uses `SaavnAPI` from MusicAPy library
- Handles both album and song searches
- Creates proper identifiers from JioSaavn permalink URLs
- Validates cover art URLs before storing

### Data Mapping

#### Custom Fields Added to Beets Database:
```python
item_types = {
    'jiosaavn_album_id': types.INTEGER,
    'jiosaavn_artist_id': types.INTEGER, 
    'jiosaavn_track_id': types.STRING,
    'jiosaavn_starring': types.STRING,
    'jiosaavn_perma_url': types.STRING,
    'jiosaavn_updated': DateType(),
    'cover_art_url': types.STRING,
}
```

### Error Handling
- Always wrap API calls in try/catch blocks
- Log errors using `self._log.debug()` 
- Return empty lists on API failures rather than crashing
- Handle missing/null data fields gracefully

### Query Processing
- Strip non-word characters that might break searches
- Remove disc/CD information (e.g., "CD1", "disc 1") from queries
- Support both Various Artists (VA) and single artist searches

## Testing & Development

### Manual Testing
- Test with various album/artist combinations
- Verify cover art URL validation works
- Check both English and non-English (Unicode) artist/album names
- Test edge cases like missing metadata fields

### Common Issues to Watch For
- API rate limiting (add delays if needed)
- Invalid permalink URL formats
- Missing required fields in API responses
- Unicode handling in song/album titles
- Image URL validation failures

## Plugin Configuration

Users configure the plugin in their beets `config.yaml`:
```yaml
plugins: jiosaavn

jiosaavn:
  source_weight: 0.5  # Relative weight vs other metadata sources
```

## Integration Points

### With Beets Core
- Inherits from `BeetsPlugin`
- Implements autotagger hooks (`candidates`, `item_candidates`)
- Uses beets distance calculation for matching
- Stores metadata in beets database fields

### With JioSaavn API
- Search endpoints for albums and songs
- Detail endpoints for complete metadata
- Permalink-based ID generation
- Image URL processing for cover art

## Best Practices for AI Assistance

1. **Preserve existing error handling patterns**
2. **Maintain API rate limiting considerations**
3. **Test with both English and Unicode content**
4. **Keep logging detailed for debugging**
5. **Follow beets plugin conventions for data structures**
6. **Validate all external URLs before storing**
7. **Handle missing metadata gracefully**
8. **Maintain backward compatibility with existing configurations**

## Debugging Tips

- Use `beets -v import` for verbose logging
- Check `self._log.debug()` messages for API responses
- Verify JioSaavn permalink URL formats
- Test image URL accessibility separately
- Validate JSON structure from API responses

## Related Resources

- [Beets Plugin Development Guide](https://beets.readthedocs.io/en/stable/dev/plugins.html)
- [JioSaavn Web Interface](https://www.jiosaavn.com)
- [MusicAPy Library Documentation](https://github.com/dmdhrumilmistry/MusicAPy)