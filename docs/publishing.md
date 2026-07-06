# Publishing

GroundGuard is prepared for PyPI Trusted Publishing.

## Local Build Check

```bash
python -m pip install -e ".[dev]"
python -m build
twine check dist/*
```

## GitHub Trusted Publishing

The repository includes `.github/workflows/publish.yml`. To complete PyPI
publishing:

1. Claim or create the `groundguard` project on PyPI.
2. Add a trusted publisher for this GitHub repository.
3. Publish a GitHub Release.
4. The workflow builds and publishes the package without storing a PyPI token.

