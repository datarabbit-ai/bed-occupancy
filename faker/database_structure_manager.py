import json
import logging.config
import pathlib
import sqlite3

logger = logging.getLogger("hospital_logger")
config_file = pathlib.Path("logger_config.json")
with open(config_file) as f:
    config = json.load(f)
logging.config.dictConfig(config)


def clear_database(path_to_database: str) -> None:
    conn = sqlite3.connect(path_to_database)

    cur = conn.cursor()

    cur.executescript(
        """
    DELETE FROM beds;
    DELETE FROM bed_assignments;
    DELETE FROM patients;
    DELETE FROM patient_queue;
    """
    )

    conn.commit()

    conn.close()


def create_database_tables_structure(database_connection: sqlite3.Connection) -> None:
    cur = database_connection.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY,
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
            bed_id INTEGER PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS bed_assignments (
            bed_id INTEGER UNIQUE NOT NULL,
            patient_id INTEGER UNIQUE NOT NULL,
            days_of_stay INTEGER UNSIGNED NOT NULL,
            FOREIGN KEY (bed_id) REFERENCES beds(bed_id),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        );
        """
    )

    database_connection.commit()


def check_data_existence(path_to_database: str) -> bool:
    conn = sqlite3.connect(path_to_database)
    create_database_tables_structure(conn)

    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM patients),
            (SELECT COUNT(*) FROM beds),
            (SELECT COUNT(*) FROM patient_queue),
            (SELECT COUNT(*) FROM bed_assignments)
        """
    )
    result = cur.fetchone()
    logger.debug(
        f"Found: {result[0]} patients, {result[1]} beds, {result[2]} patients in queue and {result[3]} assignments of patients to beds in db"
    )
    conn.commit()

    conn.close()

    if any(count == 0 for count in result):
        return False
    return True
