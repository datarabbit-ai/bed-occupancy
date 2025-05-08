import pandas as pd
import requests
import streamlit as st

if "day_for_simulation" not in st.session_state:
    st.session_state.day_for_simulation = 1
st.set_page_config(page_title="Hospital bed management", page_icon="🏥")
st.title("Bed Assignments")
st.header(f"Day {st.session_state.day_for_simulation}")


def get_bed_assignments() -> pd.DataFrame:
    try:
        response = requests.get("http://backend:8000/get-bed-assignments")
    except Exception as e:
        st.error(f"Failed to connect to the server: {e}")
        return pd.DataFrame()
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error("Failed to fetch data from the server.")
        return pd.DataFrame()


def simulate_next_day():
    try:
        response = requests.get("http://backend:8000/update-day", params={"delta": 1})
        st.session_state.day_for_simulation = response.json()["day"]
        st.session_state.error_message = None

    except Exception as e:
        st.session_state.error_message = f"Failed to connect to the server: {e}"


def simulate_previous_day():
    try:
        response = requests.get("http://backend:8000/update-day", params={"delta": -1})
        st.session_state.day_for_simulation = response.json()["day"]
        st.session_state.error_message = None
    except Exception as e:
        st.session_state.error_message = f"Failed to connect to the server: {e}"


df = get_bed_assignments()
if not df.empty:
    for col in ["patient_id", "patient_name", "sickness", "days_of_stay"]:
        df[col] = df[col].apply(lambda x: None if x == 0 or x == "Unoccupied" else x)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No bed assignments found.")

if st.session_state.day_for_simulation < 20:
    st.button("➡️ Simulate Next Day", on_click=simulate_next_day)

if st.session_state.day_for_simulation > 1:
    st.button("⬅️ Simulate Previous Day", on_click=simulate_previous_day)

if "error_message" in st.session_state and st.session_state.error_message:
    st.error(st.session_state.error_message)
