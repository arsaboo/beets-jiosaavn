# beets-jiosaavn
A plugin for [beets](https://github.com/beetbox/beets) to use JioSaavn as a metadata source.

## Requirements

- beets >= 2.10.0 — the plugin implements the metadata source interface from
  `beets.metadata_plugins` (`SearchApiMetadataSourcePlugin`).

## Installation

Install the plugin using `pip`:

```shell
pip install git+https://github.com/arsaboo/beets-jiosaavn.git
```

To pick up changes later, use `--force-reinstall`: the package version does not
change on every commit, so a plain `pip install -U` silently keeps the old copy.

```shell
pip install --force-reinstall --no-deps git+https://github.com/arsaboo/beets-jiosaavn.git
```

Then, [configure](#configuration) the plugin in your
[`config.yaml`](https://beets.readthedocs.io/en/latest/plugins/index.html) file.

## Configuration

Add `jiosaavn` to your list of enabled plugins.

```yaml
plugins: jiosaavn

jiosaavn:
  data_source_mismatch_penalty: 0.5
  search_limit: 5
```

### Configuration Options

- **data_source_mismatch_penalty** (default: 0.5): Penalty applied when the metadata source doesn't match JioSaavn during autotagging. Lower values increase JioSaavn's priority. (`source_weight` in beets < 2.10.)
- **search_limit** (default: 5): Maximum number of albums or tracks to resolve per search. Each result costs at least one extra API call, so lower values make imports noticeably faster.
- **search_query_ascii** (default: no): Transliterate the search query to ASCII before searching.

Both options are shared with beets' own metadata sources (Spotify, Deezer,
Tidal, ...), so a value set for one source can be reused here.
