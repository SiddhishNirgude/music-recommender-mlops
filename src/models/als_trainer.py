"""
ALS Model Trainer for Music Recommender System
Handles model training, evaluation, and MLflow logging
"""

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, load_npz
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, List
import time
import pickle

# ALS implementation
from implicit.als import AlternatingLeastSquares
from implicit.evaluation import mean_average_precision_at_k, ndcg_at_k, precision_at_k

# MLflow
import mlflow
import mlflow.sklearn

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ALSTrainer:
    """
    Trainer for ALS-based music recommender
    """
    
    def __init__(self, config: Dict):
        """
        Initialize trainer with configuration
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.model = None
        self.user_factors = None
        self.item_factors = None
        self.user_mapping = None
        self.artist_mapping = None
        self.stats = {}
        
    def load_data(self) -> Tuple[csr_matrix, Dict, Dict]:
        """
        Load preprocessed data
        
        Returns:
            Tuple of (user_item_matrix, user_mapping, artist_mapping)
        """
        logger.info("Loading preprocessed data...")
        
        data_config = self.config['data']
        
        # Load sparse matrix
        matrix_path = data_config['user_item_matrix']
        user_item_matrix = load_npz(matrix_path)
        logger.info(f"Loaded user-item matrix: {user_item_matrix.shape}")
        
        # Load mappings
        with open(data_config['user_mapping'], 'r') as f:
            user_mapping = json.load(f)
        
        with open(data_config['artist_mapping'], 'r') as f:
            artist_mapping = json.load(f)
        
        logger.info(f"Loaded {len(user_mapping):,} users and {len(artist_mapping):,} artists")
        
        self.user_mapping = user_mapping
        self.artist_mapping = artist_mapping
        
        return user_item_matrix, user_mapping, artist_mapping
    
    def load_test_data(self) -> pd.DataFrame:
        """
        Load test data for evaluation
        
        Returns:
            Test DataFrame
        """
        logger.info("Loading test data...")
        test_df = pd.read_csv(self.config['data']['test_file'])
        logger.info(f"Loaded {len(test_df):,} test interactions")
        return test_df
    
    def train_model(self, user_item_matrix: csr_matrix) -> AlternatingLeastSquares:
        """
        Train ALS model
        
        Args:
            user_item_matrix: Sparse user-item interaction matrix
            
        Returns:
            Trained ALS model
        """
        logger.info("="*60)
        logger.info("Training ALS Model")
        logger.info("="*60)
        
        model_config = self.config['model']
        
        # Initialize model
        model = AlternatingLeastSquares(
            factors=model_config['factors'],
            regularization=model_config['regularization'],
            iterations=model_config['iterations'],
            alpha=model_config.get('alpha', 40),
            use_gpu=False,  # Set to True if you have GPU
            random_state=42
        )
        
        logger.info(f"Model configuration:")
        logger.info(f"  - Factors: {model_config['factors']}")
        logger.info(f"  - Regularization: {model_config['regularization']}")
        logger.info(f"  - Iterations: {model_config['iterations']}")
        logger.info(f"  - Alpha: {model_config.get('alpha', 40)}")
        
        # Train model
        logger.info("\nStarting training...")
        start_time = time.time()
        
        # Note: implicit expects items × users, so we transpose
        model.fit(user_item_matrix)
        
        training_time = time.time() - start_time
        logger.info(f"Training completed in {training_time:.2f} seconds ({training_time/60:.2f} minutes)")
        
        self.model = model
        self.user_factors = model.user_factors
        self.item_factors = model.item_factors
        
        self.stats['training_time_seconds'] = training_time
        self.stats['training_time_minutes'] = training_time / 60
        
        return model
    
    def evaluate_model(self, test_df: pd.DataFrame, k: int = 10) -> Dict:
        """
        Evaluate model on test set
        
        Args:
            test_df: Test DataFrame with user_id, artist_name, confidence
            k: Number of recommendations to consider
            
        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("="*60)
        logger.info("Evaluating Model")
        logger.info("="*60)
        
        metrics = {}
        
        # Create test sparse matrix
        logger.info("Creating test matrix...")
        test_user_indices = test_df['user_id'].map(self.user_mapping).values
        test_artist_indices = test_df['artist_name'].map(self.artist_mapping).values
        test_confidence = test_df['confidence'].values
        
        n_users = len(self.user_mapping)
        n_artists = len(self.artist_mapping)
        
        test_matrix = csr_matrix(
            (test_confidence, (test_user_indices, test_artist_indices)),
            shape=(n_users, n_artists)
        )
        
        # Get training matrix for filtering
        train_matrix = load_npz(self.config['data']['user_item_matrix'])
        
        logger.info(f"Evaluating with K={k}...")
        
        # Precision@K
        try:
            precision = precision_at_k(
                self.model, 
                train_matrix.T,  # Transpose for implicit library
                test_matrix.T,
                K=k,
                show_progress=True
            )
            metrics[f'precision@{k}'] = float(precision)
            logger.info(f"Precision@{k}: {precision:.4f}")
        except Exception as e:
            logger.warning(f"Could not compute Precision@{k}: {e}")
        
        # Mean Average Precision@K
        try:
            map_score = mean_average_precision_at_k(
                self.model,
                train_matrix.T,
                test_matrix.T,
                K=k,
                show_progress=True
            )
            metrics[f'map@{k}'] = float(map_score)
            logger.info(f"MAP@{k}: {map_score:.4f}")
        except Exception as e:
            logger.warning(f"Could not compute MAP@{k}: {e}")
        
        # NDCG@K
        try:
            ndcg = ndcg_at_k(
                self.model,
                train_matrix.T,
                test_matrix.T,
                K=k,
                show_progress=True
            )
            metrics[f'ndcg@{k}'] = float(ndcg)
            logger.info(f"NDCG@{k}: {ndcg:.4f}")
        except Exception as e:
            logger.warning(f"Could not compute NDCG@{k}: {e}")
        
        # Additional metrics
        metrics['test_users'] = test_df['user_id'].nunique()
        metrics['test_interactions'] = len(test_df)
        
        self.stats.update(metrics)
        
        return metrics
    
    def generate_sample_recommendations(self, n_samples: int = 5, k: int = 10) -> List[Dict]:
        """
        Generate sample recommendations for verification
        """
        logger.info(f"\nGenerating {n_samples} sample recommendations...")
        
        samples = []
        
        # Get reverse mappings
        reverse_user_mapping = {v: k for k, v in self.user_mapping.items()}
        reverse_artist_mapping = {v: k for k, v in self.artist_mapping.items()}
        
        # Load training matrix
        train_matrix = load_npz(self.config['data']['user_item_matrix'])
        
        # Sample from the actual model's user factor space
        n_model_users = self.model.user_factors.shape[0]
        logger.info(f"Model has {n_model_users:,} user factors")
        
        sample_user_indices = np.random.choice(
            n_model_users,
            size=min(n_samples, n_model_users),
            replace=False
        )
        
        for user_idx in sample_user_indices:
            user_id = reverse_user_mapping[user_idx]
            
            # Get recommendations - returns (ids, scores)
            ids, scores = self.model.recommend(
                user_idx,
                train_matrix[user_idx],
                N=k,
                filter_already_liked_items=True
            )
            
            # ADDED DEBUG LINES HERE
            print(f"\nDEBUG: Type of recommendations: {type(ids)}") # Updated to 'ids' since model now returns (ids, scores)
            print(f"DEBUG: Length: {len(ids)}")
            print(f"DEBUG: First item type: {type(ids[0])}")
            print(f"DEBUG: First item: {ids[0]}")
            # The original structure of the loop was changed to unpack 'ids, scores'
            # I've updated the prints to reflect that the actual recommendation list is 'ids' (item indices).

            # Convert to artist names
            rec_artists = [reverse_artist_mapping[artist_idx] for artist_idx in ids]
            rec_scores = [float(score) for score in scores]
            
            sample = {
                'user_id': user_id[:20] + '...',
                'recommendations': rec_artists,
                'scores': rec_scores
            }
            samples.append(sample)
            
            # Print sample
            logger.info(f"\nUser: {sample['user_id']}")
            for i, (artist, score) in enumerate(zip(rec_artists[:5], rec_scores[:5]), 1):
                logger.info(f"  {i}. {artist} (score: {score:.3f})")
        
        return samples
    
    def save_model(self, output_dir: str = "models"):
        """
        Save trained model and artifacts
        
        Args:
            output_dir: Directory to save model
        """
        logger.info(f"\nSaving model to {output_dir}...")
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_path = f"{output_dir}/als_model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Saved model: {model_path}")
        
        # Save factors
        user_factors_path = f"{output_dir}/user_factors.npy"
        item_factors_path = f"{output_dir}/item_factors.npy"
        np.save(user_factors_path, self.user_factors)
        np.save(item_factors_path, self.item_factors)
        logger.info(f"Saved user factors: {user_factors_path}")
        logger.info(f"Saved item factors: {item_factors_path}")
        
        # Save metadata
        metadata = {
            'model_type': 'ALS',
            'n_users': len(self.user_mapping),
            'n_artists': len(self.artist_mapping),
            'factors': self.config['model']['factors'],
            'regularization': self.config['model']['regularization'],
            'iterations': self.config['model']['iterations'],
            'alpha': self.config['model'].get('alpha', 40),
            'training_time_minutes': self.stats.get('training_time_minutes', 0),
            'metrics': {k: v for k, v in self.stats.items() if '@' in k or k.startswith('test_')}
        }
        
        metadata_path = f"{output_dir}/model_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata: {metadata_path}")
        
        return model_path
    
    def log_to_mlflow(self, experiment_name: str = "music-recommender"):
        """
        Log model and metrics to MLflow
        
        Args:
            experiment_name: MLflow experiment name
        """
        logger.info("\nLogging to MLflow...")
        
        # Set experiment
        mlflow.set_experiment(experiment_name)
        
        with mlflow.start_run():
            # Log parameters
            mlflow.log_params({
                'factors': self.config['model']['factors'],
                'regularization': self.config['model']['regularization'],
                'iterations': self.config['model']['iterations'],
                'alpha': self.config['model'].get('alpha', 40),
                'n_users': len(self.user_mapping),
                'n_artists': len(self.artist_mapping)
            })
            
            # Log metrics
            mlflow.log_metrics({
                k: v for k, v in self.stats.items() 
                if isinstance(v, (int, float))
            })
            
            # Log model artifacts
            mlflow.log_artifact("models/als_model.pkl")
            mlflow.log_artifact("models/user_factors.npy")
            mlflow.log_artifact("models/item_factors.npy")
            mlflow.log_artifact("models/model_metadata.json")
            
            # Log model
            mlflow.sklearn.log_model(
                self.model, 
                "model",
                registered_model_name="music-recommender-als"
            )
            
            logger.info("✅ Logged to MLflow successfully!")
    
    def run_training_pipeline(self) -> Dict:
        """
        Run complete training pipeline
        
        Returns:
            Dictionary with training statistics
        """
        logger.info("="*70)
        logger.info(" "*15 + "ALS MODEL TRAINING PIPELINE")
        logger.info("="*70)
        
        # Step 1: Load data
        user_item_matrix, user_mapping, artist_mapping = self.load_data()
        
        # Step 2: Train model
        model = self.train_model(user_item_matrix)
        
        # Step 3: Evaluate model
        test_df = self.load_test_data()
        metrics = self.evaluate_model(test_df, k=10)
        
        # Step 4: Generate sample recommendations
        samples = self.generate_sample_recommendations(n_samples=5, k=10)
        
        # Step 5: Save model
        self.save_model(output_dir="models")
        
        # Step 6: Log to MLflow
        try:
            self.log_to_mlflow()
        except Exception as e:
            logger.warning(f"Could not log to MLflow: {e}")
            logger.warning("Continuing without MLflow logging...")
        
        logger.info("="*70)
        logger.info(" "*20 + "TRAINING COMPLETE!")
        logger.info("="*70)
        
        return self.stats


if __name__ == "__main__":
    # Example usage
    import yaml
    
    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    trainer = ALSTrainer(config)
    stats = trainer.run_training_pipeline()
    
    print("\n" + "="*70)
    print(" "*25 + "FINAL STATISTICS")
    print("="*70)
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
