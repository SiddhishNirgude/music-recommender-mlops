"""
Script to run data preprocessing pipeline
"""

import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_processing.preprocess import DataPreprocessor


def main():
    """
    Main function to run preprocessing
    """
    print("="*70)
    print(" "*15 + "MUSIC RECOMMENDER - DATA PREPROCESSING")
    print("="*70)
    
    # Load configuration
    config_path = "configs/config.yaml"
    print(f"\n📋 Loading configuration from: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"✅ Configuration loaded")
    print(f"\nKey parameters:")
    print(f"  - Min user interactions: {config['preprocessing']['min_user_interactions']}")
    print(f"  - Min artist listeners: {config['preprocessing']['min_artist_listeners']}")
    print(f"  - Test size: {config['preprocessing']['test_size']*100}%")
    print(f"  - Alpha (confidence): {config['preprocessing']['alpha']}")
    
    # Initialize preprocessor
    print(f"\n🔧 Initializing preprocessor...")
    preprocessor = DataPreprocessor(config)
    
    # Run pipeline
    print(f"\n🚀 Starting preprocessing pipeline...\n")
    stats = preprocessor.run_pipeline()
    
    # Print summary
    print("\n" + "="*70)
    print(" "*20 + "PREPROCESSING SUMMARY")
    print("="*70)
    
    print("\n📊 Data Statistics:")
    print(f"  Original:")
    print(f"    - Rows: {stats.get('original_rows', 0):,}")
    print(f"    - Users: {stats.get('original_users', 0):,}")
    print(f"    - Artists: {stats.get('original_artists', 0):,}")
    
    print(f"\n  After Filtering:")
    print(f"    - Rows: {stats.get('rows_after_filter', 0):,}")
    print(f"    - Users: {stats.get('users_after_filter', 0):,}")
    print(f"    - Artists: {stats.get('artists_after_filter', 0):,}")
    
    print(f"\n  Train/Test Split:")
    print(f"    - Train: {stats.get('train_rows', 0):,} interactions")
    print(f"    - Test: {stats.get('test_rows', 0):,} interactions")
    
    print(f"\n  User-Item Matrix:")
    print(f"    - Shape: {stats.get('matrix_shape', (0,0))}")
    print(f"    - Sparsity: {stats.get('matrix_sparsity', 0)*100:.4f}%")
    
    print(f"\n  Data Quality:")
    print(f"    - Duplicates removed: {stats.get('duplicates_removed', 0)}")
    print(f"    - Rows dropped (missing): {stats.get('rows_dropped_missing', 0)}")
    
    print("\n✅ Preprocessing complete!")
    print(f"📁 Processed data saved to: {config['data']['processed_dir']}")
    
    print("\n" + "="*70)
    print("Next steps:")
    print("  1. Train ALS model: python scripts/train_model.py")
    print("  2. Evaluate model: python scripts/evaluate_model.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
