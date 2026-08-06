import pandas as pd
from sklearn.metrics import roc_auc_score

from graph.context import CATEGORICAL_FEATURES, DATASET_PATH, NUMERIC_FEATURES

df = pd.read_csv(DATASET_PATH)
y = df["fraud_label"].astype(int)

print("=" * 60)
print("DATASET LABEL CHECK")
print("=" * 60)
print(f"Transactions : {len(df)}")
print(f"Fraud rows   : {y.sum()} ({y.mean() * 100:.2f}%)")

print("\nSingle-feature AUC (0.50 = no signal)")
print("-" * 60)

for column in NUMERIC_FEATURES:
    auc = roc_auc_score(y, df[column])
    print(f"{column:<30} {auc:.4f}")

print("\nFraud rate by category")
print("-" * 60)

for column in CATEGORICAL_FEATURES:
    rates = df.groupby(column)["fraud_label"].mean() * 100
    spread = rates.max() - rates.min()
    print(f"{column:<20} spread {spread:.2f} percentage points")

print("\nMean value: fraud vs legit")
print("-" * 60)

for column in NUMERIC_FEATURES:
    fraud_mean = df.loc[y == 1, column].mean()
    legit_mean = df.loc[y == 0, column].mean()
    gap = abs(fraud_mean - legit_mean) / max(abs(legit_mean), 1e-9) * 100
    print(f"{column:<30} fraud {fraud_mean:>10.2f} | legit {legit_mean:>10.2f} | diff {gap:.1f}%")

print("\n" + "=" * 60)
print("Verdict: if every AUC sits near 0.50 and the gaps are small,")
print("the labels carry no information about the features.")
print("=" * 60)
