import pandas as pd
from prophet import Prophet
from datetime import timedelta
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="30-Day Sales Forecast", layout="wide")
st.title("📈 30-Day Sales Forecast (Prophet + Fallback)")

# --- Step 1: Forecast for all products once and cache it ---
@st.cache_data
def run_forecasting():
    file_path = "sales.xlsx"  # Make sure this file is in the same directory
    df = pd.read_excel(file_path)

    df.rename(columns={"date": "ds", "total_orders": "y", "product": "product_name"}, inplace=True)
    df["ds"] = pd.to_datetime(df["ds"])

    forecast_dfs = []

    for product in df["product_name"].unique():
        df_prod = df[df["product_name"] == product][["ds", "y"]].copy()

        if df_prod.shape[0] >= 60 and df_prod["y"].sum() >= 10:
            model = Prophet(daily_seasonality=True, yearly_seasonality=True)
            model.fit(df_prod)

            future = model.make_future_dataframe(periods=30)
            forecast = model.predict(future)

            forecast = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
            forecast["product_name"] = product
        else:
            if not df_prod.empty:
                mean_y = df_prod.tail(30)["y"].mean() if df_prod.shape[0] >= 30 else df_prod["y"].mean()
                last_date = df_prod["ds"].max()
            else:
                mean_y = 0
                last_date = pd.to_datetime("2025-01-01")

            future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=30)

            forecast = pd.DataFrame({
                "ds": future_dates,
                "yhat": [mean_y] * 30,
                "yhat_lower": [mean_y * 0.9] * 30,
                "yhat_upper": [mean_y * 1.1] * 30,
                "product_name": product
            })

        forecast_dfs.append(forecast)

    df_all_forecasts = pd.concat(forecast_dfs, ignore_index=True)
    return df_all_forecasts

# --- Load precomputed forecast ---
df_all_forecasts = run_forecasting()

# --- Streamlit UI ---
product_list = sorted(df_all_forecasts["product_name"].unique())
selected_product = st.selectbox("🔍 Select a product to view forecast", product_list)

# Filter to 30-day forecast only
df_selected = df_all_forecasts[
    (df_all_forecasts["product_name"] == selected_product) &
    (df_all_forecasts["ds"] > pd.to_datetime("2025-01-01"))
]

# Total forecasted sales for next 30 days
total_forecast = df_selected["yhat"].sum()

# Display metric
st.markdown(f"### 📦 Total Predicted Sales for Next 30 Days: `{total_forecast:.2f}` units")

# --- Plotly Chart ---
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_selected["ds"], y=df_selected["yhat"],
    mode='lines', name='Forecast (yhat)', line=dict(color='blue')
))

fig.add_trace(go.Scatter(
    x=df_selected["ds"], y=df_selected["yhat_upper"],
    mode='lines', name='Upper Bound', line=dict(dash='dash', color='lightblue')
))

fig.add_trace(go.Scatter(
    x=df_selected["ds"], y=df_selected["yhat_lower"],
    mode='lines', name='Lower Bound', line=dict(dash='dash', color='lightblue'),
    fill='tonexty', fillcolor='rgba(173,216,230,0.2)'
))

fig.update_layout(
    title=f"30-Day Forecast for '{selected_product}'",
    xaxis_title="Date",
    yaxis_title="Predicted Daily Sales",
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# Optional raw table
with st.expander("📄 Show Forecast Table"):
    st.dataframe(df_selected, use_container_width=True)
