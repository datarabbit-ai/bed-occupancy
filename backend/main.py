import random
import sqlite3
import traceback
from typing import List

import db_operations as db
import fastapi
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel


# TODO: move it to the dedicated module in the future
class BedAssignment(BaseModel):
    bed_id: int
    patient_id: int
    patient_name: str
    sickness: str
    days_of_stay: int


app = FastAPI()
day_for_simulation = 1


@app.get("/update-day")
def update_day(delta: int = fastapi.Query(...)):
    global day_for_simulation
    if delta not in (-1, 1):
        return {"error": "Invalid delta value. Use -1 or 1."}
    if delta == 1 and day_for_simulation < 20 or delta == -1 and day_for_simulation > 1:
        day_for_simulation += delta
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

        def print_patients_to_be_released() -> None:
            df = read_query("""
                SELECT * \
                FROM patients \
                WHERE patient_id IN (SELECT patient_id \
                                     FROM bed_assignments \
                                     WHERE days_of_stay = 0); \
            """)
            print(f"pacjenci do zwolnienia: \n{df}")

        def delete_patients_to_be_released() -> None:
            cursor.execute("""
                DELETE
                FROM bed_assignments
                WHERE days_of_stay = 0;
            """)

        def assign_bed_to_patient(bed_id: int, patient_id: int, days_of_stay: int) -> None:
            cursor.execute(
                """
                INSERT INTO bed_assignments (bed_id, patient_id, days_of_stay)
                VALUES (?, ?, ?)
                """,
                (bed_id, patient_id, days_of_stay),
            )

            print(f"pacjent o id {patient_id} dostał łóżko o id {bed_id} na {days_of_stay} dni")

        def check_if_patient_has_bed(patient_id: int) -> bool:
            patients_with_beds_assigned = read_query("""
            SELECT patient_id FROM bed_assignments
            """)["patient_id"].tolist()

            return patient_id in patients_with_beds_assigned

        cursor.execute("BEGIN TRANSACTION;")

        for _ in range(day_for_simulation - 1):
            decrement_days_of_stay()
            print_patients_to_be_released()
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
                    print(f"pacjent o id {patient} nie przyszedł")
                elif check_if_patient_has_bed(patient):
                    print(f"pomijanie pacjenta o id {patient}, gdyż już jest na łóżku")
                else:
                    days: int = random.randint(1, 7)
                    assign_bed_to_patient(bed_ids[bed_iterator], patient, days)
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
        print(error_message)
        return {"error": "Server Error", "message": error_message}
