from typing import Dict, Optional

import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Hospital bed management", page_icon="🏥")
st.title("Bed Assignments")

if "day_for_simulation" not in st.session_state:
    st.session_state.day_for_simulation = requests.get("http://backend:8000/get-current-day").json()["day"]

if "refreshes_number" not in st.session_state:
    st.session_state.refreshes_number = 0

refreshes_number = None
if st.session_state.day_for_simulation < 20:
    refreshes_number = st_autorefresh(interval=10000, limit=None)

st.html(
    """
    <style>
        section[data-testid="stSidebar"]{
            width: 30% !important;
        }
        section[data-testid="stMain"]{
            width: 70% !important;
        }
    </style>
    """
)


def get_list_of_tables() -> Optional[Dict]:
    try:
        response = requests.get("http://backend:8000/get-tables")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch data from the server.")
            return None
    except Exception as e:
        st.error(f"Failed to connect to the server: {e}")
        return None


def update_day(delta: int) -> None:
    try:
        response = requests.get("http://backend:8000/update-day", params={"delta": delta})
        st.session_state.day_for_simulation = response.json()["day"]
    except Exception as e:
        st.session_state.error_message = f"Failed to connect to the server: {e}"


if refreshes_number is not None and refreshes_number > st.session_state.refreshes_number:
    update_day(delta=1)
    st.session_state.refreshes_number = refreshes_number

st.header(f"Day {st.session_state.day_for_simulation}")

tables = get_list_of_tables()
if tables:
    bed_df = pd.DataFrame(tables["BedAssignment"])
    queue_df = pd.DataFrame(tables["PatientQueue"])
    no_shows_df = pd.DataFrame(tables["NoShows"])

if not bed_df.empty:
    for col in ["patient_id", "patient_name", "sickness", "days_of_stay"]:
        bed_df[col] = bed_df[col].apply(lambda x: None if x == 0 or x == "Unoccupied" else x)
    st.dataframe(bed_df, use_container_width=True, hide_index=True)
else:
    st.info("No bed assignments found.")

st.sidebar.subheader("Patients in queue")
if not queue_df.empty:
    st.sidebar.dataframe(queue_df, use_container_width=True, hide_index=True)
else:
    st.sidebar.info("No patients found in the queue.")

st.sidebar.subheader("Patients absent on a given day")
if not no_shows_df.empty:
    st.sidebar.dataframe(no_shows_df, use_container_width=True, hide_index=True)
else:
    st.sidebar.info("No no-shows found.")

if st.session_state.day_for_simulation < 20:
    st.button("➡️ Simulate Next Day", on_click=lambda: update_day(delta=1))
if st.session_state.day_for_simulation > 1:
    st.button("⬅️ Simulate Previous Day", on_click=lambda: update_day(delta=-1))

if "error_message" in st.session_state and st.session_state.error_message:
    st.error(st.session_state.error_message)
