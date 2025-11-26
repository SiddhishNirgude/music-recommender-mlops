# GitHub Actions Workflows

This directory contains CI/CD workflows for the Music Recommender MLOps project.

## Workflows

### 1. CI/CD Pipeline (`ci.yml`)

**Triggers:** Push to main/develop, Pull Requests

**Jobs:**
- **Code Quality:** Black, isort, flake8 checks
- **Unit Tests:** Runs non-API tests (model loading, mood profiles)
- **Docker Build:** Validates Dockerfile syntax and docker-compose config
- **Security Scan:** Checks for vulnerable dependencies with Safety
- **Summary:** Overall pipeline status

**Runtime:** ~5-8 minutes

### 2. Code Linting (`lint.yml`)

**Triggers:** Push/PR with Python file changes

**Jobs:**
- Black (code formatting)
- isort (import sorting)
- Flake8 (PEP 8 compliance)
- Pylint (deep code analysis)

**Runtime:** ~3-5 minutes

## Status Badges

Add to your README.md:

```markdown
![CI/CD Pipeline](https://github.com/SiddhishNirgude/music-recommender-mlops/workflows/CI/CD%20Pipeline/badge.svg)
![Code Linting](https://github.com/SiddhishNirgude/music-recommender-mlops/workflows/Code%20Linting/badge.svg)
```

## Notes

### Why Some Tests Are Skipped in CI

The CI environment doesn't have:
- Trained models (185 MB)
- Processed data (1.8 GB)
- Running API server

Therefore, we only run:
- ✅ Code quality checks
- ✅ Unit tests that don't require models
- ✅ Configuration validation
- ⏭️ Skip: API endpoint tests (require running server)
- ⏭️ Skip: Full model tests (require trained model)

### Running Full Tests Locally

To run all tests (including API tests):

```bash
# Start API
bash scripts/start_api.sh

# In another terminal
pytest -v
```

### Future Improvements

1. **Add DVC Pull:** Download models from S3 in CI
2. **Docker Hub Push:** Push built images to Docker Hub
3. **Deploy to Staging:** Auto-deploy to test environment
4. **Coverage Reports:** Generate and publish test coverage
5. **Performance Tests:** Add load testing with Locust

## Troubleshooting

### Workflow Fails on First Run

This is normal! First run might fail due to:
- Missing linting tools (auto-installed)
- Code formatting issues (run `black src/ tests/`)
- Import sorting (run `isort src/ tests/`)

### How to Fix Linting Issues

```bash
# Auto-format code
black src/ tests/

# Auto-sort imports
isort src/ tests/

# Check for remaining issues
flake8 src/ tests/ --max-line-length=127
```

### Secrets Required (Future)

When adding advanced features, you'll need to add these secrets in GitHub Settings:

- `AWS_ACCESS_KEY_ID` - For DVC pull from S3
- `AWS_SECRET_ACCESS_KEY` - For DVC pull from S3
- `DOCKERHUB_USERNAME` - For pushing Docker images
- `DOCKERHUB_TOKEN` - For Docker Hub authentication

## Viewing Results

1. Go to your GitHub repository
2. Click "Actions" tab
3. Select a workflow run
4. View logs and test results

Lint results are also saved as artifacts (downloadable for 30 days).
