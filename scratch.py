import pandas as pd
df = pd.read_parquet('phase1/artifacts/zomato_clean.parquet')
print("Total rows:", len(df))
print("Cost notna count:", df['cost'].notna().sum())
print("Rating notna count:", df['rating'].notna().sum())
print(df[['name', 'location', 'cost', 'rating']].head(10))
