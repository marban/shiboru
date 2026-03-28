# Releasing

---

## Dependencies

Before running any of the commands below, install:

```sh
brew install oxipng jpegoptim gifsicle
```

---

## Versioning

This project follows [Semantic Versioning](https://semver.org/).

- Start at `0.1.0`.
- Increment the **patch** version for bug fixes and minor improvements.
- Increment the **minor** version for new features that do not break existing
  behaviour.
- Reserve **1.0.0** for the first stable, production-ready release.

Version is declared in exactly two places. Both must be updated together:

1. `pyproject.toml` — `version = "x.y.z"`
2. `src/shiboru/__init__.py` — `__version__ = "x.y.z"`

---

## Release workflow

### 1. Prepare the release commit

Update the version in both files listed above, then commit:

```sh
git add pyproject.toml src/shiboru/__init__.py
git commit -m "chore: release v0.x.0"
```

### 2. Tag the release

```sh
git tag -a v0.x.0 -m "Release v0.x.0"
git push origin main --tags
```

GitHub will automatically generate a source archive for the tag at:

```
https://github.com/marban/shiboru/archive/refs/tags/v0.x.0.tar.gz
```

### 3. Compute the release archive SHA256

Download the archive that GitHub generated and hash it:

```sh
curl -sL https://github.com/marban/shiboru/archive/refs/tags/v0.x.0.tar.gz \
  -o release.tar.gz
shasum -a 256 release.tar.gz
```

Keep this hash — it goes into the formula in the next step.

### 4. Update the tap formula

The tap lives in a separate repository named `homebrew-shiboru` under the same
GitHub account. Open `Formula/shiboru.rb` and update:

```ruby
url "https://github.com/marban/shiboru/archive/refs/tags/v0.x.0.tar.gz"
sha256 "PASTE_HASH_HERE"
```

Commit and push the tap repository:

```sh
git add Formula/shiboru.rb
git commit -m "shiboru 0.x.0"
git push origin main
```

### 5. Test the install from the tap

On a clean machine (or in a separate shell with no active virtualenv):

```sh
brew tap marban/shiboru
brew install shiboru
shiboru --version
shiboru --help
```

If anything fails, fix it, bump the patch version, and repeat from step 1.

### 6. Publish release notes on GitHub

Open the GitHub release that was created automatically when you pushed the tag,
add a short description of what changed, and publish it.

---

## Creating the tap repository (first time only)

1. Create a new public GitHub repository named `homebrew-shiboru` under the
   `marban` account.
2. Copy `packaging/brew/Formula/shiboru.rb` into `Formula/shiboru.rb` in that
   repository.
3. Push to `main`.
4. Verify: `brew tap marban/shiboru` should succeed.

The tap repository and the main application repository are kept separate. The
formula in `packaging/brew/Formula/` in this repository is the source of truth;
copy it into the tap repo on each release.

---

## Updating Python dependencies in the formula

The Homebrew formula pins `scour` with an explicit URL and SHA256. When `scour`
releases a new version:

1. Find the new sdist URL on [PyPI](https://pypi.org/project/scour/#files).
2. Compute its SHA256:
   ```sh
   curl -sL <url> | shasum -a 256
   ```
3. Update the `resource "scour"` block in the formula.
4. Test locally with `brew install --build-from-source Formula/shiboru.rb`.
5. Release as normal (bump patch version, new tag, update tap).

---

## Required CI checks before any release

All of the following must pass on macOS:

- [ ] `pytest tests/unit` — full unit test suite
- [ ] `shiboru --version` — prints the correct version
- [ ] `shiboru --help` — exits cleanly
- [ ] `shiboru path/to/fixture.png --dry-run` — runs without error
- [ ] `brew install --build-from-source Formula/shiboru.rb` — installs cleanly
- [ ] `brew test shiboru` — formula test block passes