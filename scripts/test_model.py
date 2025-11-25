"""
Quick test script to verify trained model works
"""

import numpy as np
import pickle
import json
from scipy.sparse import load_npz

def test_model():
    """
    Test the trained model
    """
    print("="*60)
    print("  Testing Trained ALS Model")
    print("="*60)
    
    # Load model
    print("\n📦 Loading model...")
    try:
        with open('models/als_model.pkl', 'rb') as f:
            model = pickle.load(f)
        print("✅ Model loaded")
    except FileNotFoundError:
        print("❌ Model not found. Please train first:")
        print("   python scripts/train_model.py")
        return
    
    # Load mappings
    print("\n📋 Loading mappings...")
    with open('data/processed/user_mapping.json', 'r') as f:
        user_mapping = json.load(f)
    with open('data/processed/artist_mapping.json', 'r') as f:
        artist_mapping = json.load(f)
    
    reverse_artist = {v: k for k, v in artist_mapping.items()}
    print(f"✅ Loaded {len(user_mapping):,} users, {len(artist_mapping):,} artists")
    
    # Load train matrix
    print("\n📊 Loading interaction matrix...")
    train_matrix = load_npz('data/processed/user_item_matrix.npz')
    print(f"✅ Matrix shape: {train_matrix.shape}")
    
    # Test recommendations for 3 random users
    print("\n🎵 Generating test recommendations...")
    print("="*60)
    
    sample_users = np.random.choice(len(user_mapping), size=3, replace=False)
    
    for i, user_idx in enumerate(sample_users, 1):
        print(f"\nTest {i}:")
        
        # Get recommendations
        recs = model.recommend(
            user_idx,
            train_matrix[user_idx],
            N=10,
            filter_already_liked_items=True
        )
        
        print(f"Top 10 Recommendations:")
        for rank, (artist_idx, score) in enumerate(recs, 1):
            artist_name = reverse_artist[artist_idx]
            print(f"  {rank:2d}. {artist_name:40s} (score: {score:.3f})")
    
    print("\n" + "="*60)
    print("✅ Model test successful!")
    print("="*60)
    print("\n🎯 Model is working correctly!")
    print("\nNext steps:")
    print("  1. Build FastAPI: Check src/api/")
    print("  2. Build Streamlit: Check src/ui/")
    print("  3. View MLflow: mlflow ui")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_model()
