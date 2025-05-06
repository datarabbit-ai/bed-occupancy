import sqlite3

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Hospital bed management", page_icon="🏥")

st.title("Bed Assignments")

conn = sqlite3.connect("./db/hospital.db")

query = """
SELECT
    bed_assignments.bed_id,
    bed_assignments.patient_id,
    CONCAT(patients.first_name, ' ', patients.last_name) AS patient_name,
    patients.sickness,
    bed_assignments.days_of_stay
FROM bed_assignments
JOIN patients ON bed_assignments.patient_id = patients.patient_id;
"""
df = pd.read_sql_query(query, conn)
conn.close()

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("No bed assignments found.")
