"""
Recommender Service
Wraps the trained ALS model and provides recommendation logic
"""

import pickle
import json
import numpy as np
import pandas as pd
from scipy.sparse import load_npz
from pathlib import Path
from typing import List, Tuple, Optional
import logging
from sklearn.metrics.pairwise import cosine_similarity

from .mood_profiles import get_mood_seed_artists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommenderService:
    """Service for generating recommendations using trained ALS model"""
    
    def __init__(self, model_dir: str = "models", data_dir: str = "data/processed"):
        """
        Initialize recommender service
        
        Args:
            model_dir: Directory containing trained model
            data_dir: Directory containing processed data
        """
        self.model_dir = Path(model_dir)
        self.data_dir = Path(data_dir)
        
        # Model and data
        self.model = None
        self.user_factors = None
        self.item_factors = None
        self.user_mapping = None
        self.artist_mapping = None
        self.reverse_user_mapping = None
        self.reverse_artist_mapping = None
        self.train_matrix = None
        self.train_data = None
        
        # Load everything
        self._load_model()
        self._load_mappings()
        self._load_data()
        
        logger.info("✅ Recommender service initialized successfully")
    
    def _load_model(self):
        """Load trained model and factors"""
        logger.info("Loading model...")
        
        # Load model
        model_path = self.model_dir / "als_model.pkl"
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        
        # Load factors
        self.user_factors = np.load(self.model_dir / "user_factors.npy")
        self.item_factors = np.load(self.model_dir / "item_factors.npy")
        
        logger.info(f"Model loaded: {self.user_factors.shape[0]} users, {self.item_factors.shape[0]} artists")
    
    def _load_mappings(self):
        """Load ID mappings"""
        logger.info("Loading mappings...")
        
        with open(self.data_dir / "user_mapping.json", 'r') as f:
            self.user_mapping = json.load(f)
        
        with open(self.data_dir / "artist_mapping.json", 'r') as f:
            self.artist_mapping = json.load(f)
        
        # Create reverse mappings
        self.reverse_user_mapping = {v: k for k, v in self.user_mapping.items()}
        self.reverse_artist_mapping = {v: k for k, v in self.artist_mapping.items()}
        
        logger.info(f"Mappings loaded: {len(self.user_mapping)} users, {len(self.artist_mapping)} artists")
    
    def _load_data(self):
        """Load training data"""
        logger.info("Loading training data...")
        
        # Load sparse matrix
        self.train_matrix = load_npz(self.data_dir / "user_item_matrix.npz")
        
        # Load training interactions for stats
        self.train_data = pd.read_csv(self.data_dir / "train_interactions.csv")
        
        logger.info(f"Training data loaded: {len(self.train_data)} interactions")
    
    def get_recommendations_by_user(self, user_id: str, k: int = 10) -> List[Tuple[str, float]]:
        """
        Get recommendations for a specific user
        
        Args:
            user_id: User ID
            k: Number of recommendations
            
        Returns:
            List of (artist_name, score) tuples
        """
        # Get user index
        if user_id not in self.user_mapping:
            raise ValueError(f"User ID '{user_id}' not found in dataset")
        
        user_idx = self.user_mapping[user_id]
        
        # Check if user exists in model
        if user_idx >= self.user_factors.shape[0]:
            raise ValueError(f"User index {user_idx} out of model range")
        
        # Get recommendations
        ids, scores = self.model.recommend(
            user_idx,
            self.train_matrix[user_idx],
            N=k,
            filter_already_liked_items=True
        )
        
        # Convert to artist names
        recommendations = []
        for artist_idx, score in zip(ids, scores):
            if artist_idx < len(self.reverse_artist_mapping):
                artist_name = self.reverse_artist_mapping[artist_idx]
                recommendations.append((artist_name, float(score)))
        
        return recommendations
    
    def get_recommendations_by_mood(self, mood: str, k: int = 10) -> Tuple[List[Tuple[str, float]], List[str]]:
        """
        Get recommendations based on mood
        
        Args:
            mood: Mood name (e.g., 'heartbreak', 'party')
            k: Number of recommendations
            
        Returns:
            Tuple of (recommendations, seed_artists)
            recommendations: List of (artist_name, score) tuples
            seed_artists: List of seed artists used
        """
        # Get seed artists for this mood
        seed_artists = get_mood_seed_artists(mood)
        
        if not seed_artists:
            raise ValueError(f"Mood '{mood}' not found")
        
        # Find users who listen to these seed artists
        seed_artist_indices = []
        found_seeds = []
        for artist in seed_artists:
            if artist in self.artist_mapping:
                seed_artist_indices.append(self.artist_mapping[artist])
                found_seeds.append(artist)
        
        if not seed_artist_indices:
            raise ValueError(f"No seed artists found in dataset for mood '{mood}'")
        
        # Find users who listen to these artists
        user_scores = []
        for seed_idx in seed_artist_indices:
            # Get users who listened to this artist
            users_for_artist = self.train_matrix[:, seed_idx].nonzero()[0]
            for user_idx in users_for_artist:
                if user_idx < self.user_factors.shape[0]:
                    user_scores.append(user_idx)
        
        if not user_scores:
            raise ValueError(f"No users found who listen to seed artists for mood '{mood}'")
        
        # Get most common users (who listen to multiple seed artists)
        user_counts = pd.Series(user_scores).value_counts()
        top_users = user_counts.head(min(50, len(user_counts))).index.tolist()
        
        # Aggregate recommendations from these users
        all_recommendations = {}
        for user_idx in top_users:
            try:
                ids, scores = self.model.recommend(
                    user_idx,
                    self.train_matrix[user_idx],
                    N=k * 2,  # Get more to aggregate
                    filter_already_liked_items=True
                )
                
                for artist_idx, score in zip(ids, scores):
                    if artist_idx < len(self.reverse_artist_mapping):
                        artist_name = self.reverse_artist_mapping[artist_idx]
                        # Skip seed artists
                        if artist_name not in seed_artists:
                            if artist_name in all_recommendations:
                                all_recommendations[artist_name] += float(score)
                            else:
                                all_recommendations[artist_name] = float(score)
            except:
                continue
        
        # Sort and return top K
        sorted_recs = sorted(all_recommendations.items(), key=lambda x: x[1], reverse=True)[:k]
        
        return sorted_recs, found_seeds
    
    def get_similar_artists(self, artist_name: str, k: int = 10) -> List[Tuple[str, float]]:
        """
        Get similar artists using item factors
        
        Args:
            artist_name: Artist name
            k: Number of similar artists
            
        Returns:
            List of (artist_name, similarity_score) tuples
        """
        # Normalize artist name
        artist_name = artist_name.lower().strip()
        
        # Get artist index
        if artist_name not in self.artist_mapping:
            raise ValueError(f"Artist '{artist_name}' not found in dataset")
        
        artist_idx = self.artist_mapping[artist_name]
        
        # Get artist factor vector
        artist_vector = self.item_factors[artist_idx].reshape(1, -1)
        
        # Compute cosine similarity with all artists
        similarities = cosine_similarity(artist_vector, self.item_factors)[0]
        
        # Get top K (excluding the artist itself)
        top_indices = np.argsort(similarities)[::-1][1:k+1]
        
        # Convert to artist names
        similar_artists = []
        for idx in top_indices:
            if idx < len(self.reverse_artist_mapping):
                similar_artist_name = self.reverse_artist_mapping[idx]
                similar_artists.append((similar_artist_name, float(similarities[idx])))
        
        return similar_artists
    
    def get_top_charts(self, k: int = 20) -> List[Tuple[str, int, int]]:
        """
        Get top charts (most popular artists)
        
        Args:
            k: Number of top artists
            
        Returns:
            List of (artist_name, play_count, listener_count) tuples
        """
        # Aggregate play counts and listener counts
        artist_stats = self.train_data.groupby('artist_name').agg({
            'play_count': 'sum',
            'user_id': 'nunique'
        }).reset_index()
        
        artist_stats.columns = ['artist_name', 'total_plays', 'listener_count']
        
        # Sort by total plays
        artist_stats = artist_stats.sort_values('total_plays', ascending=False).head(k)
        
        # Convert to list of tuples
        charts = []
        for _, row in artist_stats.iterrows():
            charts.append((
                row['artist_name'],
                int(row['total_plays']),
                int(row['listener_count'])
            ))
        
        return charts
    
    def get_random_recommendations(self, k: int = 10) -> Tuple[List[Tuple[str, float]], str]:
        """
        Get recommendations for a random user
        
        Args:
            k: Number of recommendations
            
        Returns:
            Tuple of (recommendations, user_id)
            recommendations: List of (artist_name, score) tuples
            user_id: The random user ID selected
        """
        # Pick a random user index from model range
        n_model_users = self.user_factors.shape[0]
        random_user_idx = np.random.randint(0, n_model_users)
        
        # Get user ID
        user_id = self.reverse_user_mapping.get(random_user_idx, f"user_{random_user_idx}")
        
        # Get recommendations
        ids, scores = self.model.recommend(
            random_user_idx,
            self.train_matrix[random_user_idx],
            N=k,
            filter_already_liked_items=True
        )
        
        # Convert to artist names
        recommendations = []
        for artist_idx, score in zip(ids, scores):
            if artist_idx < len(self.reverse_artist_mapping):
                artist_name = self.reverse_artist_mapping[artist_idx]
                recommendations.append((artist_name, float(score)))
        
        return recommendations, user_id
    
    def get_model_info(self) -> dict:
        """
        Get model metadata
        
        Returns:
            Dictionary with model information
        """
        metadata_path = self.model_dir / "model_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        
        return {
            "n_users": self.user_factors.shape[0],
            "n_artists": self.item_factors.shape[0],
            "factors": self.user_factors.shape[1]
        }
