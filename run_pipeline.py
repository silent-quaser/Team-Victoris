"""Run full data + ML pipeline."""
import sys
sys.path.insert(0, 'd:/GridGuard')

# Step 1: Run preprocessing
print('=== Step 1: Data Preprocessing ===')
from data_pipeline.preprocessor import run_preprocessing
out = run_preprocessing()
print('Profiles:', list(out.keys()))

# Step 2: Generate 2000 synthetic scenarios
print('=== Step 2: Scenario Generation ===')
from scenario.generator import run_generation
dfs = run_generation(n=2000, seed=42)
for name, df in dfs.items():
    print(f'  {name}: {len(df)} rows')

# Step 3: Train ML model
print('=== Step 3: ML Training ===')
from ml.trainer import train
metrics = train(verbose=True)
print('ROC-AUC:', metrics['roc_auc'])
print('Accuracy:', metrics['accuracy'])
print('F1-Score:', metrics['f1_score'])
print('DONE')
