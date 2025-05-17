import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from datetime import timedelta
import streamlit as st
import plotly.graph_objects as go

# Load file
file_path = "sales.xlsx"  # Adjust this path for Streamlit Cloud
df = pd.read_excel(file_path)

# Clean columns
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df.rename(columns={"product": "product_name"}, inplace=True)
df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")

# Initialize
trend_results = {}
results = []

# Process each product
for product in df["product_name"].unique():
    product_data = df[df["product_name"] == product].copy().sort_values("date")
    product_data['sales_ma'] = product_data['total_orders'].rolling(window=30, min_periods=1).mean()
    product_data['day_index'] = (product_data['date'] - product_data['date'].min()).dt.days
    X = product_data[['day_index']]
    y = product_data['sales_ma']

    model = LinearRegression()
    model.fit(X, y)
    slope = model.coef_[0]
    r2 = r2_score(y, model.predict(X))

    # Recent activity window
    end_date = product_data['date'].max()
    recent_start_date = end_date - timedelta(days=90)
    recent_data = product_data[product_data['date'] >= recent_start_date]
    recent_avg = recent_data['total_orders'].mean() if not recent_data.empty else 0
    zero_sales_pct = (recent_data['total_orders'] == 0).sum() / len(recent_data) if not recent_data.empty else 1.0

    # Classification
    if slope > 0.05 and r2 > 0.3:
        category = "Growing"
    elif slope < -0.05 and r2 > 0.3:
        category = "Decaying"
    elif -0.05 <= slope <= 0.05 and r2 < 0.3 and recent_avg >= 1:
        category = "Flat"
    elif recent_avg < 1 or zero_sales_pct > 0.5:
        category = "Obsolete"
    else:
        category = "Unclassified"

    # Save results
    results.append({
        "product": product,
        "slope": round(slope, 4),
        "r_squared": round(r2, 4),
        "recent_avg_sales": round(recent_avg, 2),
        "zero_sales_pct_last_90d": round(zero_sales_pct, 2),
        "category": category
    })

    trend_results[product] = {
        "df": product_data,
        "category": category
    }

# UI
st.title("📈 Trend and Growth Classification")

# Display trend summary table
results_df = pd.DataFrame(results)
st.dataframe(results_df)

# Select product to view chart
selected_product = st.selectbox("Select a product to view its trend", results_df["product"])

# Plot
if selected_product:
    data = trend_results[selected_product]["df"]
    category = trend_results[selected_product]["category"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["date"], y=data["total_orders"], mode='lines', name='Daily Sales', line=dict(color='lightgray')))
    fig.add_trace(go.Scatter(x=data["date"], y=data["sales_ma"], mode='lines', name='30-day MA', line=dict(color='blue')))
    fig.update_layout(
        title=f"{selected_product} – Classified as: {category}",
        xaxis_title="Date",
        yaxis_title="Sales",
        template="plotly_white",
        height=450
    )
    st.plotly_chart(fig, use_container_width=True)
