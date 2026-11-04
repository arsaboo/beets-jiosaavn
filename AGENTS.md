# beets-jiosaavn - Project Context

Canonical agent brief for this repository. `AGENTS.md` is gitignored on purpose:
it is a working brief, not published documentation (the user-facing docs are
`README.md`).

## Environment

- **Local**: Windows, conda env `py311` — `conda run -n py311 ...`. Never install
  packages into `base`, never create a new venv.
- **Lint**: `conda run -n py311 python -m black beetsplug setup.py` and
  `conda run -n py311 python -m flake8 beetsplug setup.py`. 88 columns, pinned in
  `pyproject.toml` (Black) and `setup.cfg` (flake8); Black keeps the existing
  single quotes via `skip-string-normalization`.
- **No test suite, no CI** — validation is the live checklist below.
- **Remote for live checks**: `ssh arsaboo@arsmusic`. No conda there; use the venv
  at `/home/arsaboo/.venvs/beets` (beets 2.14.1, Python 3.13.18), CLI
  `/home/arsaboo/.venvs/beets/bin/beet`, config `~/.config/beets/config.yaml`,
  library `/data/music` (`~/.config/beets/musiclibrary.blb`).
- **Deploy**: push `main`, then on arsmusic
  `/home/arsaboo/.venvs/beets/bin/pip install --force-reinstall --no-deps git+https://github.com/arsaboo/beets-jiosaavn.git`.
  The package version stays `0.1`, so plain `-U` silently no-ops. Confirm with
  `md5sum` of the installed `beetsplug/jiosaavn.py` vs `git show HEAD:beetsplug/jiosaavn.py | md5sum`
  (compare the blob, not the CRLF working copy).
- **Test uncommitted code remotely** without deploying: copy the file to
  `/tmp/x/beetsplug/` and run with `PYTHONPATH=/tmp/x` — `beetsplug` is a
  namespace package, so the local copy shadows site-packages.

## Project Overview

beets plugin (`JioSaavnPlugin`) that adds JioSaavn as an autotagging metadata
source, built on MusicAPy.

- Text search for albums/tracks, album/track lookup by JioSaavn URL
- Flexible fields: `jiosaavn_album_id`, `jiosaavn_artist_id`, `jiosaavn_track_id`,
  `jiosaavn_starring`, `jiosaavn_perma_url`, `jiosaavn_updated`, `cover_art_url`
- No CLI commands, no events, no distance hooks

## Validation checklist

1. **Strict import** (must print nothing but your own output):
   `python -W error::DeprecationWarning -c "import beetsplug.jiosaavn"`
2. **Contract** — instantiate and print `data_source` (must be `JioSaavn`,
   derived from the class name), `data_source_mismatch_penalty`,
   `config["search_limit"]`, `config["search_query_ascii"]`, and
   `__abstractmethods__` (must be empty).
3. **Live source smoke test** against the real API: `candidates()`,
   `item_candidates()`, `album_for_id()` with a JioSaavn URL and with a Spotify
   URL / MusicBrainz UUID (both must return `None` without a request).
4. **Real autotag in a throwaway library** (`directory`, `library`,
   `plugins: jiosaavn`, `import: {write: no, copy: no, move: no}`), then
   `beet -c cfg.yaml -v import -q -W -C <album dir>`, plus `-S <jiosaavn url>`
   (id path) and `-s <file>` (singleton path). Grep the log for
   `Error in 'JioSaavn`, `Error searching JioSaavn`, `Traceback`.
   **`beet import --pretend` proves nothing here**: `importer/session.py`
   short-circuits in pretend mode and never calls metadata sources.
   Never run a non-pretend import against the real config/library.

## Critical Constraints

- **Do not rename flexible attributes** or change `data_source` (`"JioSaavn"`):
  existing library rows, `match.preferred.data_source` weights and other
  plugins' queries depend on them.
- **Do not reintroduce the legacy pattern** (`BeetsPlugin` + hand-written
  `data_source`, `source_weight`, plugin-side `get_distance()`/`add_identity()`).
  The compatibility shim is removed in beets 3.0, and beets computes the source
  mismatch penalty centrally (`Distance.add_data_source()` →
  `metadata_plugins.get_penalty()`).
- **`search_limit` must be applied client-side.** JioSaavn accepts but ignores
  MusicAPy's `limit`. Every album hit costs a details request, which itself
  resolves every track (N+1), so keep the candidate count small.
- **MusicAPy is unreliable to call**: sets no socket timeouts, returns `False`
  for non-2xx, and raises for network/JSON/payload problems. Wrap lookups so one
  dead link skips one candidate (honour `config['raise_on_error']`), and give our
  own `requests` calls a timeout.
- Keep the `REIMPORT_FRESH_FIELDS_ITEM` extension (documented beets extension
  point, and idempotent). Note that arsmusic's installed
  `beets/metadata_plugins.py` carries a local hand-edit vs the 2.14.1 release
  (extra `requests` exception clause in `_search_api`) which will vanish on the
  next beets upgrade — the plugin must not depend on it.
- Nothing imports `beetsplug.jiosaavn` today (`beets-plexsync` and `arscustom`
  keep their own copies of similar code), but keep public method names stable.
- **No AI attribution** in commits, PRs or comments — no `Co-authored-by:`, no
  "Generated with", never copy a trailer from history.
- Commit style: single-line imperative subject matching existing history.
  Files are LF in the repo (`.gitattributes`, `core.autocrlf=true` locally).

## Config options

```yaml
jiosaavn:
  data_source_mismatch_penalty: 0.5   # `source_weight` in beets < 2.10
  search_limit: 5                     # candidates resolved per search
  search_query_ascii: no             # transliterate query to ASCII
```
All three are shared with beets' own sources and have defaults in
`MetadataSourcePlugin.__init__`, so the plugin does not re-declare them.

## Code map

```
beetsplug/jiosaavn.py
├── extend_reimport_fresh_fields_item()   # reimport freshness
├── to_int()                            # JioSaavn returns numbers as strings
├── JioSaavnSearchHit(IDResponse)       # id + release type
└── JioSaavnPlugin(SearchApiMetadataSourcePlugin)
    ├── get_search_query_with_filters() # free-text query, VA drops artist
    ├── get_search_response()         # MusicAPy search -> {"id": perma_url, "type": ...}
    ├── candidates()                  # only override: keeps the release type
    ├── album_for_id() / track_for_id()  # URL-guarded id lookups
    ├── get_album_info() / _get_track() # payload -> AlbumInfo / TrackInfo
    └── _get_details() / is_valid_image_url()
```

## Payload gotchas

- Album **details** carry no release type and no label: `albumtype` comes from the
  search hit, `label` from `songs[0]["label"]`.
- `get_song_details()` already unwraps `songs[0]`; some responses still wrap.
- Cover art: upgrade `150x150` → `500x500` and verify it decodes before offering.
- Song `duration` may be a string, an int, or only present under `more_info`;
  instrumentals have empty `singers` (fall back to `music`).
- JioSaavn throttles: an import running concurrently on arsmusic can make remote
  lookups minutes slower. Timeouts under load are environmental — re-run before
  blaming the code.

## Dependencies (key)

`beets>=2.10.0` (where `beets.metadata_plugins`, `IDResponse`, `search_limit` and
`data_source_mismatch_penalty` first appear), `MusicAPy` (git), `requests`,
`pillow`.
