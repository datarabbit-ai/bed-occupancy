import traceback
from typing import List

import db_operations as db
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel


class BedAssignment(BaseModel):
    bed_id: int
    patient_id: int
    patient_name: str
    sickness: str
    days_of_stay: int


app = FastAPI()


@app.get("/get-bed-assignments", response_model=List[BedAssignment])
def get_bed_assignments() -> List[BedAssignment]:
    try:
        conn = db.get_connection()
        query = """
        SELECT
            bed_assignments.bed_id,
            bed_assignments.patient_id,
            patients.first_name || ' ' || patients.last_name AS patient_name,
            patients.sickness,
            bed_assignments.days_of_stay
        FROM bed_assignments
        JOIN patients ON bed_assignments.patient_id = patients.patient_id;
        """
        df = pd.read_sql_query(query, conn)
        db.close_connection(conn)
        return df.to_dict(orient="records")
    except Exception as e:
        error_message = f"Error occurred: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {"error": "Server Error", "message": error_message}


@app.get("/simulate_next_day")
def simulate_next_day():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        cursor.execute("BEGIN TRANSACTION;")

        cursor.execute("""
        UPDATE bed_assignments SET days_of_stay = days_of_stay - 1;
        """)

        # query = """
        # SELECT * FROM patients WHERE patient_id IN (
        #     SELECT patient_id FROM bed_assignments WHERE days_of_stay = 0
        # );
        # """
        # df = pd.read_sql_query(query, conn)
        # print(f'pacjenci do wypisania: \n{df}')

        cursor.execute("""
        DELETE FROM bed_assignments WHERE days_of_stay = 0;
        """)

        query = """
        SELECT bed_id FROM beds WHERE bed_id NOT IN (SELECT bed_id FROM bed_assignments);
        """
        bed_ids: List[int] = pd.read_sql_query(query, conn)["bed_id"].tolist()

        db.close_connection(conn)
        # return df.to_dict(orient="records") commenting this only to pass ruff
    except Exception as e:
        error_message = f"Error occurred: {str(e)}\n{traceback.format_exc()}"
        print(error_message)
        return {"error": "Server Error", "message": error_message}
