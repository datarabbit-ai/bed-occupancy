import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="Hospital bed management", page_icon="🏥")
st.title("Bed Assignments")


def get_bed_assignments() -> pd.DataFrame:
    try:
        response = requests.get("http://localhost:8000/get-bed-assignments")
    except Exception as e:
        st.error(f"Failed to connect to the server: {e}")
        return pd.DataFrame()
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("Failed to fetch data from the server.")
        return pd.DataFrame()


df = get_bed_assignments()
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("No bed assignments found.")

if st.button("➡️ Simulate Next Day"):
    try:
        response = requests.post("http://localhost:8000/simulate-next-day")
        if response.status_code != 200:
            st.error("Failed to simulate next day.")
    except Exception as e:
        st.error(f"Failed to connect to the server: {e}")
