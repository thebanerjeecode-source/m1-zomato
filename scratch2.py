import pandas as pd
df = pd.read_parquet('phase1/artifacts/zomato_clean.parquet')
print(df[df['name'].str.contains("Chili", na=False)][['name', 'cost']].head())
