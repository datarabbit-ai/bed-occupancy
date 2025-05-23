import random
from typing import Dict, Optional

import pandas as pd
import requests
import streamlit as st
from agent import *
from agent import check_patient_consent_to_reschedule
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Hospital bed management", page_icon="🏥")
main_tab, statistics_tab = st.tabs(["Current state", "Data analysis"])
main_tab.title("Bed Assignments")

if "day_for_simulation" not in st.session_state:
    st.session_state.day_for_simulation = requests.get("http://backend:8000/get-current-day").json()["day"]

if "refreshes_number" not in st.session_state:
    st.session_state.refreshes_number = 0

if "auto_day_change" not in st.session_state:
    st.session_state.auto_day_change = False

if "button_pressed" not in st.session_state:
    st.session_state.button_pressed = False

st.html(
    """
    <style>
        section[data-testid="stSidebar"]{
            width: 30% !important;
        }
        section[data-testid="stMain"]{
            width: 70% !important;
        }

        .tooltip {
            position: relative;
            display: inline-block;
        }
        .tooltip .tooltiptext {
            visibility: hidden;
            width: max-content;
            background-color: black;
            color: #fff;
            text-align: center;
            padding: 8px;
            border-radius: 8px;
            position: absolute;
            bottom: 110%;
            left: 50%;
            transform: translateX(-50%);
            z-index: 100;
        }
        .tooltip:hover .tooltiptext {
            visibility: visible;
        }
        .tooltiptext table {
            font-size: 0.8em;
            margin: 0;
            padding: 0;
        }
        .tooltiptext table td, .tooltiptext table th {
            font-size: 1em;
            margin: 0;
            padding: 1px 2px;
            font-weight: 200;
        }


        .main .block-container {
            max-width: 1200px;
        }
        .box {
            border: 1px solid #d0d3d9;
            border-radius: 5px;
            height: 100px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            margin-bottom: 15px;
            cursor: pointer;
        }

        .box-empty {
            background-color: oklch(80% 0.23 140);

            &:hover {
                background-color: oklch(90% 0.23 140);
            }

        }
        .box-occupied {
            background-color: oklch(80% 0.25 25);

            &:hover {
                background-color: oklch(90% 0.25 25);
            }
        }
    </style>
    """
)


def create_box_grid(df: pd.DataFrame, boxes_per_row=4) -> None:
    """
    Creates a scrollable grid of boxes with tooltips on hover

    Parameters:
    - df: pandas DataFrame, each row represents a box
    - boxes_per_row: int, number of boxes to display per row
    """
    # Calculate number of boxes from DataFrame
    num_boxes = len(df)

    # Calculate number of rows needed
    num_rows = (num_boxes + boxes_per_row - 1) // boxes_per_row

    # Create the grid
    for row in range(num_rows):
        cols = main_tab.columns(boxes_per_row)

        for col in range(boxes_per_row):
            box_index = row * boxes_per_row + col

            if box_index < num_boxes:
                with cols[col]:
                    # Get data for this box
                    data_row = df.iloc[box_index]

                    box_title = f"Bed {box_index + 1}"

                    # Format tooltip information with row data
                    filtered_items = {k: v for k, v in data_row.items() if k != "bed_id"}
                    table_headers, table_data = list(zip(*filtered_items.items())) if filtered_items else ([], [])

                    tooltip_info = "<table style='border-collapse: collapse;'>"
                    tooltip_info += "<tr>"
                    for header in table_headers:
                        tooltip_info += f"<th style='border: 1px solid #ccc; padding: 4px; font-weight: bold;'>{header}</th>"
                    tooltip_info += "</tr><tr>"
                    for definition in table_data:
                        tooltip_info += f"<td style='border: 1px solid #ccc; padding: 4px;'>{definition}</td>"
                    tooltip_info += "</tr></table>"

                    # Create a box with HTML
                    if data_row["patient_id"] == 0 or pd.isna(data_row["patient_id"]):
                        st.markdown(
                            f"""<div class="tooltip box box-empty">{box_title}<span class="tooltiptext">This bed is empty!</span></div>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""<div class="tooltip box box-occupied">{box_title}<span class="tooltiptext">{tooltip_info}</span></div>""",
                            unsafe_allow_html=True,
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

    conversation_ids = (
        ["conv_01jvmfw4nmf7nrp2vs3em3q9hn"] * 12
        + ["conv_01jvmchxvdfeystykhfdcb0tr1"] * 7
        + ["conv_01jvmcvacefw68528gty0j0dj6"] * 1
    )
    selected_conversation_id = random.choice(conversation_ids)
    result = check_patient_consent_to_reschedule(selected_conversation_id)
    return result


def agent_call(queue_df: pd.DataFrame) -> None:
    queue_id = 0

    while queue_id < len(queue_df):
        patient_id = queue_df["patient_id"][queue_id]
        name, surname = queue_df["patient_name"][queue_id].split()
        pesel = queue_df["pesel"][queue_id][-3:]

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
            requests.get("http://backend:8000/increase-calls-number")
            main_tab.success(f"{name} {surname} agreed to reschedule.")
            return
        elif consent is None:
            st.info("Patient consent is unknown, calling one more time.")
            continue
        else:
            queue_id += 1
            requests.get("http://backend:8000/increase-calls-number")

    st.session_state.button_pressed = True

    main_tab.warning("No patient agreed to reschedule.")


def get_list_of_tables_and_statistics() -> Optional[Dict]:
    try:
        response = requests.get("http://backend:8000/get-tables-and-statistics")
        if response.status_code == 200:
            return response.json()
        else:
            main_tab.error("Failed to fetch data from the server.")
            return None
    except Exception as e:
        main_tab.error(f"Failed to connect to the server: {e}")
        return None


def update_day(delta: int) -> None:
    try:
        response = requests.get("http://backend:8000/update-day", params={"delta": delta})
        st.session_state.day_for_simulation = response.json()["day"]
    except Exception as e:
        st.session_state.error_message = f"Failed to connect to the server: {e}"


def toggle_auto_day_change() -> None:
    st.session_state.auto_day_change = not st.session_state.auto_day_change


if st.session_state.auto_day_change and not st.session_state.button_pressed:
    update_day(delta=1)
elif st.session_state.button_pressed:
    st.session_state.button_pressed = False

bed_df, queue_df, no_shows_df = None, None, None
tables = get_list_of_tables_and_statistics()
if tables:
    bed_df = pd.DataFrame(tables["BedAssignment"])
    queue_df = pd.DataFrame(tables["PatientQueue"])
    no_shows_df = pd.DataFrame(tables["NoShows"])

main_tab.header(f"Day {st.session_state.day_for_simulation}")

if len(bed_df[bed_df["patient_id"] == 0]) > 0 and len(queue_df) > 0:
    st.session_state.consent = False
    st.sidebar.button("Call next patient in queue 📞", on_click=lambda: agent_call(queue_df))
elif st.session_state.day_for_simulation < 20 and st.session_state.auto_day_change:
    st_autorefresh(interval=10000, limit=None)

if not bed_df.empty:
    create_box_grid(bed_df)
else:
    main_tab.info("No bed assignments found.")

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

st.sidebar.toggle(
    label="Activate automatic day change", value=st.session_state.auto_day_change, on_change=toggle_auto_day_change
)


statistics_tab.subheader("Bed occupancy statistics")

analytic_data = tables["Statistics"]

col1, col2, col3 = statistics_tab.columns(3)
col1.metric(label="Beds occupancy", value=analytic_data["Occupancy"], delta=analytic_data["OccupancyDifference"], border=True)
col2.metric(
    label="Average beds occupancy",
    value=analytic_data["AverageOccupancy"],
    delta=analytic_data["AverageOccupancyDifference"],
    border=True,
)
col3.metric(
    label="Average length of stay",
    value=analytic_data["AverageStayLength"],
    delta=analytic_data["AverageStayLengthDifference"],
    border=True,
)

occupancy_df = pd.DataFrame(analytic_data["OccupancyInTime"])
occupancy_df_copy = occupancy_df.copy()
occupancy_df_copy["Date"] = pd.Categorical(
    occupancy_df_copy["Date"].astype(str), categories=[str(x) for x in sorted(occupancy_df_copy["Date"])], ordered=True
)
statistics_tab.line_chart(occupancy_df_copy, x="Date", y_label="Occupancy [%]", use_container_width=True)

statistics_tab.subheader("No-show statistics")

col1, col2 = statistics_tab.columns(2)
col1.metric(
    label="No-shows percentage",
    value=analytic_data["NoShowsPercentage"],
    delta=analytic_data["NoShowsPercentageDifference"],
    border=True,
)
col2.metric(
    label="Average no-shows percentage",
    value=analytic_data["AverageNoShowsPercentage"],
    delta=analytic_data["AverageNoShowsPercentageDifference"],
    border=True,
)

no_shows_df = pd.DataFrame(analytic_data["NoShowsInTime"])
no_shows_df_copy = no_shows_df.copy()
no_shows_df_copy["Date"] = pd.Categorical(
    no_shows_df_copy["Date"].astype(str), categories=[str(x) for x in sorted(no_shows_df_copy["Date"])], ordered=True
)
statistics_tab.line_chart(no_shows_df_copy, x="Date", y_label="No-shows percentage [%]", use_container_width=True)


statistics_tab.subheader("Phone calls statistics")

col1, col2 = statistics_tab.columns(2)
col1.metric(
    label="Percentage of calls resulting in rescheduling",
    value=analytic_data["ConsentsPercentage"],
    delta=analytic_data["ConsentsPercentageDifference"],
    border=True,
)
col2.metric(
    label="Average percentage of calls resulting in rescheduling",
    value=analytic_data["AverageConstentsPercentage"],
    delta=analytic_data["AverageConstentsPercentageDifference"],
    border=True,
)

calls_df = pd.DataFrame(analytic_data["CallsInTime"])
calls_df_copy = calls_df.copy()
calls_df_copy["Date"] = pd.Categorical(
    calls_df_copy["Date"].astype(str), categories=[str(x) for x in sorted(calls_df_copy["Date"])], ordered=True
)
statistics_tab.line_chart(calls_df_copy, x="Date", y_label="Number of phone calls completed", use_container_width=True)


if st.session_state.day_for_simulation < 20 and not st.session_state.auto_day_change:
    st.button("➡️ Simulate Next Day", on_click=lambda: update_day(delta=1))
if st.session_state.day_for_simulation > 1 and not st.session_state.auto_day_change:
    st.button("⬅️ Simulate Previous Day", on_click=lambda: update_day(delta=-1))

if "error_message" in st.session_state and st.session_state.error_message:
    st.error(st.session_state.error_message)
