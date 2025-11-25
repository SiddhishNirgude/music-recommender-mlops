"""
Data Preprocessing Module for Music Recommender System
Handles data loading, cleaning, filtering, and train-test split
"""

import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix, save_npz
import json
import logging
from pathlib import Path
from typing import Tuple, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Preprocessor for Last.fm music interaction data
    """
    
    def __init__(self, config: Dict):
        """
        Initialize preprocessor with configuration
        
        Args:
            config: Configuration dictionary with paths and parameters
        """
        self.config = config
        self.stats = {}
        
    def load_data(self, data_path: str) -> pd.DataFrame:
        """
        Load raw TSV data
        
        Args:
            data_path: Path to raw data file
            
        Returns:
            DataFrame with loaded data
        """
        logger.info(f"Loading data from {data_path}")
        
        df = pd.read_csv(
            data_path,
            sep='\t',
            names=['user_id', 'artist_mbid', 'artist_name', 'play_count']
        )
        
        logger.info(f"Loaded {len(df):,} rows")
        self.stats['original_rows'] = len(df)
        self.stats['original_users'] = df['user_id'].nunique()
        self.stats['original_artists'] = df['artist_name'].nunique()
        
        return df
    
    def handle_missingness(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in dataset
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with missing values handled
        """
        logger.info("Handling missing values...")
        
        # Log missing values before
        missing_before = df.isnull().sum()
        logger.info(f"Missing values before:\n{missing_before}")
        
        # Drop rows with missing artist_name (only 7 rows = 0.0004%)
        rows_before = len(df)
        df = df.dropna(subset=['artist_name'])
        rows_dropped = rows_before - len(df)
        logger.info(f"Dropped {rows_dropped} rows with missing artist_name")
        
        # Keep rows with missing artist_mbid - we'll use artist_name instead
        # artist_mbid is just for disambiguation, not required
        logger.info(f"Keeping {df['artist_mbid'].isnull().sum()} rows with missing artist_mbid")
        
        self.stats['rows_dropped_missing'] = rows_dropped
        
        return df
    
    def handle_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle duplicate user-artist pairs by summing play counts
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with duplicates handled
        """
        logger.info("Handling duplicates...")
        
        # Check for duplicates
        duplicates = df.duplicated(subset=['user_id', 'artist_name']).sum()
        logger.info(f"Found {duplicates} duplicate user-artist pairs")
        
        # Group by user and artist, sum play counts
        df = df.groupby(['user_id', 'artist_name'], as_index=False).agg({
            'artist_mbid': 'first',  # Keep first mbid
            'play_count': 'sum'       # Sum play counts
        })
        
        logger.info(f"After deduplication: {len(df):,} rows")
        self.stats['duplicates_removed'] = duplicates
        
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean data - lowercase artist names, basic cleaning
        
        Args:
            df: Input DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        logger.info("Cleaning data...")
        
        # Lowercase artist names for consistency
        df['artist_name'] = df['artist_name'].str.lower().str.strip()
        
        # Remove any remaining weird characters (keep alphanumeric, spaces, hyphens, apostrophes)
        df['artist_name'] = df['artist_name'].str.replace(r'[^\w\s\-\']', '', regex=True)
        
        # Remove extra whitespace
        df['artist_name'] = df['artist_name'].str.replace(r'\s+', ' ', regex=True)
        
        logger.info("Data cleaning complete")
        
        return df
    
    def filter_sparse_data(self, df: pd.DataFrame, 
                          min_user_interactions: int = 5,
                          min_artist_listeners: int = 3) -> pd.DataFrame:
        """
        Filter out sparse users and artists
        
        Args:
            df: Input DataFrame
            min_user_interactions: Minimum interactions per user
            min_artist_listeners: Minimum listeners per artist
            
        Returns:
            Filtered DataFrame
        """
        logger.info("Filtering sparse data...")
        
        # Initial counts
        initial_users = df['user_id'].nunique()
        initial_artists = df['artist_name'].nunique()
        initial_rows = len(df)
        
        # Iteratively filter until convergence
        iteration = 0
        while True:
            iteration += 1
            rows_before = len(df)
            
            # Filter users with too few interactions
            user_counts = df.groupby('user_id').size()
            valid_users = user_counts[user_counts >= min_user_interactions].index
            df = df[df['user_id'].isin(valid_users)]
            
            # Filter artists with too few listeners
            artist_counts = df.groupby('artist_name').size()
            valid_artists = artist_counts[artist_counts >= min_artist_listeners].index
            df = df[df['artist_name'].isin(valid_artists)]
            
            rows_after = len(df)
            logger.info(f"Iteration {iteration}: {rows_after:,} rows remaining")
            
            # Check convergence
            if rows_before == rows_after:
                break
        
        # Final counts
        final_users = df['user_id'].nunique()
        final_artists = df['artist_name'].nunique()
        final_rows = len(df)
        
        logger.info(f"\nFiltering results:")
        logger.info(f"  Users: {initial_users:,} → {final_users:,} ({final_users/initial_users*100:.1f}%)")
        logger.info(f"  Artists: {initial_artists:,} → {final_artists:,} ({final_artists/initial_artists*100:.1f}%)")
        logger.info(f"  Rows: {initial_rows:,} → {final_rows:,} ({final_rows/initial_rows*100:.1f}%)")
        
        self.stats['users_after_filter'] = final_users
        self.stats['artists_after_filter'] = final_artists
        self.stats['rows_after_filter'] = final_rows
        
        return df
    
    def create_implicit_feedback(self, df: pd.DataFrame, alpha: int = 40) -> pd.DataFrame:
        """
        Create implicit feedback signals from play counts
        
        Args:
            df: Input DataFrame with play_count
            alpha: Confidence weight parameter
            
        Returns:
            DataFrame with confidence and preference columns
        """
        logger.info(f"Creating implicit feedback (alpha={alpha})...")
        
        # Confidence: 1 + alpha * play_count
        df['confidence'] = 1 + alpha * df['play_count']
        
        # Preference: binary (1 for all observed interactions)
        df['preference'] = 1
        
        logger.info(f"Confidence range: [{df['confidence'].min():.0f}, {df['confidence'].max():.0f}]")
        logger.info(f"Mean confidence: {df['confidence'].mean():.1f}")
        
        return df
    
    def train_test_split(self, df: pd.DataFrame, test_size: float = 0.2, 
                        random_seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into train and test sets per user
        
        Args:
            df: Input DataFrame
            test_size: Fraction of data for test set
            random_seed: Random seed for reproducibility
            
        Returns:
            Tuple of (train_df, test_df)
        """
        logger.info(f"Splitting data (test_size={test_size})...")
        
        np.random.seed(random_seed)
        
        train_data = []
        test_data = []
        
        # Split per user to ensure each user is in both sets
        for user_id, user_df in df.groupby('user_id'):
            n_interactions = len(user_df)
            n_test = max(1, int(n_interactions * test_size))  # At least 1 test item
            
            # Randomly sample test items
            test_indices = np.random.choice(user_df.index, size=n_test, replace=False)
            train_indices = user_df.index.difference(test_indices)
            
            test_data.append(user_df.loc[test_indices])
            train_data.append(user_df.loc[train_indices])
        
        train_df = pd.concat(train_data, ignore_index=True)
        test_df = pd.concat(test_data, ignore_index=True)
        
        logger.info(f"Train set: {len(train_df):,} interactions ({len(train_df)/len(df)*100:.1f}%)")
        logger.info(f"Test set: {len(test_df):,} interactions ({len(test_df)/len(df)*100:.1f}%)")
        logger.info(f"Users in train: {train_df['user_id'].nunique():,}")
        logger.info(f"Users in test: {test_df['user_id'].nunique():,}")
        
        self.stats['train_rows'] = len(train_df)
        self.stats['test_rows'] = len(test_df)
        
        return train_df, test_df
    
    def create_mappings(self, df: pd.DataFrame) -> Tuple[Dict, Dict]:
        """
        Create user and artist ID mappings
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (user_mapping, artist_mapping) dictionaries
        """
        logger.info("Creating ID mappings...")
        
        # Create mappings: original_id -> integer_index
        unique_users = df['user_id'].unique()
        unique_artists = df['artist_name'].unique()
        
        user_mapping = {user_id: idx for idx, user_id in enumerate(unique_users)}
        artist_mapping = {artist_name: idx for idx, artist_name in enumerate(unique_artists)}
        
        logger.info(f"Created mappings for {len(user_mapping):,} users and {len(artist_mapping):,} artists")
        
        return user_mapping, artist_mapping
    
    def create_sparse_matrix(self, df: pd.DataFrame, 
                            user_mapping: Dict, 
                            artist_mapping: Dict) -> csr_matrix:
        """
        Create sparse user-item matrix
        
        Args:
            df: Input DataFrame with confidence values
            user_mapping: User ID to index mapping
            artist_mapping: Artist name to index mapping
            
        Returns:
            Sparse CSR matrix
        """
        logger.info("Creating sparse user-item matrix...")
        
        # Map IDs to indices
        user_indices = df['user_id'].map(user_mapping).values
        artist_indices = df['artist_name'].map(artist_mapping).values
        confidence_values = df['confidence'].values
        
        # Create sparse matrix
        n_users = len(user_mapping)
        n_artists = len(artist_mapping)
        
        user_item_matrix = csr_matrix(
            (confidence_values, (user_indices, artist_indices)),
            shape=(n_users, n_artists)
        )
        
        # Calculate sparsity
        sparsity = 1 - (user_item_matrix.nnz / (n_users * n_artists))
        
        logger.info(f"Matrix shape: {user_item_matrix.shape}")
        logger.info(f"Non-zero entries: {user_item_matrix.nnz:,}")
        logger.info(f"Sparsity: {sparsity*100:.4f}%")
        
        self.stats['matrix_shape'] = user_item_matrix.shape
        self.stats['matrix_sparsity'] = sparsity
        
        return user_item_matrix
    
    def save_processed_data(self, train_df: pd.DataFrame, test_df: pd.DataFrame,
                           user_item_matrix: csr_matrix, user_mapping: Dict, 
                           artist_mapping: Dict, output_dir: str):
        """
        Save all processed data
        
        Args:
            train_df: Training DataFrame
            test_df: Test DataFrame
            user_item_matrix: Sparse user-item matrix
            user_mapping: User ID mappings
            artist_mapping: Artist ID mappings
            output_dir: Output directory path
        """
        logger.info(f"Saving processed data to {output_dir}...")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save train/test CSVs
        train_path = f"{output_dir}/train_interactions.csv"
        test_path = f"{output_dir}/test_interactions.csv"
        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)
        logger.info(f"Saved train data: {train_path}")
        logger.info(f"Saved test data: {test_path}")
        
        # Save sparse matrix
        matrix_path = f"{output_dir}/user_item_matrix.npz"
        save_npz(matrix_path, user_item_matrix)
        logger.info(f"Saved sparse matrix: {matrix_path}")
        
        # Save mappings
        user_mapping_path = f"{output_dir}/user_mapping.json"
        artist_mapping_path = f"{output_dir}/artist_mapping.json"
        
        with open(user_mapping_path, 'w') as f:
            json.dump(user_mapping, f)
        with open(artist_mapping_path, 'w') as f:
            json.dump(artist_mapping, f)
        
        logger.info(f"Saved user mapping: {user_mapping_path}")
        logger.info(f"Saved artist mapping: {artist_mapping_path}")
        
        # Save statistics
        stats_path = f"{output_dir}/preprocessing_stats.json"
        with open(stats_path, 'w') as f:
            # Convert numpy types to native Python types
            stats_serializable = {
                k: int(v) if isinstance(v, (np.integer, np.int64)) else 
                   float(v) if isinstance(v, (np.floating, np.float64)) else
                   list(v) if isinstance(v, tuple) else v
                for k, v in self.stats.items()
            }
            json.dump(stats_serializable, f, indent=2)
        
        logger.info(f"Saved preprocessing stats: {stats_path}")
        logger.info("All data saved successfully!")
    
    def run_pipeline(self) -> Dict:
        """
        Run complete preprocessing pipeline
        
        Returns:
            Dictionary with statistics
        """
        logger.info("="*60)
        logger.info("Starting Data Preprocessing Pipeline")
        logger.info("="*60)
        
        # Load configuration
        data_config = self.config['data']
        preprocess_config = self.config['preprocessing']
        
        # Step 1: Load data
        df = self.load_data(data_config['raw_data_path'])
        
        # Step 2: Handle missingness
        df = self.handle_missingness(df)
        
        # Step 3: Handle duplicates
        df = self.handle_duplicates(df)
        
        # Step 4: Clean data
        df = self.clean_data(df)
        
        # Step 5: Filter sparse data
        df = self.filter_sparse_data(
            df,
            min_user_interactions=preprocess_config['min_user_interactions'],
            min_artist_listeners=preprocess_config['min_artist_listeners']
        )
        
        # Step 6: Create implicit feedback
        df = self.create_implicit_feedback(df, alpha=preprocess_config['alpha'])
        
        # Step 7: Train-test split
        train_df, test_df = self.train_test_split(
            df,
            test_size=preprocess_config['test_size'],
            random_seed=preprocess_config['random_seed']
        )
        
        # Step 8: Create mappings
        user_mapping, artist_mapping = self.create_mappings(df)
        
        # Step 9: Create sparse matrix (from train data)
        user_item_matrix = self.create_sparse_matrix(train_df, user_mapping, artist_mapping)
        
        # Step 10: Save everything
        self.save_processed_data(
            train_df, test_df, user_item_matrix,
            user_mapping, artist_mapping,
            data_config['processed_dir']
        )
        
        logger.info("="*60)
        logger.info("Preprocessing Pipeline Complete!")
        logger.info("="*60)
        
        return self.stats


if __name__ == "__main__":
    # Example usage
    import yaml
    
    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    preprocessor = DataPreprocessor(config)
    stats = preprocessor.run_pipeline()
    
    print("\n" + "="*60)
    print("Final Statistics:")
    print("="*60)
    for key, value in stats.items():
        print(f"{key}: {value}")
