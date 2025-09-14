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
- Verify Python environment: `python3 --version` (requires Python 3.6+, tested with 3.12.3)
- Check beets installation: `beet version` (should show beets 2.4.0 or compatible)

### Build and Test Process
- **No formal build process required** - this is a pure Python plugin
- **No existing test suite** - the repository contains no test files
- **No CI/CD configuration** - no GitHub Actions or other automation
- Run basic plugin validation:
  ```bash
  python3 -c "from beets.autotag.distance import Distance; from beets.autotag.hooks import AlbumInfo, TrackInfo; from beets.plugins import BeetsPlugin; print('Core imports work')"
  ```
- Test JioSaavn API dependency:
  ```bash
  python3 -c "from musicapy.saavn_api.api import SaavnAPI; api = SaavnAPI(); print('JioSaavn API available')"
  ```

### Known Issues and Compatibility
- **CRITICAL COMPATIBILITY ISSUE**: The plugin currently has import errors with beets 2.4.0
  - Current code: `from beets.autotag.hooks import Distance` (WRONG)
  - Correct import: `from beets.autotag.distance import Distance`
  - Current code: `from beets.plugins import get_distance` (WRONG - function not available)
  - Plugin will not load until these imports are fixed
- **Do not try to use the plugin without fixing imports first** - beets will show "Could not import plugin jiosaavn" error

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
- **Always fix the import statements before testing plugin functionality**
- Test plugin installation without dependencies (if deps already available):
  ```bash
  python3 -m pip install -e . --no-deps
  ```
  - Takes ~1 second, reinstalls if already present

### Validation Scenarios
After making changes, ALWAYS validate with these scenarios:

1. **Basic Plugin Loading**:
   ```bash
   python3 -c "from beets.autotag.distance import Distance; from beets.autotag.hooks import AlbumInfo, TrackInfo; print('Imports fixed')"
   ```
   - Should complete in ~0.17 seconds

2. **Plugin Instantiation** (after fixing imports):
   ```bash
   python3 -c "import sys; sys.path.insert(0, '.'); from beetsplug.jiosaavn import JioSaavnPlugin; plugin = JioSaavnPlugin(); print('Plugin creation successful')"
   ```

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
- **beets>=1.6.0** - Main music library management system
- **MusicAPy** - JioSaavn API wrapper (installed from GitHub)
- **requests** - HTTP requests for API calls
- **pillow** - Image processing for album art
- **Standard library**: collections, re, time, io

### Plugin Architecture
- Main class: `JioSaavnPlugin` extends `BeetsPlugin`
- Data source: "JioSaavn" 
- Implements beets plugin hooks:
  - `candidates()` - Album search results
  - `item_candidates()` - Track search results  
  - `album_for_id()` - Fetch album by JioSaavn URL
  - `track_for_id()` - Fetch track by JioSaavn URL
- Custom distance calculation for metadata matching
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
    'beets>=1.6.0',
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
beets version 2.4.0
Python version 3.12.3
plugins: musicbrainz
```

### Import statements that need fixing
Current (broken):
```python
from beets.autotag.hooks import AlbumInfo, Distance, TrackInfo
from beets.plugins import BeetsPlugin, get_distance
```

Corrected:
```python
from beets.autotag.distance import Distance
from beets.autotag.hooks import AlbumInfo, TrackInfo  
from beets.plugins import BeetsPlugin
# get_distance function usage needs to be replaced with direct distance calculation
```

## Troubleshooting

### Common Issues

1. **Import Error: Cannot import 'Distance' from 'beets.autotag.hooks'**
   - This is the primary compatibility issue with beets 2.4.0
   - Fix: Change import to `from beets.autotag.distance import Distance`

2. **Network timeout during installation**  
   - The MusicAPy dependency is cloned from GitHub and may timeout
   - Workaround: Install dependencies separately or use `--no-deps` flag

3. **Plugin shows as not loaded in beets**
   - Check for import errors in beets output
   - Fix import statements before expecting plugin to work

4. **"Could not import plugin jiosaavn" error**
   - This confirms the import compatibility issue
   - Plugin won't function until imports are corrected

### Performance Expectations
- Import validation: ~0.17 seconds
- JioSaavn API test: ~0.11 seconds  
- Full dependency check: ~0.12 seconds
- Plugin installation (no deps): ~1 second
- Initial installation with deps: 10 seconds - 5 minutes (depending on network)