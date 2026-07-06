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

1. In the PyPI account `chasen2041`, open account-level **Publishing**.
2. Add a pending GitHub trusted publisher:
   - PyPI project: `groundguard-ai`
   - Owner: `chasen2041maker`
   - Repository name: `GroundGuard`
   - Workflow name: `publish.yml`
   - Environment name: leave blank for the current release workflow
3. Publish a GitHub Release for the matching version tag.
4. The workflow builds and publishes the package without storing a PyPI token.

`groundguard-ai` is the PyPI distribution name. The Python import package remains
`groundguard`.

If the workflow fails with `invalid-publisher`, the PyPI trusted publisher does
not match the claims in the GitHub Actions token yet. Fix the PyPI publisher
configuration, then re-run the failed `Publish Python Package` workflow.
