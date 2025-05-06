import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Hospital bed management", page_icon="🏥")

st.title("Bed Assignments")

response = requests.get("http://localhost:8000/get-bed-assignments")
if response.status_code == 200:
    df = pd.DataFrame(response.json())

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No bed assignments found.")
else:
    st.error("Failed to fetch data from the server.")
    print(response.status_code)
