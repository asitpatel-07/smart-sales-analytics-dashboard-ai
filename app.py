import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Smart Sales Dashboard", layout="wide")

st.title("📊 Smart Sales Analytics Dashboard")

# Initialize data
if "sales_data" not in st.session_state:
    st.session_state.sales_data = pd.DataFrame(
        columns=["Date","Product","Sales","Profit/Loss","Type"]
    )

# -----------------------------
# Sidebar Input
# -----------------------------

st.sidebar.header("Enter Sales Data")

date = str(st.sidebar.date_input("Date"))
product = st.sidebar.text_input("Product Name")
sales = st.sidebar.number_input("Sales Amount", min_value=0)
profit_loss = st.sidebar.number_input("Profit/Loss (negative for loss)")

entry_type = "Profit" if profit_loss >= 0 else "Loss"

if st.sidebar.button("Add Data"):

    new_data = pd.DataFrame(
        [[date,product,sales,profit_loss,entry_type]],
        columns=["Date","Product","Sales","Profit/Loss","Type"]
    )

    st.session_state.sales_data = pd.concat(
        [st.session_state.sales_data,new_data],
        ignore_index=True
    )

df = st.session_state.sales_data

df["Date"] = pd.to_datetime(df["Date"]).astype(str)

# -----------------------------
# Sales Data Table
# -----------------------------

st.subheader("📋 Sales Data Table")

df_display = df.copy()
df_display.index = df_display.index + 1

st.dataframe(df_display)

# -----------------------------
# Delete Wrong Entry
# -----------------------------

st.subheader("🗑 Delete Wrong Entry")

if not df.empty:

    row_number = st.number_input(
        "Enter Row Number to Delete",
        min_value=1,
        max_value=len(df),
        step=1
    )

    if st.button("Delete Row"):

        st.session_state.sales_data = st.session_state.sales_data.drop(row_number-1)
        st.session_state.sales_data = st.session_state.sales_data.reset_index(drop=True)

        st.success("Row deleted successfully!")

# -----------------------------
# Date Filter
# -----------------------------

st.subheader("📅 Filter Sales Data")

if not df.empty:

    df["Date"] = pd.to_datetime(df["Date"])

    selected_date = st.selectbox(
        "Select Date",
        ["All Dates"] + list(df["Date"].dt.date.unique())
    )

    if selected_date != "All Dates":
        filtered_df = df[df["Date"].dt.date == selected_date]
    else:
        filtered_df = df

# -----------------------------
# Metrics
# -----------------------------

    total_sales = filtered_df["Sales"].sum()
    total_profit = filtered_df[filtered_df["Type"]=="Profit"]["Profit/Loss"].sum()
    total_loss = filtered_df[filtered_df["Type"]=="Loss"]["Profit/Loss"].sum()
    net_result = filtered_df["Profit/Loss"].sum()

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Total Sales", f"₹{total_sales}")
    col2.metric("Total Profit", f"₹{total_profit}")
    col3.metric("Total Loss", f"₹{total_loss}")
    col4.metric("Net Result", f"₹{net_result}")

# -----------------------------
# Business Insights
# -----------------------------

    st.subheader("🧠 Business Insights")

    top_product = filtered_df.groupby("Product")["Sales"].sum().idxmax()

    profit_products = filtered_df[filtered_df["Type"]=="Profit"]

    if not profit_products.empty:
        best_profit_product = profit_products.groupby("Product")["Profit/Loss"].sum().idxmax()
    else:
        best_profit_product = "No Profit Data"

    loss_products = filtered_df[filtered_df["Type"]=="Loss"]["Product"].unique()

    if len(loss_products) > 0:
        loss_list = ", ".join(loss_products)
    else:
        loss_list = "No Loss Detected"

    net_profit = filtered_df["Profit/Loss"].sum()

    if net_profit > 0:
        status = "Business is in Profit 📈"
    elif net_profit < 0:
        status = "Business is in Loss 📉"
    else:
        status = "No Profit No Loss"

    st.info(f"""
Top Selling Product → **{top_product}**

Highest Profit Product → **{best_profit_product}**

Loss Detected In → **{loss_list}**

Business Status → **{status}**
""")

# -----------------------------
# Sales Trend
# -----------------------------

    st.subheader("📈 Sales Trend")

    trend = px.line(filtered_df, x="Date", y="Sales", markers=True)
    st.plotly_chart(trend, use_container_width=True)

# -----------------------------
# Product Sales Chart
# -----------------------------

    st.subheader("🏆 Sales by Product")

    product_sales = filtered_df.groupby("Product")["Sales"].sum().reset_index()

    bar = px.bar(product_sales, x="Product", y="Sales", color="Product")
    st.plotly_chart(bar, use_container_width=True)

# -----------------------------
# Profit vs Loss Chart
# -----------------------------

    st.subheader("💰 Profit vs Loss")

    profit_loss_chart = filtered_df.groupby(["Product","Type"])["Profit/Loss"].sum().reset_index()

    chart = px.bar(
        profit_loss_chart,
        x="Product",
        y="Profit/Loss",
        color="Type",
        barmode="group",
        color_discrete_map={
            "Profit":"green",
            "Loss":"red"
        }
    )

    st.plotly_chart(chart, use_container_width=True)

# -----------------------------
# AI Sales Prediction
# -----------------------------

    st.subheader("🤖 AI Sales Prediction")

    if len(filtered_df) > 2:

        prediction_days = st.slider("Predict Next Days",1,30,7)

        df_ai = filtered_df.copy()
        df_ai = df_ai.sort_values("Date")

        df_ai["Day"] = (df_ai["Date"] - df_ai["Date"].min()).dt.days

        X = df_ai[["Day"]]
        y = df_ai["Sales"]

        model = LinearRegression()
        model.fit(X,y)

        future_days = np.arange(
            df_ai["Day"].max()+1,
            df_ai["Day"].max()+prediction_days+1
        ).reshape(-1,1)

        predicted_sales = model.predict(future_days)

        future_dates = pd.date_range(
            start=df_ai["Date"].max()+pd.Timedelta(days=1),
            periods=prediction_days
        )

        prediction_df = pd.DataFrame({
            "Date":future_dates,
            "Predicted Sales":predicted_sales
        })

        st.dataframe(prediction_df)

        fig_pred = px.line(
            prediction_df,
            x="Date",
            y="Predicted Sales",
            markers=True,
            title="Future Sales Prediction"
        )

        st.plotly_chart(fig_pred,use_container_width=True)

    else:
        st.warning("Enter at least 3 records for AI prediction")

# -----------------------------
# Download Data
# -----------------------------

    csv = filtered_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Filtered Data",
        csv,
        "sales_data.csv",
        "text/csv"
    )