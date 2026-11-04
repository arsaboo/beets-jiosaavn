# beets-jiosaavn
A plugin for [beets](https://github.com/beetbox/beets) to use JioSaavn as a metadata source.

## Installation

Install the plugin using `pip`:

```shell
pip install git+https://github.com/arsaboo/beets-jiosaavn.git
```

Then, [configure](#configuration) the plugin in your
[`config.yaml`](https://beets.readthedocs.io/en/latest/plugins/index.html) file.

## Configuration

Add `jiosaavn` to your list of enabled plugins.

```yaml
plugins: jiosaavn

jiosaavn:
  data_source_mismatch_penalty: 0.5
```

### Configuration Options

- **data_source_mismatch_penalty** (default: 0.5): Penalty applied when the metadata source doesn't match JioSaavn during autotagging. Lower values increase JioSaavn's priority.
