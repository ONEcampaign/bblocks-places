# Changelog

## v1.0.0 (in development)

- Stable release of the `bblocks-places` package

## v0.1.0 (in development)

- Initial minor release of the `bblocks-places` package for external testing

## v0.0.6 (2026-08-13)

- Deprecated the package in favour of [resolvekit](https://pypi.org/project/resolvekit/). This is the final release; `bblocks-places` will not receive further updates.
- Importing the package now raises a `DeprecationWarning` pointing to `resolvekit`.

## v0.0.5 (2026-02-09)

- Bug fix: resolving from known numeric entity type
- Added additional DAC codes to the concordance table

## v0.0.4 (2025-09-24)

- Updated concordance table income groupings

## v0.0.3 (2025-06-23)

- Bug fixes for handling of not found places
- Fix requests dependency
- Bug fix DCStatusError 500 - handle cases where an entity input is not valid
  for the resolve endpoint.

## v0.0.2 (2025-06-18)

- Set up GitHub Actions for CI/CD PYPI deployment

## v0.0.1 (2025-06-18)

- Test release to PyPI
