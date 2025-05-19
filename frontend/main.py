import random
from typing import Dict, Optional

import pandas as pd
import requests
import streamlit as st
from agent import *

if "day_for_simulation" not in st.session_state:
    st.session_state.day_for_simulation = requests.get("http://backend:8000/get-current-day").json()["day"]
st.set_page_config(page_title="Hospital bed management", page_icon="🏥")
st.title("Bed Assignments")
st.header(f"Day {st.session_state.day_for_simulation}")

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


def handle_patient_rescheduling(name: str, surname: str, pesel: str, sickness: str, old_day: int, new_day: int) -> bool:
    """
    Handles the process of rescheduling a patient's appointment by initiating a voice conversation
    with the patient and analyzing their consent.

    :param name: The first name of the patient.
    :param surname: The last name of the patient.
    :param pesel: The PESEL number of the patient.
    :param sickness: The sickness or condition of the patient.
    :param old_day: The current day of the patient's visit.
    :param new_day: The suggested day for the new appointment.
    :return: A boolean indicating whether the patient consented to the rescheduling.
    """
    # conversation = prepare_conversation(
    #     patient_name=name,
    #     patient_surname=surname,
    #     pesel=pesel,
    #     patient_sickness=sickness,
    #     current_visit_day=old_day,
    #     suggested_appointment_day=new_day,
    # )
    # conversation_id = establish_voice_conversation(conversation)
    # return check_patient_consent_to_reschedule(conversation_id)
    will_come = random.choice([True, True, False, False, False])
    return will_come


def agent_call(queue_df: pd.DataFrame) -> None:
    queue_id = 0

    while queue_id < len(queue_df):
        patient_id = queue_df["patient_id"][queue_id]
        name, surname = queue_df["patient_name"][queue_id].split()
        pesel = queue_df["PESEL"][queue_id][-3:]

        response = requests.get("http://backend:8000/get-patient-data", params={"patient_id": patient_id}).json()
        consent = handle_patient_rescheduling(
            name=name,
            surname=surname,
            pesel=pesel,
            sickness=response["sickness"],
            old_day=response["old_day"],
            new_day=response["new_day"],
        )

        if consent:
            st.session_state.patient_id = patient_id
            st.session_state.consent = True
            requests.get("http://backend:8000/add-patient-to-approvers", params={"patient_id": patient_id})
            st.success(f"{name} {surname} agreed to reschedule.")
            return
        else:
            queue_id += 1

    st.warning("No patient agreed to reschedule.")


def get_list_of_tables() -> Optional[Dict]:
    try:
        response = requests.get("http://backend:8000/get-tables")
    except Exception as e:
        st.error(f"Failed to connect to the server: {e}")
        return None
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch data from the server.")
        return None


def simulate_next_day() -> None:
    try:
        response = requests.get("http://backend:8000/update-day", params={"delta": 1})
        st.session_state.day_for_simulation = response.json()["day"]
        st.session_state.error_message = None

    except Exception as e:
        st.session_state.error_message = f"Failed to connect to the server: {e}"


def simulate_previous_day() -> None:
    try:
        response = requests.get("http://backend:8000/update-day", params={"delta": -1})
        st.session_state.day_for_simulation = response.json()["day"]
        st.session_state.error_message = None
    except Exception as e:
        st.session_state.error_message = f"Failed to connect to the server: {e}"


tables = get_list_of_tables()
bed_df = pd.DataFrame(tables["BedAssignment"])
queue_df = pd.DataFrame(tables["PatientQueue"])
no_shows_df = pd.DataFrame(tables["NoShows"])

if len(bed_df[bed_df["patient_id"] == 0]) > 0 and len(queue_df) > 0:
    st.session_state.consent = False
    st.sidebar.button("Call next patient in queue 📞", on_click=lambda: agent_call(queue_df))

if not bed_df.empty:
    for col in ["patient_id", "patient_name", "sickness", "days_of_stay", "PESEL"]:
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
    st.button("➡️ Simulate Next Day", on_click=simulate_next_day)

if st.session_state.day_for_simulation > 1:
    st.button("⬅️ Simulate Previous Day", on_click=simulate_previous_day)

if "error_message" in st.session_state and st.session_state.error_message:
    st.error(st.session_state.error_message)
