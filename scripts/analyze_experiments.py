"""
MLflow Experiment Results Analyzer

Reads all MLflow runs and creates a comparison report.
Shows which model performed best.

Usage: python scripts/analyze_experiments.py
"""

import mlflow
import pandas as pd
from pathlib import Path
import json

def get_all_runs():
    """Get all MLflow runs from experiment"""
    
    # Set MLflow tracking URI
    mlflow.set_tracking_uri("file:./mlruns")
    
    # Get experiment (assuming default experiment or first one)
    client = mlflow.tracking.MlflowClient()
    experiments = client.search_experiments()
    
    if not experiments:
        print("❌ No experiments found!")
        return None
    
    # Get runs from first experiment
    experiment_id = experiments[0].experiment_id
    runs = client.search_runs(experiment_ids=[experiment_id])
    
    return runs


def create_comparison_table(runs):
    """Create comparison table from runs"""
    
    results = []
    
    for run in runs:
        # Get metrics
        metrics = run.data.metrics
        params = run.data.params
        
        # Extract relevant info
        result = {
            'Run ID': run.info.run_id[:8],
            'Factors': int(params.get('factors', 0)),
            'Iterations': int(params.get('iterations', 0)),
            'Regularization': float(params.get('regularization', 0)),
            'Precision@10': metrics.get('precision_at_10', 0),
            'MAP@10': metrics.get('map_at_10', 0),
            'NDCG@10': metrics.get('ndcg_at_10', 0),
            'Training Time (min)': metrics.get('training_time_seconds', 0) / 60,
            'Timestamp': run.info.start_time
        }
        
        results.append(result)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Sort by Precision@10 (descending)
    df = df.sort_values('Precision@10', ascending=False)
    
    # Add rank
    df.insert(0, 'Rank', range(1, len(df) + 1))
    
    return df


def print_summary(df):
    """Print formatted summary"""
    
    print("\n" + "="*90)
    print("📊 MLFLOW EXPERIMENT COMPARISON REPORT")
    print("="*90)
    
    # Print full table
    print("\n" + df.to_string(index=False))
    
    print("\n" + "="*90)
    
    # Best model
    best = df.iloc[0]
    
    print("\n🏆 BEST MODEL:")
    print(f"   Rank:           #1")
    print(f"   Run ID:         {best['Run ID']}")
    print(f"   Factors:        {best['Factors']}")
    print(f"   Iterations:     {best['Iterations']}")
    print(f"   Precision@10:   {best['Precision@10']:.6f}")
    print(f"   MAP@10:         {best['MAP@10']:.6f}")
    print(f"   NDCG@10:        {best['NDCG@10']:.6f}")
    print(f"   Training Time:  {best['Training Time (min)']:.2f} minutes")
    
    # Improvement over worst
    worst = df.iloc[-1]
    improvement = ((best['Precision@10'] - worst['Precision@10']) / worst['Precision@10']) * 100
    
    print(f"\n📈 Performance Improvement:")
    print(f"   Best vs Worst: +{improvement:.2f}%")
    
    # Trade-off analysis
    fastest = df.loc[df['Training Time (min)'].idxmin()]
    
    if fastest['Run ID'] != best['Run ID']:
        print(f"\n⚡ Fastest Training:")
        print(f"   Run ID:         {fastest['Run ID']}")
        print(f"   Factors:        {fastest['Factors']}")
        print(f"   Training Time:  {fastest['Training Time (min)']:.2f} minutes")
        print(f"   Precision@10:   {fastest['Precision@10']:.6f}")
        
        precision_loss = ((best['Precision@10'] - fastest['Precision@10']) / best['Precision@10']) * 100
        time_saved = best['Training Time (min)'] - fastest['Training Time (min)']
        
        print(f"\n   Trade-off: {time_saved:.2f} min faster, {precision_loss:.2f}% lower precision")
    
    print("\n" + "="*90)
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    
    if improvement > 10:
        print(f"   ✅ Significant improvement found! Use best model (factors={best['Factors']})")
    elif improvement > 5:
        print(f"   ✅ Moderate improvement. Best model recommended (factors={best['Factors']})")
    else:
        print(f"   ⚠️  Small differences. Consider speed vs accuracy trade-off")
    
    if best['Training Time (min)'] > 8:
        print(f"   ⚠️  Best model takes {best['Training Time (min)']:.1f} min to train")
        print(f"       Consider factors={fastest['Factors']} for faster retraining")
    
    print("\n" + "="*90 + "\n")


def save_report(df):
    """Save report to CSV and JSON"""
    
    # Save CSV
    csv_path = Path("experiments_comparison.csv")
    df.to_csv(csv_path, index=False)
    print(f"💾 Report saved to: {csv_path}")
    
    # Save JSON
    json_path = Path("experiments_comparison.json")
    df.to_json(json_path, orient='records', indent=2)
    print(f"💾 JSON saved to: {json_path}")
    
    # Save best model info
    best = df.iloc[0].to_dict()
    best_path = Path("best_model_info.json")
    with open(best_path, 'w') as f:
        json.dump(best, f, indent=2, default=str)
    print(f"💾 Best model info: {best_path}")


def main():
    """Main execution"""
    
    print("\n🔍 Analyzing MLflow experiments...")
    
    try:
        # Get runs
        runs = get_all_runs()
        
        if not runs:
            print("❌ No runs found!")
            return
        
        print(f"✅ Found {len(runs)} experiment runs")
        
        # Create comparison table
        df = create_comparison_table(runs)
        
        # Print summary
        print_summary(df)
        
        # Save report
        save_report(df)
        
        print("✅ Analysis complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
