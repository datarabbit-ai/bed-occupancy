import logging
import random
import sys
import traceback
from typing import List

import db_operations as db
import fastapi
import pandas as pd
from fastapi import FastAPI
from modules import BedAssignment, ListOfTables, NoShows, PatientQueue

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,
)


app = FastAPI()
day_for_simulation = 1
last_change = 1  # 1 - next day, -1 - previous day


@app.get("/update-day")
def update_day(delta: int = fastapi.Query(...)):
    global day_for_simulation
    global last_change
    if delta not in (-1, 1):
        return {"error": "Invalid delta value. Use -1 or 1."}
    if delta == 1 and day_for_simulation < 20 or delta == -1 and day_for_simulation > 1:
        day_for_simulation += delta
        last_change = delta
    return {"day": day_for_simulation}


@app.get("/get-tables", response_model=ListOfTables)
def get_tables() -> ListOfTables:
    try:
        random.seed(43)
        conn = db.get_connection()
        cursor = conn.cursor()

        def read_query(query: str) -> pd.DataFrame:
            return pd.read_sql_query(query, conn)

        def decrement_days_of_stay() -> None:
            cursor.execute("""
                UPDATE bed_assignments
                SET days_of_stay = days_of_stay - 1;
            """)

        def print_patients_to_be_released(log: bool) -> None:
            df = read_query("""
                SELECT * \
                FROM patients \
                WHERE patient_id IN (SELECT patient_id \
                                     FROM bed_assignments \
                                     WHERE days_of_stay = 0); \
            """)
            if log:
                logging.info(f"Patients to be released from hospital: \n{df}")

        def delete_patients_to_be_released() -> None:
            cursor.execute("""
                DELETE
                FROM bed_assignments
                WHERE days_of_stay = 0;
            """)

        def assign_bed_to_patient(bed_id: int, patient_id: int, days_of_stay: int, log: bool) -> None:
            cursor.execute(
                """
                INSERT INTO bed_assignments (bed_id, patient_id, days_of_stay)
                VALUES (?, ?, ?)
                """,
                (bed_id, patient_id, days_of_stay),
            )
            if log:
                logging.info(f"Patient with id {patient_id} got a bed with id {bed_id} for {days_of_stay} days")

        def check_if_patient_has_bed(patient_id: int) -> bool:
            patients_with_beds_assigned = read_query("""
            SELECT patient_id FROM bed_assignments
            """)["patient_id"].tolist()

            return patient_id in patients_with_beds_assigned

        def delete_patient_by_id_from_queue(patient_id: int) -> None:
            cursor.execute(
                """
                SELECT queue_id FROM patient_queue
                WHERE patient_id = ?
                ORDER BY queue_id
                LIMIT 1
                """,
                (patient_id,),
            )

            patient_place_in_queue = cursor.fetchone()

            cursor.execute(
                """
                DELETE FROM patient_queue
                WHERE queue_id = ?
                """,
                (patient_place_in_queue["queue_id"],),
            )

            cursor.execute(
                """
                UPDATE patient_queue
                SET queue_id = queue_id - 1
                WHERE queue_id > ?
                """,
                (patient_place_in_queue["queue_id"],),
            )

        cursor.execute("BEGIN TRANSACTION;")

        if last_change == 1:
            logging.info(f"Current simulation day: {day_for_simulation}")
        else:
            logging.info(f"Rollback of simulation to day {day_for_simulation}")

        for iteration in range(day_for_simulation - 1):
            should_log = iteration == day_for_simulation - 2 and last_change == 1

            decrement_days_of_stay()
            print_patients_to_be_released(log=should_log)
            delete_patients_to_be_released()

            bed_ids: List[int] = read_query("""
                SELECT bed_id \
                FROM beds \
                WHERE bed_id NOT IN (SELECT bed_id FROM bed_assignments); \
                """)["bed_id"].tolist()

            queue = read_query("""
                SELECT patient_id, queue_id \
                FROM patient_queue \
                """)

            bed_iterator = 0
            for patient in queue["patient_id"]:
                if bed_iterator >= len(bed_ids):
                    break

                will_come: bool = random.choice([True, True, True, True, False])

                if not will_come:
                    delete_patient_by_id_from_queue(patient)
                    if should_log:
                        logging.info(f"Patient with id {patient} did not come. He was removed from the queue")
                elif check_if_patient_has_bed(patient):
                    if should_log:
                        logging.info(f"Skipping a patient with id {patient}, because he/she is already on the bed ")
                else:
                    days: int = random.randint(1, 7)
                    assign_bed_to_patient(bed_ids[bed_iterator], patient, days, log=should_log)
                    delete_patient_by_id_from_queue(patient)
                    bed_iterator += 1

        bed_assignments_df: BedAssignment = read_query("""
            SELECT beds.bed_id,
                   bed_assignments.patient_id,
                   patients.first_name || ' ' || patients.last_name AS patient_name,
                   patients.sickness,
                   bed_assignments.days_of_stay
            FROM beds
            LEFT JOIN bed_assignments ON beds.bed_id = bed_assignments.bed_id
            LEFT JOIN patients ON bed_assignments.patient_id = patients.patient_id
            ORDER BY beds.bed_id;
        """)

        queue_df: PatientQueue = read_query("""
            SELECT patient_queue.queue_id AS place_in_queue,
                   patient_queue.patient_id,
                   patients.first_name || ' ' || patients.last_name AS patient_name
            FROM patients
            INNER JOIN patient_queue ON patients.patient_id = patient_queue.patient_id
            ORDER BY patient_queue.queue_id;
        """)

        bed_assignments_df = bed_assignments_df.fillna(
            {"patient_id": 0, "patient_name": "Unoccupied", "sickness": "Unoccupied", "days_of_stay": 0}
        )

        cursor.execute("ROLLBACK;")
        db.close_connection(conn)

        tables = ListOfTables(
            BedAssignment=bed_assignments_df.to_dict(orient="records"),
            PatientQueue=queue_df.to_dict(orient="records"),
            NoShows=[],
        )
        return tables

    except Exception as e:
        error_message = f"Error occurred: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_message)
        return {"error": "Server Error", "message": error_message}
