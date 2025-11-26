"""
Pytest configuration and shared fixtures
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_paths():
    """Project directory paths"""
    root = Path(__file__).parent.parent
    return {
        "root": root,
        "src": root / "src",
        "models": root / "models",
        "data": root / "data",
        "configs": root / "configs"
    }


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "api_url": "http://localhost:8000",
        "timeout": 30,
        "max_recommendations": 10
    }


@pytest.fixture(scope="session")
def sample_moods():
    """Sample mood names for testing"""
    return ["heartbreak", "party", "chill", "rock", "jazz"]


@pytest.fixture(scope="session")
def sample_artists():
    """Sample artist names for testing"""
    return ["radiohead", "the beatles", "coldplay", "pink floyd", "muse"]
