import json
import logging.config
import random
import traceback
from pathlib import Path
from typing import List

import pandas as pd
from db_operations import get_engine
from fastapi import FastAPI, Query
from models import ListOfTables, NoShow
from sqlalchemy import text
from sqlalchemy.engine import Connection

logger = logging.getLogger("hospital_logger")
config_file = Path("logger_config.json")
with open(config_file) as f:
    config = json.load(f)
logging.config.dictConfig(config)

app = FastAPI()
day_for_simulation = 1
last_change = 1


@app.get("/update-day")
def update_day(delta: int = Query(...)):
    global day_for_simulation, last_change
    if delta not in (-1, 1):
        return {"error": "Invalid delta value. Use -1 or 1."}
    if delta == 1 and day_for_simulation < 20 or delta == -1 and day_for_simulation > 1:
        day_for_simulation += delta
        last_change = delta
    return {"day": day_for_simulation}


@app.get("/get-tables", response_model=ListOfTables)
def get_tables():
    def read_query(query: str) -> pd.DataFrame:
        return pd.read_sql(text(query), conn)

    def decrement_days_of_stay():
        conn.execute(text("UPDATE bed_assignments SET days_of_stay = days_of_stay - 1"))

    def print_patients_to_be_released(log: bool):
        df = read_query("""
            SELECT * FROM patients
            WHERE patient_id IN (
                SELECT patient_id FROM bed_assignments WHERE days_of_stay = 0
            );
        """)
        if log:
            logger.info(f"Patients to be released from hospital: \n{df}")

    def delete_patients_to_be_released():
        conn.execute(text("DELETE FROM bed_assignments WHERE days_of_stay = 0"))

    def assign_bed_to_patient(bed_id: int, patient_id: int, days: int, log: bool):
        conn.execute(
            text("""
            INSERT INTO bed_assignments (bed_id, patient_id, days_of_stay)
            VALUES (:bed_id, :patient_id, :days)
        """),
            {"bed_id": bed_id, "patient_id": patient_id, "days": days},
        )
        if log:
            logger.info(f"Assigned bed {bed_id} to patient {patient_id} for {days} days")

    def check_if_patient_has_bed(patient_id: int) -> bool:
        result = read_query("SELECT patient_id FROM bed_assignments")
        return patient_id in result["patient_id"].tolist()

    def delete_patient_by_id_from_queue(patient_id: int):
        result = conn.execute(
            text("""
            SELECT queue_id FROM patient_queue
            WHERE patient_id = :pid ORDER BY queue_id LIMIT 1
        """),
            {"pid": patient_id},
        ).fetchone()

        if result:
            queue_id = result.queue_id
            conn.execute(text("DELETE FROM patient_queue WHERE queue_id = :qid"), {"qid": queue_id})
            conn.execute(
                text("""
                UPDATE patient_queue
                SET queue_id = queue_id - 1
                WHERE queue_id > :qid
            """),
                {"qid": queue_id},
            )

    def get_patient_name_by_id(patient_id: int) -> str:
        result = conn.execute(
            text("""
            SELECT first_name || ' ' || last_name AS name FROM patients
            WHERE patient_id = :pid
        """),
            {"pid": patient_id},
        ).fetchone()
        return result.name if result else "Unknown"

    try:
        random.seed(43)
        engine = get_engine()
        conn: Connection = engine.connect()
        trans = conn.begin()

        if last_change == 1:
            logger.info(f"Current simulation day: {day_for_simulation}")
        else:
            logger.info(f"Rollback of simulation to day {day_for_simulation}")

        no_shows_list: List[NoShow] = []

        for iteration in range(day_for_simulation - 1):
            should_log = iteration == day_for_simulation - 2 and last_change == 1

            decrement_days_of_stay()
            print_patients_to_be_released(log=should_log)
            delete_patients_to_be_released()

            bed_ids = read_query("""
                SELECT bed_id FROM beds
                WHERE bed_id NOT IN (SELECT bed_id FROM bed_assignments)
            """)["bed_id"].tolist()

            queue = read_query("SELECT patient_id FROM patient_queue ORDER BY queue_id")
            bed_iterator = 0

            for patient_id in queue["patient_id"]:
                if bed_iterator >= len(bed_ids):
                    break
                will_come = random.choice([True] * 4 + [False])
                if not will_come:
                    delete_patient_by_id_from_queue(patient_id)
                    no_show = NoShow(patient_id=patient_id, patient_name=get_patient_name_by_id(patient_id))
                    if should_log:
                        no_shows_list.append(no_show)
                        logger.info(f"No-show: {no_show.patient_name}")
                elif check_if_patient_has_bed(patient_id):
                    if should_log:
                        logger.info(f"Patient {patient_id} already has a bed")
                else:
                    days = random.randint(1, 7)
                    assign_bed_to_patient(bed_ids[bed_iterator], patient_id, days, should_log)
                    delete_patient_by_id_from_queue(patient_id)
                    bed_iterator += 1

        bed_df = read_query("""
            SELECT beds.bed_id,
                   COALESCE(bed_assignments.patient_id, 0) AS patient_id,
                   COALESCE(patients.first_name || ' ' || patients.last_name, 'Unoccupied') AS patient_name,
                   COALESCE(patients.sickness, 'Unoccupied') AS sickness,
                   COALESCE(bed_assignments.days_of_stay, 0) AS days_of_stay
            FROM beds
            LEFT JOIN bed_assignments ON beds.bed_id = bed_assignments.bed_id
            LEFT JOIN patients ON bed_assignments.patient_id = patients.patient_id
            ORDER BY beds.bed_id
        """)

        queue_df = read_query("""
            SELECT patient_queue.queue_id AS place_in_queue,
                   patient_queue.patient_id,
                   patients.first_name || ' ' || patients.last_name AS patient_name
            FROM patient_queue
            JOIN patients ON patient_queue.patient_id = patients.patient_id
            ORDER BY patient_queue.queue_id
        """)

        trans.rollback()
        conn.close()

        tables = ListOfTables(
            BedAssignment=bed_df.to_dict(orient="records"),
            PatientQueue=queue_df.to_dict(orient="records"),
            NoShows=[n.model_dump() for n in no_shows_list],
        )
        return tables

    except Exception as e:
        error_message = f"Error occurred: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_message)
        return {"error": "Server Error", "message": error_message}
