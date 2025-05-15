import pandas as pd
from prophet import Prophet
from datetime import timedelta
import matplotlib.pyplot as plt

# Load your Excel file (replace with actual path)
file_path = "sales.xlsx"  # Example filename
df = pd.read_excel(file_path)

# Rename for Prophet
df.rename(columns={"date": "ds", "total_orders": "y", "product": "product_name"}, inplace=True)

# Ensure date is datetime
df["ds"] = pd.to_datetime(df["ds"])

# Store results
results = []

# Iterate over each product
for product in df["product_name"].unique():
    df_prod = df[df["product_name"] == product][["ds", "y"]].copy()

    # Skip very low-activity SKUs
    if df_prod["y"].sum() < 10:
        continue

    # Initialize and train model
    model = Prophet(daily_seasonality=True, yearly_seasonality=True)
    model.fit(df_prod)

    # Forecast next 30 days
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)

    # Compute metrics
    forecast_next_30 = forecast.tail(30)["yhat"].mean()
    recent_past = df_prod[df_prod["ds"] > df_prod["ds"].max() - timedelta(days=60)]
    past_60_avg = recent_past["y"].mean()
    trend_slope = forecast["trend"].tail(30).diff().mean()
    seasonal_cols = [col for col in forecast.columns if col in ["weekly", "yearly", "daily"] and col in forecast]
    seasonality_strength = forecast[seasonal_cols].sum(axis=1).std() if seasonal_cols else 0


    # Insight tagging
    if forecast_next_30 < past_60_avg * 0.5 and trend_slope < 0:
        label = "Decaying"
    elif forecast_next_30 > past_60_avg * 1.2 and trend_slope > 0:
        label = "Growing"
    elif forecast_next_30 < 2 and past_60_avg < 2 and abs(trend_slope) < 0.1:
        label = "Flat / Obsolete"
    elif seasonal_strength > 2 and forecast_next_30 > past_60_avg:
        label = "Seasonally Quiet"
    else:
        label = "Stable / Uncertain"

    results.append({
        "product_name": product,
        "forecast_avg": round(forecast_next_30, 2),
        "past_60d_avg": round(past_60_avg, 2),
        "trend_slope": round(trend_slope, 3),
        "seasonality_strength": round(seasonal_strength, 3),
        "insight_label": label
    })

# Convert to DataFrame and display
df_results = pd.DataFrame(results)
import ace_tools as tools; tools.display_dataframe_to_user(name="Product Insight Forecasting Results", dataframe=df_results)
