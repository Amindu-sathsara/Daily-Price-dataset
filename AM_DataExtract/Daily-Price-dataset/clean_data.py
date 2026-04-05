import pandas as pd
import numpy as np

# Path to your raw data
RAW_DATA_PATH = '../data/final/daily_vegetable_prices.csv'
CLEANED_DATA_PATH = '../data/final/daily_vegetable_prices_cleaned.csv'

# Load data

df = pd.read_csv(RAW_DATA_PATH)
print(f'Original shape: {df.shape}')
print('Columns:', list(df.columns))

# Drop duplicates
df = df.drop_duplicates()


# Drop rows with missing values in critical columns (customize as needed)
critical_cols = ['Date', 'Market', 'Crop', 'Avg_Price']
df = df.dropna(subset=critical_cols)

# Convert Avg_Price to numeric (force errors to NaN, then drop)
df['Avg_Price'] = pd.to_numeric(df['Avg_Price'], errors='coerce')
df = df.dropna(subset=['Avg_Price'])

# Outlier removal using IQR method (for Avg_Price)
Q1 = df['Avg_Price'].quantile(0.25)
Q3 = df['Avg_Price'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
df = df[(df['Avg_Price'] >= lower_bound) & (df['Avg_Price'] <= upper_bound)]

print(f'After cleaning: {df.shape}')

# Save cleaned data
df.to_csv(CLEANED_DATA_PATH, index=False)
print(f'Cleaned data saved to: {CLEANED_DATA_PATH}')
