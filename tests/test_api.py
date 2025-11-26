"""
API Endpoint Tests

Tests all FastAPI endpoints for proper functionality
"""

import pytest
import requests
from requests.exceptions import RequestException


class TestAPIHealth:
    """Test /health endpoint"""
    
    def test_health_endpoint_returns_200(self, test_config):
        """Health endpoint should return 200 OK"""
        response = requests.get(
            f"{test_config['api_url']}/health",
            timeout=test_config['timeout']
        )
        assert response.status_code == 200
    
    def test_health_response_has_status(self, test_config):
        """Health response should contain status field"""
        response = requests.get(
            f"{test_config['api_url']}/health",
            timeout=test_config['timeout']
        )
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_response_has_model_info(self, test_config):
        """Health response should contain model information"""
        response = requests.get(
            f"{test_config['api_url']}/health",
            timeout=test_config['timeout']
        )
        data = response.json()
        assert "model_loaded" in data
        assert "model_info" in data
        assert data["model_loaded"] is True


class TestRecommendEndpoint:
    """Test /recommend endpoint"""
    
    def test_mood_recommendation_returns_200(self, test_config, sample_moods):
        """Mood recommendation should return 200 OK"""
        response = requests.post(
            f"{test_config['api_url']}/recommend",
            json={
                "type": "mood",
                "mood": sample_moods[0],
                "k": 10
            },
            timeout=test_config['timeout']
        )
        assert response.status_code == 200
    
    def test_mood_recommendation_returns_correct_count(self, test_config, sample_moods):
        """Mood recommendation should return requested number of items"""
        k = 5
        response = requests.post(
            f"{test_config['api_url']}/recommend",
            json={
                "type": "mood",
                "mood": sample_moods[0],
                "k": k
            },
            timeout=test_config['timeout']
        )
        data = response.json()
        assert len(data["recommendations"]) <= k
    
    def test_mood_recommendation_has_required_fields(self, test_config, sample_moods):
        """Mood recommendation items should have artist_name, score, rank"""
        response = requests.post(
            f"{test_config['api_url']}/recommend",
            json={
                "type": "mood",
                "mood": sample_moods[0],
                "k": 10
            },
            timeout=test_config['timeout']
        )
        data = response.json()
        
        assert "recommendations" in data
        assert "type" in data
        assert "metadata" in data
        
        if len(data["recommendations"]) > 0:
            first_rec = data["recommendations"][0]
            assert "artist_name" in first_rec
            assert "score" in first_rec
            assert "rank" in first_rec
            assert first_rec["rank"] == 1
    
    def test_random_recommendation_returns_200(self, test_config):
        """Random recommendation should return 200 OK"""
        response = requests.post(
            f"{test_config['api_url']}/recommend",
            json={
                "type": "random",
                "k": 10
            },
            timeout=test_config['timeout']
        )
        assert response.status_code == 200
    
    def test_random_recommendation_returns_results(self, test_config):
        """Random recommendation should return some recommendations"""
        response = requests.post(
            f"{test_config['api_url']}/recommend",
            json={
                "type": "random",
                "k": 10
            },
            timeout=test_config['timeout']
        )
        data = response.json()
        assert len(data["recommendations"]) > 0
    
    def test_invalid_mood_returns_404(self, test_config):
        """Invalid mood should return 404"""
        response = requests.post(
            f"{test_config['api_url']}/recommend",
            json={
                "type": "mood",
                "mood": "nonexistent_mood_xyz",
                "k": 10
            },
            timeout=test_config['timeout']
        )
        assert response.status_code == 404
    
    def test_missing_mood_returns_400(self, test_config):
        """Missing mood parameter should return 400"""
        response = requests.post(
            f"{test_config['api_url']}/recommend",
            json={
                "type": "mood",
                "k": 10
            },
            timeout=test_config['timeout']
        )
        assert response.status_code == 400


class TestSimilarEndpoint:
    """Test /similar endpoint"""
    
    def test_similar_artists_returns_200(self, test_config, sample_artists):
        """Similar artists endpoint should return 200 OK"""
        response = requests.post(
            f"{test_config['api_url']}/similar",
            json={
                "artist_name": sample_artists[0],
                "k": 10
            },
            timeout=test_config['timeout']
        )
        assert response.status_code == 200
    
    def test_similar_artists_returns_results(self, test_config, sample_artists):
        """Similar artists should return some results"""
        response = requests.post(
            f"{test_config['api_url']}/similar",
            json={
                "artist_name": sample_artists[0],
                "k": 10
            },
            timeout=test_config['timeout']
        )
        data = response.json()
        assert "query_artist" in data
        assert "similar_artists" in data
        assert len(data["similar_artists"]) > 0
    
    def test_similar_artists_has_correct_fields(self, test_config, sample_artists):
        """Similar artists items should have required fields"""
        response = requests.post(
            f"{test_config['api_url']}/similar",
            json={
                "artist_name": sample_artists[0],
                "k": 10
            },
            timeout=test_config['timeout']
        )
        data = response.json()
        
        if len(data["similar_artists"]) > 0:
            first_artist = data["similar_artists"][0]
            assert "artist_name" in first_artist
            assert "score" in first_artist
            assert "rank" in first_artist
            assert 0 <= first_artist["score"] <= 1  # Cosine similarity range
    
    def test_similar_artists_excludes_query_artist(self, test_config, sample_artists):
        """Similar artists should not include the query artist itself"""
        query_artist = sample_artists[0]
        response = requests.post(
            f"{test_config['api_url']}/similar",
            json={
                "artist_name": query_artist,
                "k": 10
            },
            timeout=test_config['timeout']
        )
        data = response.json()
        
        similar_names = [a["artist_name"] for a in data["similar_artists"]]
        assert query_artist not in similar_names
    
    def test_invalid_artist_returns_404(self, test_config):
        """Invalid artist name should return 404"""
        response = requests.post(
            f"{test_config['api_url']}/similar",
            json={
                "artist_name": "nonexistent_artist_xyz_12345",
                "k": 10
            },
            timeout=test_config['timeout']
        )
        assert response.status_code == 404


class TestChartsEndpoint:
    """Test /charts endpoint"""
    
    def test_charts_returns_200(self, test_config):
        """Charts endpoint should return 200 OK"""
        response = requests.get(
            f"{test_config['api_url']}/charts",
            timeout=test_config['timeout']
        )
        assert response.status_code == 200
    
    def test_charts_returns_results(self, test_config):
        """Charts should return some results"""
        response = requests.get(
            f"{test_config['api_url']}/charts?k=20",
            timeout=test_config['timeout']
        )
        data = response.json()
        assert "charts" in data
        assert len(data["charts"]) > 0
    
    def test_charts_respects_k_parameter(self, test_config):
        """Charts should return requested number of items"""
        k = 5
        response = requests.get(
            f"{test_config['api_url']}/charts?k={k}",
            timeout=test_config['timeout']
        )
        data = response.json()
        assert len(data["charts"]) <= k
    
    def test_charts_items_have_required_fields(self, test_config):
        """Chart items should have artist_name, play_count, listener_count, rank"""
        response = requests.get(
            f"{test_config['api_url']}/charts",
            timeout=test_config['timeout']
        )
        data = response.json()
        
        if len(data["charts"]) > 0:
            first_item = data["charts"][0]
            assert "artist_name" in first_item
            assert "play_count" in first_item
            assert "listener_count" in first_item
            assert "rank" in first_item
            assert first_item["rank"] == 1
    
    def test_charts_sorted_by_play_count(self, test_config):
        """Charts should be sorted by play count descending"""
        response = requests.get(
            f"{test_config['api_url']}/charts?k=10",
            timeout=test_config['timeout']
        )
        data = response.json()
        
        if len(data["charts"]) > 1:
            play_counts = [item["play_count"] for item in data["charts"]]
            assert play_counts == sorted(play_counts, reverse=True)


class TestMoodsEndpoint:
    """Test /moods endpoint"""
    
    def test_moods_returns_200(self, test_config):
        """Moods endpoint should return 200 OK"""
        response = requests.get(
            f"{test_config['api_url']}/moods",
            timeout=test_config['timeout']
        )
        assert response.status_code == 200
    
    def test_moods_returns_moods_dict(self, test_config):
        """Moods endpoint should return moods dictionary"""
        response = requests.get(
            f"{test_config['api_url']}/moods",
            timeout=test_config['timeout']
        )
        data = response.json()
        assert "moods" in data
        assert isinstance(data["moods"], dict)
    
    def test_moods_has_required_moods(self, test_config, sample_moods):
        """Moods endpoint should include expected moods"""
        response = requests.get(
            f"{test_config['api_url']}/moods",
            timeout=test_config['timeout']
        )
        data = response.json()
        
        for mood in sample_moods:
            assert mood in data["moods"]
    
    def test_mood_info_has_required_fields(self, test_config):
        """Each mood should have name, description, seed_artists"""
        response = requests.get(
            f"{test_config['api_url']}/moods",
            timeout=test_config['timeout']
        )
        data = response.json()
        
        for mood_id, mood_info in data["moods"].items():
            assert "name" in mood_info
            assert "description" in mood_info
            assert "seed_artists" in mood_info
            assert isinstance(mood_info["seed_artists"], list)
            assert len(mood_info["seed_artists"]) > 0


class TestAPIErrors:
    """Test API error handling"""
    
    def test_invalid_endpoint_returns_404(self, test_config):
        """Invalid endpoint should return 404"""
        response = requests.get(
            f"{test_config['api_url']}/invalid_endpoint_xyz",
            timeout=test_config['timeout']
        )
        assert response.status_code == 404
    
    def test_invalid_method_returns_405(self, test_config):
        """Invalid HTTP method should return 405"""
        response = requests.get(
            f"{test_config['api_url']}/recommend",  # Should be POST
            timeout=test_config['timeout']
        )
        assert response.status_code == 405


# Test markers examples
pytestmark = pytest.mark.api
