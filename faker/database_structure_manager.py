import json
import logging.config
import pathlib

from psycopg2.extensions import connection as pg_connection

logger = logging.getLogger("hospital_logger")
config_file = pathlib.Path("logger_config.json")
with open(config_file) as f:
    config = json.load(f)
logging.config.dictConfig(config)


def clear_database(conn: pg_connection) -> None:
    cur = conn.cursor()

    cur.execute("TRUNCATE bed_assignments, patient_queue, patients, beds RESTART IDENTITY CASCADE;")
    conn.commit()
    cur.close()


def create_database_tables_structure(conn: pg_connection) -> None:
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id SERIAL PRIMARY KEY,
            first_name VARCHAR(30) NOT NULL,
            last_name VARCHAR(30) NOT NULL,
            urgency TEXT CHECK (urgency IN ('pilny', 'stabilny')) NOT NULL,
            contact_phone CHAR(9) NOT NULL,
            sickness TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS patient_queue (
            patient_id INTEGER NOT NULL,
            queue_id INTEGER NOT NULL UNIQUE,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );

        CREATE TABLE IF NOT EXISTS beds (
            bed_id SERIAL PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS bed_assignments (
            bed_id INTEGER UNIQUE NOT NULL,
            patient_id INTEGER UNIQUE NOT NULL,
            days_of_stay INTEGER CHECK (days_of_stay > 0) NOT NULL,
            FOREIGN KEY (bed_id) REFERENCES beds(bed_id),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );
    """)

    conn.commit()
    cur.close()


def check_data_existence(conn: pg_connection) -> bool:
    create_database_tables_structure(conn)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            (SELECT COUNT(*) FROM patients),
            (SELECT COUNT(*) FROM beds),
            (SELECT COUNT(*) FROM patient_queue),
            (SELECT COUNT(*) FROM bed_assignments)
    """)

    result = cur.fetchone()
    logger.setLevel(logging.DEBUG)
    logger.debug(
        f"Found: {result[0]} patients, {result[1]} beds, {result[2]} patients in queue and {result[3]} assignments of patients to beds in db"
    )

    cur.close()

    return all(count > 0 for count in result)
