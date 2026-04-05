# train_model.py
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error, r2_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import warnings
warnings.filterwarnings('ignore')

# ------------------------------------------------------------
# 0. Locate the dataset file (flexible path)
# ------------------------------------------------------------

possible_paths = [
    'data/final/daily_vegetable_prices_cleaned.csv',           # if running from project root
    '../data/final/daily_vegetable_prices_cleaned.csv',        # if running from AM_DataExtract/
    '../../data/final/daily_vegetable_prices_cleaned.csv',     # if deeper
    '../../../data/final/daily_vegetable_prices_cleaned.csv',
    'AM_DataExtract/data/final/daily_vegetable_prices_cleaned.csv'
]

csv_path = None
for path in possible_paths:
    if os.path.exists(path):
        csv_path = path
        break

if csv_path is None:
    raise FileNotFoundError(
        "Could not find daily_vegetable_prices.csv. "
        "Please check that the file exists and adjust possible_paths."
    )

print(f"Loading data from: {csv_path}")

# ------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------
df = pd.read_csv(csv_path, parse_dates=['Date'])
print(f"Original shape: {df.shape}")
df = df.dropna(subset=['Avg_Price'])

# ------------------------------------------------------------
# 2. Add time features
# ------------------------------------------------------------
df['year'] = df['Date'].dt.year
df['month'] = df['Date'].dt.month
df['day'] = df['Date'].dt.day
df['dayofweek'] = df['Date'].dt.dayofweek
df['quarter'] = df['Date'].dt.quarter

# Cyclic encoding
df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
df['dow_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
df['dow_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)

# ------------------------------------------------------------
# 3. Lag features (past prices)
# ------------------------------------------------------------
def add_lags(group, lags=[1,2,3,7,14,30]):
    group = group.sort_values('Date')
    for lag in lags:
        group[f'lag_{lag}'] = group['Avg_Price'].shift(lag)
    return group

df = df.groupby(['Crop', 'Market']).apply(add_lags).reset_index(drop=True)

# ------------------------------------------------------------
# 4. Rolling statistics
# ------------------------------------------------------------
def add_rolling_stats(group, windows=[7,14,30]):
    for w in windows:
        group[f'rolling_mean_{w}'] = group['Avg_Price'].rolling(w, min_periods=1).mean()
        group[f'rolling_std_{w}'] = group['Avg_Price'].rolling(w, min_periods=1).std()
    return group

df = df.groupby(['Crop', 'Market']).apply(add_rolling_stats).reset_index(drop=True)

# Drop rows with NaN from lags
df = df.dropna().reset_index(drop=True)
print(f"After feature engineering: {df.shape}")

# ------------------------------------------------------------
# 5. Encode categorical variables
# ------------------------------------------------------------
le_crop = LabelEncoder()
le_market = LabelEncoder()
df['crop_encoded'] = le_crop.fit_transform(df['Crop'])
df['market_encoded'] = le_market.fit_transform(df['Market'])

joblib.dump(le_crop, 'le_crop.pkl')
joblib.dump(le_market, 'le_market.pkl')

# ------------------------------------------------------------
# 6. Define features and target
# ------------------------------------------------------------
feature_columns = [
    'crop_encoded', 'market_encoded',
    'year', 'month', 'day', 'dayofweek', 'quarter',
    'month_sin', 'month_cos', 'dow_sin', 'dow_cos',
    'lag_1', 'lag_2', 'lag_3', 'lag_7', 'lag_14', 'lag_30',
    'rolling_mean_7', 'rolling_mean_14', 'rolling_mean_30',
    'rolling_std_7', 'rolling_std_14', 'rolling_std_30'
]

X = df[feature_columns]
y = df['Avg_Price']

# ------------------------------------------------------------
# 7. Chronological train/test split
# ------------------------------------------------------------
df_sorted = df.sort_values('Date')
split_date = '2025-01-01'

train_mask = df_sorted['Date'] < split_date
test_mask = df_sorted['Date'] >= split_date

X_train = df_sorted.loc[train_mask, feature_columns]
y_train = df_sorted.loc[train_mask, 'Avg_Price']
X_test = df_sorted.loc[test_mask, feature_columns]
y_test = df_sorted.loc[test_mask, 'Avg_Price']

print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
joblib.dump(scaler, 'scaler.pkl')

# ------------------------------------------------------------
# 8. Train models (only tree-based, no TensorFlow)
# ------------------------------------------------------------
rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
rf.fit(X_train_scaled, y_train)
y_pred_rf = rf.predict(X_test_scaled)

gbr = GradientBoostingRegressor(n_estimators=100, random_state=42)
gbr.fit(X_train_scaled, y_train)
y_pred_gbr = gbr.predict(X_test_scaled)

# ------------------------------------------------------------
# 9. Evaluate
# ------------------------------------------------------------
def evaluate(y_true, y_pred, name):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = mean_absolute_percentage_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    print(f"{name:20} | MAE: {mae:6.2f} | RMSE: {rmse:6.2f} | MAPE: {mape:6.2%} | R²: {r2:.4f}")
    return {'model': name, 'MAE': mae, 'RMSE': rmse, 'MAPE': mape, 'R2': r2}

results = []
results.append(evaluate(y_test, y_pred_rf, 'Random Forest'))
results.append(evaluate(y_test, y_pred_gbr, 'Gradient Boosting'))

# Save comparison
pd.DataFrame(results).to_csv('model_comparison.csv', index=False)

# ------------------------------------------------------------
# 10. Save best model (based on RMSE)
# ------------------------------------------------------------
best_rmse = min(r['RMSE'] for r in results)
best_model = rf if results[0]['RMSE'] == best_rmse else gbr
joblib.dump(best_model, 'best_price_model.pkl')
print(f"\nBest model saved: {type(best_model).__name__} with RMSE = {best_rmse:.2f}")