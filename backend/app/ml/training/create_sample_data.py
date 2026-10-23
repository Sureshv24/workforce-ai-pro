import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
n = 1200

age = rng.integers(21, 61, n)
monthly_income = rng.integers(1800, 20001, n)
years_at_company = rng.integers(0, 21, n)
job_satisfaction = rng.integers(1, 5, n)
work_life_balance = rng.integers(1, 5, n)
overtime = rng.choice(["Yes", "No"], n, p=[0.35, 0.65])
years_since_promotion = np.array([
    rng.integers(0, max(1, min(11, y + 1))) for y in years_at_company
])
distance_from_home = rng.integers(1, 31, n)

# Synthetic label for pipeline testing only.
logit = (
    -1.0
    + 0.9 * (overtime == "Yes")
    + 0.45 * (job_satisfaction == 1)
    + 0.35 * (work_life_balance == 1)
    + 0.035 * distance_from_home
    - 0.09 * years_at_company
    - 0.00006 * monthly_income
    + 0.08 * years_since_promotion
)
probability = 1 / (1 + np.exp(-logit))
attrition = rng.binomial(1, probability)

df = pd.DataFrame({
    "age": age,
    "monthly_income": monthly_income,
    "years_at_company": years_at_company,
    "job_satisfaction": job_satisfaction,
    "work_life_balance": work_life_balance,
    "overtime": overtime,
    "years_since_promotion": years_since_promotion,
    "distance_from_home": distance_from_home,
    "attrition": attrition,
})

output = Path("app/ml/datasets/attrition_sample.csv")
df.to_csv(output, index=False)

print(f"Dataset created: {output}")
print(f"Rows: {len(df)}")
print("\nAttrition label distribution:")
print(df["attrition"].value_counts().sort_index())
