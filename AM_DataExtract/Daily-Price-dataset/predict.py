# predict.py
import pandas as pd
import numpy as np
import joblib
import os

# ====================== FULL PATHS ======================
# Put the correct full path to your CSV here
CSV_PATH = r"C:\Users\HP\Desktop\My Daily price\Daily-Price-dataset\AM_DataExtract\data\final\daily_vegetable_prices_cleaned.csv"

# If your .pkl files are in the same folder as predict.py, leave these as is.
# Otherwise, change them to full paths too.
MODEL_PATH = 'best_price_model.pkl'
SCALER_PATH = 'scaler.pkl'
LE_CROP_PATH = 'le_crop.pkl'
LE_MARKET_PATH = 'le_market.pkl'
# =======================================================

# Load models and data
print("Loading model and data...")

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
le_crop = joblib.load(LE_CROP_PATH)
le_market = joblib.load(LE_MARKET_PATH)

df_history = pd.read_csv(CSV_PATH, parse_dates=['Date'])
print(f"✅ Data loaded successfully! Shape: {df_history.shape}")

# Feature columns (must match training)
feature_columns = [
    'crop_encoded', 'market_encoded',
    'year', 'month', 'day', 'dayofweek', 'quarter',
    'month_sin', 'month_cos', 'dow_sin', 'dow_cos',
    'lag_1', 'lag_2', 'lag_3', 'lag_7', 'lag_14', 'lag_30',
    'rolling_mean_7', 'rolling_mean_14', 'rolling_mean_30',
    'rolling_std_7', 'rolling_std_14', 'rolling_std_30'
]

def predict_price(date, market, crop):
    date = pd.to_datetime(date)
    
    # Normalize names
    crop = crop.lower().strip()
    market = market.lower().capitalize().strip()
    
    # Get historical data for this crop & market
    hist = df_history[
        (df_history['Crop'].str.lower().str.strip() == crop) &
        (df_history['Market'].str.lower().str.strip() == market.lower())
    ].sort_values('Date')
    
    if len(hist) < 30:
        raise ValueError(f"Not enough history for '{crop}' in '{market}'. Found only {len(hist)} days.")
    
    # Build features
    row = {
        'crop_encoded': le_crop.transform([crop])[0],
        'market_encoded': le_market.transform([market])[0],
        'year': date.year,
        'month': date.month,
        'day': date.day,
        'dayofweek': date.dayofweek,
        'quarter': date.quarter,
        'month_sin': np.sin(2 * np.pi * date.month / 12),
        'month_cos': np.cos(2 * np.pi * date.month / 12),
        'dow_sin': np.sin(2 * np.pi * date.dayofweek / 7),
        'dow_cos': np.cos(2 * np.pi * date.dayofweek / 7),
    }
    
    recent_prices = hist['Avg_Price'].tail(30).values
    
    # Lag features
    for lag in [1, 2, 3, 7, 14, 30]:
        row[f'lag_{lag}'] = recent_prices[-lag] if len(recent_prices) >= lag else recent_prices[0] if len(recent_prices) > 0 else 0
    
    # Rolling features
    for w in [7, 14, 30]:
        if len(recent_prices) >= w:
            row[f'rolling_mean_{w}'] = np.mean(recent_prices[-w:])
            row[f'rolling_std_{w}'] = np.std(recent_prices[-w:])
        else:
            row[f'rolling_mean_{w}'] = np.mean(recent_prices)
            row[f'rolling_std_{w}'] = np.std(recent_prices) if len(recent_prices) > 1 else 0
    
    # Predict
    X_pred = pd.DataFrame([row])[feature_columns]
    X_pred_scaled = scaler.transform(X_pred)
    price = model.predict(X_pred_scaled)[0]
    
    return max(0.0, round(float(price), 2))


# ====================== TEST ======================
if __name__ == "__main__":
    try:
        test_price = predict_price('2025-04-10', 'Dambulla', 'tomato')
        print(f"\n✅ Predicted price for tomato in Dambulla on 2025-04-10: Rs. {test_price:.2f}/kg")
        
        # Optional: Test another one
        # test2 = predict_price('2025-04-15', 'Colombo', 'beans')
        # print(f"Predicted for beans in Colombo: Rs. {test2:.2f}/kg")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()