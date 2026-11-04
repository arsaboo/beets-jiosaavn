# beets-jiosaavn Plugin

beets-jiosaavn is a Python plugin for the [beets](https://github.com/beetbox/beets) music library management system. It adds JioSaavn as a metadata source for automatic tagging of music files.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Initial Setup and Installation
- Install dependencies and the plugin:
  ```bash
  python3 -m pip install -e .
  ```
- **NEVER CANCEL**: Initial installation takes 10-20 seconds normally, but may take up to 5 minutes if network is slow or MusicAPy dependency needs to be cloned from GitHub. Set timeout to 10+ minutes.
- If installation fails with network timeout, the core dependencies may already be available. Try:
  ```bash
  python3 -m pip install -e . --no-deps
  ```
- Verify Python environment: `python3 --version` (requires Python 3.9+, tested with 3.13)
- Check beets installation: `beet version` (should show beets 2.10.0 or newer)

### Build and Test Process
- **No formal build process required** - this is a pure Python plugin
- **No existing test suite** - the repository contains no test files
- **No CI/CD configuration** - no GitHub Actions or other automation
- Lint with Black and flake8 at 88 columns (config lives in `pyproject.toml` and `setup.cfg`):
  ```bash
  python3 -m black beetsplug setup.py
  python3 -m flake8 beetsplug setup.py
  ```
- Run basic plugin validation (prints nothing when the imports are clean):
  ```bash
  python3 -W error::DeprecationWarning -c "import beetsplug.jiosaavn; print('ok')"
  ```
- Test JioSaavn API dependency:
  ```bash
  python3 -c "from musicapy.saavn_api.api import SaavnAPI; api = SaavnAPI(); print('JioSaavn API available')"
  ```

### Known Issues and Compatibility
- The plugin targets the metadata source interface introduced in beets 2.10.0:
  `JioSaavnPlugin` extends `beets.metadata_plugins.SearchApiMetadataSourcePlugin`
  and implements `get_search_query_with_filters()`, `get_search_response()`,
  `album_for_id()` and `track_for_id()`.
- Do **not** reintroduce the legacy pattern: `BeetsPlugin` plus a hand-written
  `data_source` attribute, a `source_weight` config option, or plugin-side
  `get_distance()` / `add_identity()` hooks. beets 2.x derives the source name
  from the class, renames `source_weight` to `data_source_mismatch_penalty` and
  computes the match distance centrally; the legacy shim disappears in beets 3.0.
- MusicAPy accepts a `limit` parameter on its search endpoints but the API
  ignores it, so `get_search_response()` applies `search_limit` itself.

### Development Workflow
- Edit plugin code in `beetsplug/jiosaavn.py`
- No compilation needed - Python plugin loads directly
- Test changes by creating a minimal beets config:
  ```bash
  echo "plugins: jiosaavn" > test_config.yaml
  beet -c test_config.yaml version
  ```
  - **Note**: beets will run even if plugin fails to load, but will show error messages
  - Look for "** error loading plugin jiosaavn" in output to identify import issues
- **Lint before testing plugin functionality**
- Test plugin installation without dependencies (if deps already available):
  ```bash
  python3 -m pip install -e . --no-deps
  ```
  - Takes ~1 second, reinstalls if already present

### Validation Scenarios
After making changes, ALWAYS validate with these scenarios:

1. **Basic Plugin Loading**:
   ```bash
   python3 -W error::DeprecationWarning -c "import beetsplug.jiosaavn; print('Imports clean')"
   ```
   - Should complete in ~0.17 seconds

2. **Plugin Instantiation**:
   ```bash
   python3 -c "import sys; sys.path.insert(0, '.'); from beetsplug.jiosaavn import JioSaavnPlugin; plugin = JioSaavnPlugin(); print('Plugin creation successful:', plugin.data_source)"
   ```
   - Must print `JioSaavn`: the data source name is derived from the class name
     by `MetadataSourcePlugin`, the plugin does not declare it

3. **Dependencies Available**:
   ```bash
   python3 -c "from musicapy.saavn_api.api import SaavnAPI; import requests; from PIL import Image; print('All dependencies available')"
   ```
   - Should complete in ~0.12 seconds

4. **Complete Workflow Test** (after fixing imports):
   ```bash
   echo "plugins: jiosaavn" > test_config.yaml
   beet -c test_config.yaml version
   ```
   - Should show beets version and loaded plugins (including jiosaavn if working)
   - If plugin has issues, will show error but beets still runs

## Key Components

### Repository Structure
```
.
├── beetsplug/
│   ├── __init__.py          # Plugin namespace package
│   └── jiosaavn.py          # Main plugin implementation
├── setup.py                 # Package configuration
├── README.md               # Basic usage documentation  
├── LICENSE                 # MIT license
└── .gitignore              # Standard Python gitignore
```

### Dependencies
- **beets>=2.10.0** - Main music library management system
- **MusicAPy** - JioSaavn API wrapper (installed from GitHub)
- **requests** - HTTP requests for API calls
- **pillow** - Image processing for album art
- **Standard library**: collections, re, time, io

### Plugin Architecture
- Main class: `JioSaavnPlugin` extends `beets.metadata_plugins.SearchApiMetadataSourcePlugin`
- Data source: "JioSaavn" (inferred from the class name)
- Metadata source API implemented:
  - `get_search_query_with_filters()` - builds the free-text search query
  - `get_search_response()` - calls MusicAPy and returns hits carrying release URLs
  - `candidates()` - album search results (also passes the release type through)
  - `item_candidates()` - track search results (inherited from the base class)
  - `album_for_id()` - fetch an album by JioSaavn URL
  - `track_for_id()` - fetch a track by JioSaavn URL
- Flexible attributes: `jiosaavn_album_id`, `jiosaavn_artist_id`,
  `jiosaavn_track_id`, `jiosaavn_starring`, `jiosaavn_perma_url`,
  `jiosaavn_updated`, `cover_art_url`
- Album art URL validation and processing

## Common Tasks

The following are outputs from frequently run commands. Reference them instead of running bash commands to save time.

### Repository root listing
```bash
ls -la
```
```
total 48
drwxr-xr-x 6 runner runner 4096 .
drwxr-xr-x 3 runner runner 4096 ..
drwxrwxr-x 2 runner runner 4096 .github/           # Contains copilot-instructions.md
-rw-rw-r-- 1 runner runner 2763 .gitignore  
-rw-rw-r-- 1 runner runner 1067 LICENSE
-rw-rw-r-- 1 runner runner  469 README.md
drwxrwxr-x 3 runner runner 4096 beetsplug/         # Main plugin code
-rw-rw-r-- 1 runner runner  522 setup.py
```

### Plugin main code structure
```bash
wc -l beetsplug/jiosaavn.py
```
```
241 beetsplug/jiosaavn.py  # ~240 lines of Python code
```

### Actual dependency verification
```bash
cat setup.py | grep -A 10 install_requires
```
```python
install_requires=[
    'beets>=2.10.0',
    'MusicAPy @ git+https://github.com/dmdhrumilmistry/MusicAPy',
    'requests',
    'pillow',
],
```

### Expected beets version
```bash
beet version
```
```
beets version 2.10.0 or newer
```

### Imports to use for a beets 2.x metadata source
```python
from beets.autotag import AlbumInfo, TrackInfo
from beets.dbcore import types
from beets.importer.tasks import REIMPORT_FRESH_FIELDS_ITEM
from beets.metadata_plugins import IDResponse, SearchApiMetadataSourcePlugin
```
Do not import `Distance`/`get_distance` (the plugin does not compute distance) or
`beets.library.DateType` (deprecated; use `beets.dbcore.types.DATE`).

## Troubleshooting

### Common Issues

1. **"is used as a legacy metadata source" deprecation warning**
   - The plugin class was reached through `BeetsPlugin` instead of
     `MetadataSourcePlugin`; keep `JioSaavnPlugin` extending
     `SearchApiMetadataSourcePlugin`

2. **Network timeout during installation**  
   - The MusicAPy dependency is cloned from GitHub and may timeout
   - Workaround: Install dependencies separately or use `--no-deps` flag

3. **Plugin shows as not loaded in beets**
   - Check for import errors in beets output; rerun the strict import check
     (`python3 -W error::DeprecationWarning -c "import beetsplug.jiosaavn"`)

4. **`Error in 'JioSaavn.candidates'` in a `beet -v import` log**
   - An exception escaped a metadata source method; look at the
     "Exception details:" traceback right below it

### Performance Expectations
- Import validation: ~0.17 seconds
- JioSaavn API test: ~0.11 seconds  
- Full dependency check: ~0.12 seconds
- Plugin installation (no deps): ~1 second
- Initial installation with deps: 10 seconds - 5 minutes (depending on network)