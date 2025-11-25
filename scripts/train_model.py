"""
Script to train ALS music recommender model
"""

import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.als_trainer import ALSTrainer


def main():
    """
    Main function to train model
    """
    print("="*70)
    print(" "*15 + "MUSIC RECOMMENDER - MODEL TRAINING")
    print("="*70)
    
    # Load configuration
    config_path = "configs/config.yaml"
    print(f"\n📋 Loading configuration from: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"✅ Configuration loaded")
    print(f"\nModel hyperparameters:")
    print(f"  - Factors: {config['model']['factors']}")
    print(f"  - Regularization: {config['model']['regularization']}")
    print(f"  - Iterations: {config['model']['iterations']}")
    print(f"  - Alpha: {config['model'].get('alpha', 40)}")
    
    # Check if processed data exists
    processed_dir = Path(config['data']['processed_dir'])
    if not processed_dir.exists():
        print(f"\n❌ Error: Processed data not found at {processed_dir}")
        print("Please run preprocessing first: python scripts/run_preprocessing.py")
        sys.exit(1)
    
    print(f"\n✅ Processed data found")
    
    # Initialize trainer
    print(f"\n🔧 Initializing ALS trainer...")
    trainer = ALSTrainer(config)
    
    # Run training pipeline
    print(f"\n🚀 Starting training pipeline...\n")
    print("⏰ This will take approximately 20-30 minutes...")
    print("☕ Good time for a coffee break!\n")
    
    stats = trainer.run_training_pipeline()
    
    # Print summary
    print("\n" + "="*70)
    print(" "*25 + "TRAINING SUMMARY")
    print("="*70)
    
    print("\n📊 Model Statistics:")
    print(f"  Training time: {stats.get('training_time_minutes', 0):.2f} minutes")
    print(f"  Users: {stats.get('n_users', len(trainer.user_mapping)):,}")
    print(f"  Artists: {stats.get('n_artists', len(trainer.artist_mapping)):,}")
    
    print("\n📈 Evaluation Metrics (K=10):")
    if 'precision@10' in stats:
        print(f"  Precision@10: {stats['precision@10']:.4f}")
    if 'map@10' in stats:
        print(f"  MAP@10: {stats['map@10']:.4f}")
    if 'ndcg@10' in stats:
        print(f"  NDCG@10: {stats['ndcg@10']:.4f}")
    
    print("\n📁 Saved Artifacts:")
    print(f"  - Model: models/als_model.pkl")
    print(f"  - User factors: models/user_factors.npy")
    print(f"  - Item factors: models/item_factors.npy")
    print(f"  - Metadata: models/model_metadata.json")
    
    print("\n✅ Training complete!")
    print(f"🎯 Model is ready for deployment!")
    
    print("\n" + "="*70)
    print("Next steps:")
    print("  1. Start MLflow UI: mlflow ui")
    print("  2. Build API: python scripts/build_api.py")
    print("  3. Test predictions: python scripts/test_model.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
