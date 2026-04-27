from datasets import load_dataset
ds = load_dataset('ManikaSaini/zomato-restaurant-recommendation')['train']
df = ds.to_pandas()
chili = df[df['name'].str.contains("Chili's American Grill", na=False)]
print(chili[['name', 'approx_cost(for two people)', 'rate']].head())
