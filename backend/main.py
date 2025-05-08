import logging
import random
import sys
import traceback
from typing import List

import db_operations as db
import fastapi
import pandas as pd
from fastapi import FastAPI
from modules import BedAssignment

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


@app.get("/get-bed-assignments", response_model=List[BedAssignment])
def get_bed_assignments() -> List[BedAssignment]:
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
                logging.info(f"pacjenci do zwolnienia: \n{df}")

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
                logging.info(f"pacjent o id {patient_id} dostał łóżko o id {bed_id} na {days_of_stay} dni")

        def check_if_patient_has_bed(patient_id: int) -> bool:
            patients_with_beds_assigned = read_query("""
            SELECT patient_id FROM bed_assignments
            """)["patient_id"].tolist()

            return patient_id in patients_with_beds_assigned

        def delete_patient_by_id_from_queue(patient_id: int) -> None:
            cursor.execute(
                """
                DELETE FROM patient_queue
                WHERE queue_id = (
                    SELECT queue_id FROM patient_queue
                    WHERE patient_id = ?
                    ORDER BY queue_id
                    LIMIT 1
                )
            """,
                (patient_id,),
            )

        cursor.execute("BEGIN TRANSACTION;")

        if day_for_simulation == 1 and last_change == 1:
            logging.info(f"Aktualny dzień symulacji: {day_for_simulation}")
        elif last_change == -1:
            logging.info(f"Cofnięcie symulacji do dnia {day_for_simulation}")

        for iteration in range(day_for_simulation - 1):
            should_log = iteration == day_for_simulation - 2 and last_change == 1
            if should_log:
                logging.info(f"Aktualny dzień symulacji: {day_for_simulation}")
            elif last_change == -1:
                logging.info(f"Cofnięcie symulacji do dnia {day_for_simulation}")

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
                        logging.info(f"pacjent o id {patient} nie przyszedł")
                elif check_if_patient_has_bed(patient):
                    if should_log:
                        logging.info(f"pomijanie pacjenta o id {patient}, gdyż już jest na łóżku")
                else:
                    days: int = random.randint(1, 7)
                    assign_bed_to_patient(bed_ids[bed_iterator], patient, days, log=should_log)
                    delete_patient_by_id_from_queue(patient)
                    bed_iterator += 1

        df = read_query("""
            SELECT bed_assignments.bed_id,
                   bed_assignments.patient_id,
                   patients.first_name || ' ' || patients.last_name AS patient_name,
                   patients.sickness,
                   bed_assignments.days_of_stay
            FROM bed_assignments
            JOIN patients ON bed_assignments.patient_id = patients.patient_id
            ORDER BY bed_assignments.bed_id;
        """)

        cursor.execute("ROLLBACK;")
        db.close_connection(conn)
        return df.to_dict(orient="records")

    except Exception as e:
        error_message = f"Error occurred: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_message)
        return {"error": "Server Error", "message": error_message}
