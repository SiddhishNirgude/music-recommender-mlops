"""
Recommender Service and Model Tests

Tests the core recommendation logic and model functionality
"""

import pytest
import pickle
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestModelLoading:
    """Test model file loading"""
    
    def test_model_file_exists(self, project_paths):
        """Model pickle file should exist"""
        model_path = project_paths["models"] / "als_model.pkl"
        assert model_path.exists(), f"Model not found at {model_path}"
    
    def test_user_factors_exist(self, project_paths):
        """User factors file should exist"""
        factors_path = project_paths["models"] / "user_factors.npy"
        assert factors_path.exists(), f"User factors not found at {factors_path}"
    
    def test_item_factors_exist(self, project_paths):
        """Item factors file should exist"""
        factors_path = project_paths["models"] / "item_factors.npy"
        assert factors_path.exists(), f"Item factors not found at {factors_path}"
    
    def test_model_loads_successfully(self, project_paths):
        """Model should load without errors"""
        model_path = project_paths["models"] / "als_model.pkl"
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        assert model is not None
    
    def test_user_factors_load_successfully(self, project_paths):
        """User factors should load as numpy array"""
        factors_path = project_paths["models"] / "user_factors.npy"
        user_factors = np.load(factors_path)
        
        assert isinstance(user_factors, np.ndarray)
        assert len(user_factors.shape) == 2  # Should be 2D array
    
    def test_item_factors_load_successfully(self, project_paths):
        """Item factors should load as numpy array"""
        factors_path = project_paths["models"] / "item_factors.npy"
        item_factors = np.load(factors_path)
        
        assert isinstance(item_factors, np.ndarray)
        assert len(item_factors.shape) == 2  # Should be 2D array


class TestModelDimensions:
    """Test model dimensions and shape"""
    
    def test_user_factors_shape(self, project_paths):
        """User factors should have correct dimensions"""
        factors_path = project_paths["models"] / "user_factors.npy"
        user_factors = np.load(factors_path)
        
        n_users, n_factors = user_factors.shape
        
        # Should have many users (100K+) and 100 factors
        assert n_users > 100000, f"Expected >100K users, got {n_users}"
        assert n_factors == 100, f"Expected 100 factors, got {n_factors}"
    
    def test_item_factors_shape(self, project_paths):
        """Item factors should have correct dimensions"""
        factors_path = project_paths["models"] / "item_factors.npy"
        item_factors = np.load(factors_path)
        
        n_items, n_factors = item_factors.shape
        
        # Should have many artists (100K+) and 100 factors
        assert n_items > 100000, f"Expected >100K artists, got {n_items}"
        assert n_factors == 100, f"Expected 100 factors, got {n_factors}"
    
    def test_factors_match(self, project_paths):
        """User and item factors should have same number of latent factors"""
        user_factors = np.load(project_paths["models"] / "user_factors.npy")
        item_factors = np.load(project_paths["models"] / "item_factors.npy")
        
        assert user_factors.shape[1] == item_factors.shape[1]


class TestRecommenderService:
    """Test RecommenderService class (if API is running)"""
    
    @pytest.fixture
    def recommender(self):
        """Create RecommenderService instance"""
        try:
            from src.api.recommender import RecommenderService
            return RecommenderService()
        except Exception as e:
            pytest.skip(f"Could not load RecommenderService: {e}")
    
    def test_recommender_initializes(self, recommender):
        """RecommenderService should initialize without errors"""
        assert recommender is not None
        assert recommender.model is not None
    
    def test_recommender_has_user_factors(self, recommender):
        """RecommenderService should have loaded user factors"""
        assert recommender.user_factors is not None
        assert isinstance(recommender.user_factors, np.ndarray)
    
    def test_recommender_has_item_factors(self, recommender):
        """RecommenderService should have loaded item factors"""
        assert recommender.item_factors is not None
        assert isinstance(recommender.item_factors, np.ndarray)
    
    def test_recommender_has_mappings(self, recommender):
        """RecommenderService should have loaded mappings"""
        assert recommender.user_mapping is not None
        assert recommender.artist_mapping is not None
        assert len(recommender.user_mapping) > 0
        assert len(recommender.artist_mapping) > 0


class TestRecommendationLogic:
    """Test recommendation generation logic"""
    
    @pytest.fixture
    def recommender(self):
        """Create RecommenderService instance"""
        try:
            from src.api.recommender import RecommenderService
            return RecommenderService()
        except Exception as e:
            pytest.skip(f"Could not load RecommenderService: {e}")
    
    def test_mood_recommendation_returns_results(self, recommender, sample_moods):
        """Mood recommendations should return results"""
        recs, seeds = recommender.get_recommendations_by_mood(sample_moods[0], k=10)
        
        assert len(recs) > 0
        assert len(seeds) > 0
        assert len(recs) <= 10
    
    def test_mood_recommendation_format(self, recommender, sample_moods):
        """Mood recommendations should be (artist_name, score) tuples"""
        recs, seeds = recommender.get_recommendations_by_mood(sample_moods[0], k=10)
        
        for artist, score in recs:
            assert isinstance(artist, str)
            assert isinstance(score, (int, float))
            assert score > 0
    
    def test_similar_artists_returns_results(self, recommender, sample_artists):
        """Similar artists should return results"""
        similar = recommender.get_similar_artists(sample_artists[0], k=10)
        
        assert len(similar) > 0
        assert len(similar) <= 10
    
    def test_similar_artists_format(self, recommender, sample_artists):
        """Similar artists should be (artist_name, similarity) tuples"""
        similar = recommender.get_similar_artists(sample_artists[0], k=10)
        
        for artist, similarity in similar:
            assert isinstance(artist, str)
            assert isinstance(similarity, (int, float))
            assert 0 <= similarity <= 1  # Cosine similarity range
    
    def test_top_charts_returns_results(self, recommender):
        """Top charts should return results"""
        charts = recommender.get_top_charts(k=20)
        
        assert len(charts) > 0
        assert len(charts) <= 20
    
    def test_top_charts_format(self, recommender):
        """Top charts should be (artist, plays, listeners) tuples"""
        charts = recommender.get_top_charts(k=20)
        
        for artist, plays, listeners in charts:
            assert isinstance(artist, str)
            assert isinstance(plays, (int, np.integer))
            assert isinstance(listeners, (int, np.integer))
            assert plays > 0
            assert listeners > 0
    
    def test_random_recommendations_returns_results(self, recommender):
        """Random recommendations should return results"""
        recs, user_id = recommender.get_random_recommendations(k=10)
        
        assert len(recs) > 0
        assert len(recs) <= 10
        assert user_id is not None


class TestMoodProfiles:
    """Test mood profile configuration"""
    
    def test_mood_profiles_import(self):
        """Should be able to import mood profiles"""
        try:
            from src.api.mood_profiles import MOOD_PROFILES
            assert MOOD_PROFILES is not None
        except ImportError:
            pytest.skip("Could not import mood_profiles")
    
    def test_mood_profiles_has_moods(self, sample_moods):
        """Mood profiles should contain expected moods"""
        from src.api.mood_profiles import MOOD_PROFILES
        
        for mood in sample_moods:
            assert mood in MOOD_PROFILES
    
    def test_mood_profile_structure(self):
        """Each mood profile should have required fields"""
        from src.api.mood_profiles import MOOD_PROFILES
        
        for mood_id, mood_info in MOOD_PROFILES.items():
            assert "name" in mood_info
            assert "description" in mood_info
            assert "seed_artists" in mood_info
            assert isinstance(mood_info["seed_artists"], list)
            assert len(mood_info["seed_artists"]) > 0
    
    def test_get_mood_seed_artists(self, sample_moods):
        """get_mood_seed_artists should return artist list"""
        from src.api.mood_profiles import get_mood_seed_artists
        
        seeds = get_mood_seed_artists(sample_moods[0])
        assert isinstance(seeds, list)
        assert len(seeds) > 0


class TestDataFiles:
    """Test data file integrity"""
    
    def test_config_file_exists(self, project_paths):
        """Config file should exist"""
        config_path = project_paths["configs"] / "config.yaml"
        assert config_path.exists()
    
    def test_user_mapping_exists(self, project_paths):
        """User mapping should exist (if not in gitignore)"""
        # Note: This file is large and may be gitignored
        mapping_path = project_paths["data"] / "processed" / "user_mapping.json"
        
        if mapping_path.exists():
            import json
            with open(mapping_path, 'r') as f:
                mapping = json.load(f)
            assert len(mapping) > 0
    
    def test_artist_mapping_exists(self, project_paths):
        """Artist mapping should exist (if not in gitignore)"""
        # Note: This file is large and may be gitignored
        mapping_path = project_paths["data"] / "processed" / "artist_mapping.json"
        
        if mapping_path.exists():
            import json
            with open(mapping_path, 'r') as f:
                mapping = json.load(f)
            assert len(mapping) > 0


# Mark all tests as model tests
pytestmark = pytest.mark.model
