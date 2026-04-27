import pandas as pd
df = pd.read_parquet('phase1/artifacts/zomato_clean.parquet')
bell = df[df['location'].str.contains('bellandur', case=False, na=False)]
print("Total Bellandur:", len(bell))
print("Bellandur cost notna count:", bell['cost'].notna().sum())
print("Bellandur max cost:", bell['cost'].max())
print("Bellandur rating notna count:", bell['rating'].notna().sum())
