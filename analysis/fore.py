import pandas as pd
from prophet import Prophet
from datetime import timedelta

# Load the Excel file (assumed same format as before)
file_path = "/mnt/data/sales_data_1year.xlsx"
df = pd.read_excel(file_path)

# Rename for Prophet compatibility
df.rename(columns={"date": "ds", "total_orders": "y", "product": "product_name"}, inplace=True)
df["ds"] = pd.to_datetime(df["ds"])

# Create a directory to store all forecasts (optional visualization step)
forecast_dfs = []

# Run forecasting for each product
for product in df["product_name"].unique():
    df_prod = df[df["product_name"] == product][["ds", "y"]].copy()

    # If enough data, use Prophet
    if df_prod.shape[0] >= 60 and df_prod["y"].sum() >= 10:
        model = Prophet(daily_seasonality=True, yearly_seasonality=True)
        model.fit(df_prod)

        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)

        forecast = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        forecast["product_name"] = product

    else:
        # Fallback forecast using average of past 30 days or entire series
        if not df_prod.empty:
            mean_y = df_prod.tail(30)["y"].mean() if df_prod.shape[0] >= 30 else df_prod["y"].mean()
            last_date = df_prod["ds"].max()
        else:
            mean_y = 0
            last_date = pd.to_datetime("2025-04-30")  # default end date

        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=30)

        forecast = pd.DataFrame({
            "ds": future_dates,
            "yhat": [mean_y] * 30,
            "yhat_lower": [mean_y * 0.9] * 30,
            "yhat_upper": [mean_y * 1.1] * 30,
            "product_name": product
        })

    forecast_dfs.append(forecast)

# Combine all forecasts
df_all_forecasts = pd.concat(forecast_dfs, ignore_index=True)
import ace_tools as tools; tools.display_dataframe_to_user(name="30-Day Forecast (with Fallback)", dataframe=df_all_forecasts)
