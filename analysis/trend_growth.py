import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from datetime import timedelta
import streamlit as st
import plotly.graph_objects as go

# Load file
file_path = "sales.xlsx"
df = pd.read_excel(file_path)

# Clean columns
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
df.rename(columns={"product": "product_name"}, inplace=True)
df["date"] = pd.to_datetime(df["date"])

# Aggregate daily sales into monthly totals
df["month"] = df["date"].dt.to_period("M")
monthly_df = df.groupby(["product_name", "month"]).agg({"total_orders": "sum"}).reset_index()
monthly_df["month"] = monthly_df["month"].dt.to_timestamp()

# Initialize
trend_results = []
plot_data_map = {}

# Process each product
for product in monthly_df["product_name"].unique():
    product_data = monthly_df[monthly_df["product_name"] == product].copy().sort_values("month")
    product_data["month_index"] = (product_data["month"] - product_data["month"].min()).dt.days

    X = product_data[["month_index"]]
    y = product_data["total_orders"]

    model = LinearRegression()
    model.fit(X, y)
    slope = model.coef_[0]
    r2 = r2_score(y, model.predict(X))

    # Recent activity window (last 3 months)
    end_date = product_data["month"].max()
    recent_start_date = end_date - pd.DateOffset(months=3)
    recent_data = product_data[product_data["month"] >= recent_start_date]
    recent_avg = recent_data["total_orders"].mean() if not recent_data.empty else 0
    zero_sales_pct = (recent_data["total_orders"] == 0).sum() / len(recent_data) if not recent_data.empty else 1.0

    # Classification (monthly-level thresholds)
    if slope > 5 and r2 > 0.3:
        category = "Growing"
    elif slope < -5 and r2 > 0.3:
        category = "Decaying"
    elif -5 <= slope <= 5 and r2 < 0.3 and recent_avg >= 1:
        category = "Flat"
    elif recent_avg < 1 or zero_sales_pct > 0.5:
        category = "Obsolete"
    else:
        category = "Unclassified"

    # Store results
    trend_results.append({
        "product": product,
        "slope": round(slope, 4),
        "r_squared": round(r2, 4),
        "recent_avg_sales": round(recent_avg, 2),
        "zero_sales_pct_last_3m": round(zero_sales_pct, 2),
        "category": category
    })
    plot_data_map[product] = {"df": product_data, "category": category}

# UI
st.title("📈 Monthly Sales Trend Classification")

results_df = pd.DataFrame(trend_results)
st.dataframe(results_df)

selected_product = st.selectbox("Select a product to view its trend", results_df["product"])

if selected_product:
    product_info = plot_data_map[selected_product]
    chart_df = product_info["df"]
    category = product_info["category"]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=chart_df["month"], y=chart_df["total_orders"], name="Monthly Sales", marker_color="blue"))
    fig.update_layout(
        title=f"{selected_product} – Classified as: {category}",
        xaxis_title="Month",
        yaxis_title="Total Orders",
        template="plotly_white",
        height=450
    )
    st.plotly_chart(fig, use_container_width=True)

