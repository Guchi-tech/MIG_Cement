import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Load Data
kpi_summary = pd.read_csv("historical_kpi_summary.csv")
results_df = pd.read_parquet("cement_forecast_results.parquet")

results_df["date"] = pd.to_datetime(results_df["date"])

# Streamlit Page Settings
st.set_page_config(page_title="MIG Cement Operational Planner", layout="wide")

st.title("MIG Cement Operational Planner")

# Site Dropdown
site_list = sorted(results_df["site_id"].unique())
site_id = st.selectbox("Select Site:", site_list)

site_df = results_df[results_df["site_id"] == site_id].copy()

# Compute KPIs
total_forecast = site_df["forecasted_consumption"].sum()
total_reorders = site_df["reorder_flag"].sum()
avg_inventory = site_df["sim_inventory"].mean()
silo_capacity = kpi_summary[kpi_summary['site_id'] == site_id]['silo_capacity'].values[0]
util_rate = (avg_inventory / silo_capacity) * 100

# KPI Display
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Forecasted Consumption", f"{total_forecast:,.0f} t")
col2.metric("Planned Reorders", f"{total_reorders}")
col3.metric("Average Inventory", f"{avg_inventory:,.0f} t")
col4.metric("Utilization Rate", f"{util_rate:.1f}%")

# Inventory Chart
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=site_df["date"], y=site_df["sim_inventory"],
    mode="lines", name="Simulated Inventory",
    fill='tozeroy'
))
fig.add_trace(go.Bar(
    x=site_df["date"], y=site_df["forecasted_consumption"],
    name="Forecasted Consumption", opacity=0.6
))
reorder_points = site_df[site_df["reorder_flag"] == True]
fig.add_trace(go.Scatter(
    x=reorder_points["date"], y=reorder_points["sim_inventory"],
    mode="markers", name="Reorder Trigger",
    marker=dict(color="red", size=10, symbol="x")
))

fig.update_layout(
    title=f"Inventory & Demand Forecast - {site_id}",
    xaxis_title="Date",
    yaxis_title="Inventory (t)",
    height=450
)

st.plotly_chart(fig, use_container_width=True)

# Reorder Table
reorder_data = site_df[site_df["reorder_flag"] == True][[
    "date", "sim_inventory", "recommended_delivery_date",
    "recommended_delivery_quantity", "buffer_applied"
]].copy()

reorder_data['date'] = reorder_data['date'].dt.strftime('%Y-%m-%d')

st.subheader("Upcoming Reorder Recommendations")
st.dataframe(reorder_data, use_container_width=True)
# Download Reorder Table
@st.cache_data
def convert_to_excel(df):
    return df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Reorder Schedule (CSV)",
    data=convert_to_excel(reorder_data),
    file_name=f"reorder_schedule_{site_id}.csv",
    mime="text/csv"
)
