"""
Automated MLflow Experiment Runner

Runs 5 different ALS model experiments with varying hyperparameters.
Each experiment is logged to MLflow for comparison.

Usage: python scripts/run_experiments.py
"""

import yaml
import subprocess
import time
import sys
from pathlib import Path

# Experiment configurations
EXPERIMENTS = [
    {
        "name": "Experiment 1: Low Factors",
        "factors": 50,
        "iterations": 15,
        "regularization": 0.01
    },
    {
        "name": "Experiment 2: Medium-Low Factors",
        "factors": 75,
        "iterations": 20,
        "regularization": 0.01
    },
    {
        "name": "Experiment 3: Medium Factors (Baseline)",
        "factors": 100,
        "iterations": 20,
        "regularization": 0.01
    },
    {
        "name": "Experiment 4: Medium-High Factors",
        "factors": 125,
        "iterations": 25,
        "regularization": 0.01
    },
    {
        "name": "Experiment 5: High Factors",
        "factors": 150,
        "iterations": 25,
        "regularization": 0.01
    }
]

CONFIG_PATH = Path("configs/config.yaml")
BACKUP_PATH = Path("configs/config.yaml.backup")


def backup_config():
    """Backup original config file"""
    print("📁 Backing up original config...")
    with open(CONFIG_PATH, 'r') as f:
        original = f.read()
    with open(BACKUP_PATH, 'w') as f:
        f.write(original)
    print(f"✅ Backup saved to {BACKUP_PATH}")


def restore_config():
    """Restore original config file"""
    if BACKUP_PATH.exists():
        print("\n📁 Restoring original config...")
        with open(BACKUP_PATH, 'r') as f:
            original = f.read()
        with open(CONFIG_PATH, 'w') as f:
            f.write(original)
        BACKUP_PATH.unlink()  # Delete backup
        print("✅ Original config restored")


def update_config(factors, iterations, regularization):
    """Update config file with new hyperparameters"""
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update model parameters
    config['model']['factors'] = factors
    config['model']['iterations'] = iterations
    config['model']['regularization'] = regularization
    
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def run_training():
    """Run the training script"""
    result = subprocess.run(
        [sys.executable, 'scripts/train_model.py'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Training failed!")
        print(f"Error: {result.stderr}")
        return False
    
    return True


def print_experiment_header(exp_num, total, exp_config):
    """Print formatted experiment header"""
    print("\n" + "="*70)
    print(f"🔬 {exp_config['name']}")
    print(f"📊 Experiment {exp_num}/{total}")
    print("="*70)
    print(f"📋 Parameters:")
    print(f"   - Factors:        {exp_config['factors']}")
    print(f"   - Iterations:     {exp_config['iterations']}")
    print(f"   - Regularization: {exp_config['regularization']}")
    print("="*70)


def print_summary():
    """Print final summary"""
    print("\n" + "="*70)
    print("🎉 ALL EXPERIMENTS COMPLETED!")
    print("="*70)
    print("\n📊 Next Steps:")
    print("   1. Open MLflow UI: http://localhost:5000")
    print("   2. Go to 'Runs' tab")
    print("   3. Compare all 5 experiments")
    print("   4. Sort by 'metrics.precision_at_10' (highest is best)")
    print("   5. Select best model for production")
    print("\n🔄 To use new model in API:")
    print("   docker-compose restart api")
    print("\n✅ Original config has been restored")
    print("="*70 + "\n")


def main():
    """Main execution function"""
    print("\n" + "🚀" + "="*68 + "🚀")
    print("    AUTOMATED MLFLOW EXPERIMENT RUNNER")
    print("🚀" + "="*68 + "🚀")
    print(f"\n📝 Will run {len(EXPERIMENTS)} experiments")
    print(f"⏱️  Estimated time: ~{len(EXPERIMENTS) * 5} minutes")
    print("\n💡 You can work on other tasks while this runs!")
    print("\nPress Ctrl+C at any time to stop (original config will be restored)")
    
    # Confirm start
    try:
        input("\n👉 Press ENTER to start experiments (or Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return
    
    start_time = time.time()
    
    try:
        # Backup original config
        backup_config()
        
        # Run each experiment
        for i, exp in enumerate(EXPERIMENTS, 1):
            print_experiment_header(i, len(EXPERIMENTS), exp)
            
            # Update config with new parameters
            update_config(
                factors=exp['factors'],
                iterations=exp['iterations'],
                regularization=exp['regularization']
            )
            
            print(f"\n⚙️  Updated config.yaml")
            print(f"🏋️  Training model... (this will take ~5 minutes)")
            
            exp_start = time.time()
            
            # Run training
            success = run_training()
            
            exp_duration = time.time() - exp_start
            
            if not success:
                print(f"\n❌ Experiment {i} failed! Stopping...")
                break
            
            print(f"\n✅ Experiment {i} completed in {exp_duration/60:.2f} minutes")
            print(f"📊 Results logged to MLflow")
            
            # Small delay between experiments
            if i < len(EXPERIMENTS):
                print(f"\n⏳ Starting next experiment in 3 seconds...")
                time.sleep(3)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        print(f"\n⏱️  Total time: {total_time/60:.2f} minutes")
        
        # Print summary
        print_summary()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user!")
        print("🔄 Restoring original config...")
        restore_config()
        print("❌ Experiments stopped")
    
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("🔄 Restoring original config...")
        restore_config()
        raise
    
    else:
        # Restore original config
        restore_config()


if __name__ == "__main__":
    main()
