import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Database Setup
def init_db():
    conn = sqlite3.connect('business_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            revenue REAL,
            client_id TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# 2. Page Configuration
st.set_page_config(page_title="Client Analytics Dashboard", layout="wide")
st.warning("Public Demo Mode: Do not upload sensitive company data. App resets automatically. Buy the source code to run locally and privately.")
st.title("📊 Client Analytics Dashboard")
st.markdown("Automated revenue tracking and visualization.")

# 3. Sidebar for Data Entry & CSV Upload
st.sidebar.header("Data Management")
option = st.sidebar.radio("Choose Mode", ["Manual Entry", "CSV Upload"])

if option == "Manual Entry":
    with st.sidebar.form("entry_form", clear_on_submit=True):
        date = st.date_input("Date")
        revenue = st.number_input("Daily Revenue (INR)", min_value=0.0)
        client_id = st.text_input("Client ID (e.g., Shop_01)")
        submit = st.form_submit_button("Save Record")

        if submit and client_id:
            c = conn.cursor()
            c.execute("INSERT INTO sales (date, revenue, client_id) VALUES (?, ?, ?)", 
                      (str(date), revenue, client_id))
            conn.commit()
            st.sidebar.success("Record saved successfully!")

else:
    st.sidebar.subheader("Upload CSV Report")
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        df_upload = pd.read_csv(uploaded_file)
        if {'date', 'revenue', 'client_id'}.issubset([col.lower().strip() for col in df_upload.columns]):
            # Normalize column names for insertion
            df_upload.columns = [col.lower().strip() for col in df_upload.columns]
            for _, row in df_upload.iterrows():
                c = conn.cursor()
                c.execute("INSERT INTO sales (date, revenue, client_id) VALUES (?, ?, ?)", 
                          (str(row['date']), float(row['revenue']), str(row['client_id'])))
            conn.commit()
            st.sidebar.success("CSV data imported successfully into database!")
        else:
            st.sidebar.error("CSV must contain columns: date, revenue, client_id")

# 4. Main Dashboard Area
st.subheader("Revenue Trends")

clients_df = pd.read_sql_query("SELECT DISTINCT client_id FROM sales", conn)

if not clients_df.empty:
    selected_client = st.selectbox("Select Client to View", clients_df['client_id'].tolist())
    
    query = f"SELECT date, revenue FROM sales WHERE client_id = '{selected_client}' ORDER BY date"
    df = pd.read_sql_query(query, conn)
    
    if not df.empty:
        col1, col2 = st.columns(2)
        col1.metric("Total Revenue", f"₹{df['revenue'].sum():,.2f}")
        col2.metric("Average Daily Revenue", f"₹{df['revenue'].mean():,.2f}")
        
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df['date'], df['revenue'], marker='o', color='#2e66ff', linewidth=2)
        ax.set_title(f"Revenue Timeline: {selected_client}", pad=15)
        ax.set_xlabel("Date")
        ax.set_ylabel("Revenue (INR)")
        plt.xticks(rotation=45)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        st.pyplot(fig)
        
        with st.expander("View Raw Database Records"):
            st.dataframe(df, use_container_width=True)
else:
    st.info("No data available yet. Add some records or upload a CSV from the sidebar.")
