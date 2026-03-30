# shiboru

A macOS command-line image optimizer. Supports PNG, JPEG, GIF, SVG, and ICO.

By Thomas Marban: https://thomas.me

> **shiboru** (絞る) — Japanese for "to squeeze"

---

## Install

```bash
brew tap marban/shiboru
brew install shiboru
```

Upgrade:

```bash
brew upgrade shiboru
```

---

## Usage

```bash
shiboru logo.png
shiboru logo.png hero.jpg icon.ico
shiboru assets/ --recursive
shiboru assets/ --recursive --replace
shiboru assets/ --recursive --suffix=-min
shiboru assets/ --dry-run
```

By default, optimized copies are written next to the originals with `-optimized` inserted before the extension:

```
logo.png        →  logo-optimized.png
hero.jpg        →  hero-optimized.jpg
assets/icon.svg →  assets/icon-optimized.svg
```

---

## Output modes

### Suffix mode (default)

Writes an optimized copy alongside the original. The original is never touched.

```bash
shiboru logo.png
# produces: logo-optimized.png

shiboru logo.png --suffix=-min
# produces: logo-min.png
```

If the destination already exists, a counter is appended:

```
logo-optimized.png
logo-optimized-2.png
logo-optimized-3.png
```

### Replace mode

Overwrites the original in-place using a safe atomic replacement. The optimized
file is written to a temporary path first, validated, then swapped in. The
original is only removed once the replacement is confirmed readable.

```bash
shiboru logo.png --replace
shiboru assets/ --recursive --replace
```

---

## Supported formats

| Format | Optimizer     |
|--------|---------------|
| PNG    | oxipng        |
| JPEG   | jpegoptim     |
| GIF    | gifsicle      |
| SVG    | scour         |
| ICO    | oxipng (embedded PNG frames) |

Files that are already fully optimized are reported as `unchanged` and left
untouched.

---

## Flags

```
PATH [PATH ...]     Files or directories to optimize.

--replace           Replace originals in-place (safe atomic replacement).
--suffix VALUE      Suffix before the extension on output files (default: -optimized).
--recursive, -r     Recurse into directories.
--quiet, -q         Suppress per-file output; show only the summary.
--verbose, -v       Show additional diagnostic information.
--dry-run, -n       Report intended actions without writing any files.
--formats LIST      Comma-separated formats to process: png, jpg, jpeg, gif, svg, ico.
--include-hidden    Include hidden files and directories when scanning.
--version           Show version and exit.
--help              Show help and exit.

Environment variable overrides for helper tool paths:
  SHIBORU_OXIPNG_PATH, SHIBORU_JPEGOPTIM_PATH, SHIBORU_GIFSICLE_PATH
```

---

## Example output

```
logo.png                                  PNG     124.0 KB -> 91.2 KB    -26.5%
hero.jpg                                  JPEG    812.0 KB -> 701.4 KB   -13.6%
icon.ico                                  ICO      18.0 KB -> 11.3 KB    -37.2%
chart.svg                                 SVG      41.0 KB -> 29.1 KB    -29.0%
badge.png                                 PNG       4.1 KB               (unchanged)

5 files processed
4 optimized, 1 unchanged, 0 failed
Total saved: 162.9 KB
```

---

## Dry run

Use `--dry-run` to preview what would happen without writing anything:

```bash
shiboru assets/ --recursive --dry-run
```

```
assets/logo.png     PNG    124.0 KB  -> assets/logo-optimized.png    [dry run]
assets/hero.jpg     JPEG   812.0 KB  -> assets/hero-optimized.jpg    [dry run]
```

---

## Troubleshooting

### A format shows "helper tool not found"

Each format relies on a helper tool installed by Homebrew. If one is missing,
reinstall the package:

```bash
brew reinstall shiboru
```

If the issue persists, install the missing tool directly:

```bash
brew install oxipng      # PNG and ICO
brew install jpegoptim   # JPEG
brew install gifsicle    # GIF
```

SVG optimization uses `scour`, which is a Python library bundled with `shiboru`
— no separate install required. By default, `shiboru` strips comments and
descriptive SVG elements such as `<metadata>`, `<title>`, and `<desc>`.

### Apple Silicon vs Intel

`shiboru` supports both architectures. Homebrew installs to `/opt/homebrew` on
Apple Silicon and `/usr/local` on Intel. The tool detects both automatically.

### Repeated runs

Running `shiboru` more than once on the same file is safe. Already-optimized
files are detected and reported as `unchanged` without being rewritten.

---

## Exit codes

| Code | Meaning                          |
|------|----------------------------------|
| 0    | All work completed successfully  |
| 1    | One or more files failed         |
| 2    | Bad arguments or usage error     |

---

## License

MIT. See [LICENSE](LICENSE).  
Copyright (c) 2025 Thomas Marban

Helper tools (oxipng, jpegoptim, gifsicle) are separate Homebrew packages with
their own licenses. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
