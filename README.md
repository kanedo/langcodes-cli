# langcodes oh-my-zsh plugin

This plugin adds a `langcode` helper (with a shorter `lc` alias) for exploring language metadata using the [`langcodes`](https://pypi.org/project/langcodes/) Python library. It understands both BCP 47 tags and English language names, reports the canonical tag, describes the language, surfaces the likely writing system, and highlights closely related tags.

## Requirements

- [oh-my-zsh](https://ohmyz.sh/) with custom plugins enabled.
- [`uv`](https://github.com/astral-sh/uv) available on your `PATH`. The helper script is executed via `uv run --script`, which will automatically download the `langcodes` dependency into uv's cache the first time you use it.


## Installation

1. Clone or copy this repository into your oh-my-zsh custom plugins directory:
   ```bash
   git clone https://github.com/<your-user>/langcodes-cli.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/langcodes
   ```
2. Enable the plugin by adding `langcodes` to the `plugins=(...)` array in your `~/.zshrc`.
3. Reload your shell configuration:
   ```bash
   source ~/.zshrc
   ```

After reloading, the `langcode` function and `lc` alias become available in every new shell session.

## Usage

```
langcode QUERY
langcode --simple QUERY
lc QUERY             # alias for langcode
```

- `QUERY` can be a BCP 47 tag (`es-MX`, `zh-Hant`), an ISO code (`eng`), or an English name (`"Brazilian Portuguese"`).
- `--simple` prints a single line description and is handy for scripts or prompts.

### Examples

```bash
$ langcode es-MX
Tag: es-MX
Name: {'language': 'Spanish', 'territory': 'Mexico'}
Likely script: Latn
Identical or near-identical codes:
  - es-Latn-MX: Spanish (Mexico)

$ langcode "Swiss German"
Tag: gsw
Name: {'language': 'Swiss German'}
Likely script: Latn
Identical or near-identical codes:
  - gsw-CH: Swiss German (Switzerland)
  - gsw-Latn-CH: Swiss German (Switzerland)
  - gsw-Latn: Swiss German
```

Run `langcode --help` to see the full flag reference. The script lives at `inspect_langcodes.py` and can be executed directly if you prefer.
