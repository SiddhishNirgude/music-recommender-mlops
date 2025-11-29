"""
Train ALS Model with Comprehensive Evaluation

This script:
1. Loads preprocessed data
2. Trains ALS collaborative filtering model
3. Evaluates with multiple metrics (Precision, MAP, NDCG)
4. Logs everything to MLflow
5. Saves model artifacts
"""

import pickle
import numpy as np
import pandas as pd
import yaml
import mlflow
import mlflow.sklearn
from pathlib import Path
from scipy.sparse import load_npz, csr_matrix
import time
from datetime import datetime
import json

# Import implicit library
from implicit.als import AlternatingLeastSquares
from implicit.evaluation import (
    precision_at_k,
    mean_average_precision_at_k,
    ndcg_at_k
)


def load_config(config_path='configs/config.yaml'):
    """Load configuration file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_data(data_dir='data/processed'):
    """Load preprocessed data"""
    print("📂 Loading preprocessed data...")
    
    # Load user-item matrix
    matrix_path = Path(data_dir) / 'user_item_matrix.npz'
    user_item_matrix = load_npz(matrix_path)
    
    # Load train/test splits
    train_df = pd.read_csv(Path(data_dir) / 'train_interactions.csv')
    test_df = pd.read_csv(Path(data_dir) / 'test_interactions.csv')
    
    # Load mappings
    with open(Path(data_dir) / 'user_mapping.json', 'r') as f:
        user_mapping = json.load(f)
    
    with open(Path(data_dir) / 'artist_mapping.json', 'r') as f:
        artist_mapping = json.load(f)
    
    # Reverse mappings for evaluation
    idx_to_user = {v: k for k, v in user_mapping.items()}
    idx_to_artist = {v: k for k, v in artist_mapping.items()}
    
    print(f"✅ Loaded matrix: {user_item_matrix.shape}")
    print(f"   Train interactions: {len(train_df):,}")
    print(f"   Test interactions: {len(test_df):,}")
    
    return {
        'user_item_matrix': user_item_matrix,
        'train_df': train_df,
        'test_df': test_df,
        'user_mapping': user_mapping,
        'artist_mapping': artist_mapping,
        'idx_to_user': idx_to_user,
        'idx_to_artist': idx_to_artist
    }


def create_train_test_matrices(train_df, test_df, n_users, n_artists, user_mapping, artist_mapping):
    """Create sparse matrices for train and test data"""
    
    print("🔨 Creating train/test matrices...")
    
    # Map user/artist to indices (using correct column names)
    train_df['user_idx'] = train_df['user_id'].astype(str).map(user_mapping)
    train_df['artist_idx'] = train_df['artist_name'].map(artist_mapping)
    
    test_df['user_idx'] = test_df['user_id'].astype(str).map(user_mapping)
    test_df['artist_idx'] = test_df['artist_name'].map(artist_mapping)
    
    # Remove rows with NaN indices (users/artists not in mapping)
    train_df = train_df.dropna(subset=['user_idx', 'artist_idx'])
    test_df = test_df.dropna(subset=['user_idx', 'artist_idx'])
    
    # Convert to int
    train_df['user_idx'] = train_df['user_idx'].astype(int)
    train_df['artist_idx'] = train_df['artist_idx'].astype(int)
    test_df['user_idx'] = test_df['user_idx'].astype(int)
    test_df['artist_idx'] = test_df['artist_idx'].astype(int)
    
    # Use confidence or preference as weights (prefer confidence)
    weight_col = 'confidence' if 'confidence' in train_df.columns else 'preference'
    
    # Create train matrix (user x artist)
    train_matrix = csr_matrix(
        (train_df[weight_col], (train_df['user_idx'], train_df['artist_idx'])),
        shape=(n_users, n_artists)
    )
    
    # Create test matrix (user x artist)
    test_matrix = csr_matrix(
        (test_df[weight_col], (test_df['user_idx'], test_df['artist_idx'])),
        shape=(n_users, n_artists)
    )
    
    print(f"✅ Train matrix: {train_matrix.shape}, nnz: {train_matrix.nnz:,}")
    print(f"✅ Test matrix: {test_matrix.shape}, nnz: {test_matrix.nnz:,}")
    
    return train_matrix, test_matrix


def train_als_model(train_matrix, config):
    """Train ALS model"""
    
    print("\n🏋️  Training ALS model...")
    
    model_params = config['model']
    
    model = AlternatingLeastSquares(
        factors=model_params['factors'],
        regularization=model_params['regularization'],
        iterations=model_params['iterations'],
        alpha=model_params.get('alpha', 40),
        random_state=42
    )
    
    # Train (implicit expects item-user matrix)
    start_time = time.time()
    model.fit(train_matrix.T)  # Transpose for implicit library
    training_time = time.time() - start_time
    
    print(f"✅ Training complete in {training_time/60:.2f} minutes")
    
    return model, training_time


def evaluate_model(model, train_matrix, test_matrix, k=10):
    """Evaluate model with multiple metrics"""
    
    print(f"\n📊 Evaluating model (K={k})...")
    
    try:
        # Precision@K (pass item-user matrices for implicit library)
        print("   Computing Precision@K...")
        precision = precision_at_k(model, train_matrix.T.tocsr(), test_matrix.T.tocsr(), K=k, show_progress=False)
        
        # MAP@K
        print("   Computing MAP@K...")
        map_score = mean_average_precision_at_k(model, train_matrix.T.tocsr(), test_matrix.T.tocsr(), K=k, show_progress=False)
        
        # NDCG@K
        print("   Computing NDCG@K...")
        ndcg = ndcg_at_k(model, train_matrix.T.tocsr(), test_matrix.T.tocsr(), K=k, show_progress=False)
        
        metrics = {
            f'precision_at_{k}': float(precision),
            f'map_at_{k}': float(map_score),
            f'ndcg_at_{k}': float(ndcg)
        }
        
        print(f"\n📈 Evaluation Results:")
        print(f"   Precision@{k}: {precision:.6f}")
        print(f"   MAP@{k}:       {map_score:.6f}")
        print(f"   NDCG@{k}:      {ndcg:.6f}")
        
    except Exception as e:
        print(f"⚠️  Evaluation failed: {e}")
        print("   Using default metrics (0.0)")
        metrics = {
            f'precision_at_{k}': 0.0,
            f'map_at_{k}': 0.0,
            f'ndcg_at_{k}': 0.0
        }
    
    return metrics


def save_model_artifacts(model, data, output_dir='models'):
    """Save model and factors"""
    
    print(f"\n💾 Saving model artifacts to {output_dir}/...")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save model
    model_path = output_path / 'als_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f"   ✅ Saved model: {model_path}")
    
    # Save user factors
    user_factors_path = output_path / 'user_factors.npy'
    np.save(user_factors_path, model.user_factors)
    print(f"   ✅ Saved user factors: {user_factors_path}")
    
    # Save item factors
    item_factors_path = output_path / 'item_factors.npy'
    np.save(item_factors_path, model.item_factors)
    print(f"   ✅ Saved item factors: {item_factors_path}")
    
    # Save metadata
    metadata = {
        'model_type': 'ALS',
        'n_users': model.user_factors.shape[0],
        'n_items': model.item_factors.shape[0],
        'n_factors': model.user_factors.shape[1],
        'trained_at': datetime.now().isoformat(),
        'library': 'implicit',
        'version': '1.0'
    }
    
    metadata_path = output_path / 'model_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"   ✅ Saved metadata: {metadata_path}")
    
    return {
        'model_path': str(model_path),
        'user_factors_path': str(user_factors_path),
        'item_factors_path': str(item_factors_path),
        'metadata_path': str(metadata_path)
    }


def print_summary(config, data, metrics, training_time, paths):
    """Print training summary"""
    
    model_params = config['model']
    
    print("\n" + "="*70)
    print("                         TRAINING SUMMARY")
    print("="*70)
    
    print("\n📊 Model Statistics:")
    print(f"  Training time: {training_time/60:.2f} minutes")
    print(f"  Users: {data['user_item_matrix'].shape[0]:,}")
    print(f"  Artists: {data['user_item_matrix'].shape[1]:,}")
    
    print("\n🎛️  Hyperparameters:")
    print(f"  Factors: {model_params['factors']}")
    print(f"  Iterations: {model_params['iterations']}")
    print(f"  Regularization: {model_params['regularization']}")
    print(f"  Alpha: {model_params.get('alpha', 40)}")
    
    print("\n📈 Evaluation Metrics (K=10):")
    for metric_name, metric_value in metrics.items():
        print(f"  {metric_name}: {metric_value:.6f}")
    
    print("\n📁 Saved Artifacts:")
    for name, path in paths.items():
        print(f"  - {name.replace('_', ' ').title()}: {path}")
    
    print("\n✅ Training complete!")
    print("🎯 Model is ready for deployment!")
    
    print("="*70)
    print("\nNext steps:")
    print("  1. Start MLflow UI: mlflow ui")
    print("  2. Build API: python scripts/build_api.py")
    print("  3. Test predictions: python scripts/test_model.py")
    print("="*70 + "\n")


def main():
    """Main training pipeline"""
    
    print("\n" + "🚀" + "="*68 + "🚀")
    print("           ALS MODEL TRAINING WITH MLFLOW TRACKING")
    print("🚀" + "="*68 + "🚀" + "\n")
    
    # Load config
    config = load_config()
    
    # Load data
    data = load_data()
    
    # Get dimensions
    n_users = data['user_item_matrix'].shape[0]
    n_artists = data['user_item_matrix'].shape[1]
    
    # Create train/test matrices
    train_matrix, test_matrix = create_train_test_matrices(
        data['train_df'],
        data['test_df'],
        n_users,
        n_artists,
        data['user_mapping'],
        data['artist_mapping']
    )
    
    # Start MLflow run
    mlflow.set_experiment("music-recommender-als")
    
    with mlflow.start_run():
        
        # Log parameters
        model_params = config['model']
        mlflow.log_params({
            'factors': model_params['factors'],
            'regularization': model_params['regularization'],
            'iterations': model_params['iterations'],
            'alpha': model_params.get('alpha', 40),
            'n_users': n_users,
            'n_artists': n_artists
        })
        
        # Train model
        model, training_time = train_als_model(train_matrix, config)
        
        # Evaluate model
        metrics = evaluate_model(model, train_matrix, test_matrix, k=10)
        
        # Log metrics to MLflow
        mlflow.log_metrics({
            **metrics,
            'training_time_seconds': training_time,
            'training_time_minutes': training_time / 60,
            'train_interactions': train_matrix.nnz,
            'test_interactions': test_matrix.nnz,
            'train_users': (train_matrix.sum(axis=1) > 0).sum(),
            'test_users': (test_matrix.sum(axis=1) > 0).sum()
        })
        
        # Save model artifacts
        paths = save_model_artifacts(model, data)
        
        # Log artifacts to MLflow
        mlflow.log_artifacts('models', artifact_path='model')
        
        # Print summary
        print_summary(config, data, metrics, training_time, paths)
        
        # Log model to MLflow registry
        mlflow.sklearn.log_model(
            model,
            "model",
            registered_model_name="music-recommender-als"
        )
        
        print("✅ MLflow run completed!")
        print(f"🔗 View at: http://localhost:5000")


if __name__ == "__main__":
    main()
