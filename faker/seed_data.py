import json
import logging.config
import os
import pathlib
import random

import psycopg2
from data_generator import generate_fake_patient_data
from database_structure_manager import check_data_existence, clear_database
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()


logger = logging.getLogger("hospital_logger")
config_file = pathlib.Path("logger_config.json")
with open(config_file) as f:
    config = json.load(f)
logging.config.dictConfig(config)


def add_patients(conn) -> None:
    cur = conn.cursor()
    new_patients_number = random.randint(100, 150)

    for _ in range(new_patients_number):
        new_patient = generate_fake_patient_data()
        cur.execute(
            "INSERT INTO patients(first_name, last_name, urgency, contact_phone, sickness) VALUES (%s, %s, %s, %s, %s)",
            (
                new_patient.first_name,
                new_patient.last_name,
                new_patient.urgency,
                new_patient.contact_phone,
                new_patient.sickness,
            ),
        )

    conn.commit()
    cur.close()
    logger.info(f"Added {new_patients_number} generated patients to db")


def add_beds(conn) -> None:
    cur = conn.cursor()
    new_beds_number = random.randint(15, 20)

    for _ in range(new_beds_number):
        cur.execute("INSERT INTO beds DEFAULT VALUES")

    conn.commit()
    cur.close()
    logger.info(f"Added {new_beds_number} generated beds to db")


def add_patients_to_queue(conn) -> None:
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT patient_id FROM patients")
    all_patient_ids = cur.fetchall()

    cur.execute("SELECT patient_id FROM bed_assignments")
    patients_with_cooldown_ids = cur.fetchall()

    if all_patient_ids and patients_with_cooldown_ids:
        new_patients_in_queue_number = random.randint(50, 100)

        cur.execute("SELECT MAX(queue_id) AS max_queue_position FROM patient_queue")
        max_queue_position = cur.fetchone()["max_queue_position"] or 0

        patient_ids_all = [p["patient_id"] for p in all_patient_ids]
        cooldown_ids = [p["patient_id"] for p in patients_with_cooldown_ids]

        available_ids = list(set(patient_ids_all) - set(cooldown_ids))

        queue = []
        for _ in range(new_patients_in_queue_number):
            if not available_ids:
                break
            selected = random.choice(available_ids)
            max_queue_position += 1
            queue.append((selected, max_queue_position))
            available_ids.remove(selected)
            cooldown_ids.append(selected)

            if len(cooldown_ids) > 60:
                cooldown_ids.pop(0)

        cur.executemany("INSERT INTO patient_queue(patient_id, queue_id) VALUES (%s, %s)", queue)

        logger.info(f"Added {len(queue)} patients to queue in db")

    conn.commit()
    cur.close()


def add_patient_assignment_to_bed(conn) -> None:
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT bed_id FROM beds")
    bed_ids = [row["bed_id"] for row in cur.fetchall()]

    cur.execute("SELECT patient_id FROM patients")
    patient_ids = [row["patient_id"] for row in cur.fetchall()]

    if bed_ids and patient_ids:
        assignments = []
        for bed_id in bed_ids:
            if not patient_ids:
                break
            patient_id = random.choice(patient_ids)
            days_of_stay = random.randint(1, 7)
            assignments.append((bed_id, patient_id, days_of_stay))
            patient_ids.remove(patient_id)

        cur.executemany("INSERT INTO bed_assignments(bed_id, patient_id, days_of_stay) VALUES (%s, %s, %s)", assignments)

        logger.info(f"Assigned {len(assignments)} patients to beds in db")

    conn.commit()
    cur.close()


if __name__ == "__main__":
    random.seed(43)

    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_NAME"),
        user=os.getenv("POSTGRES_USERNAME"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host="db",
        port="5432",
    )

    if not check_data_existence(conn):
        clear_database(conn)
        add_patients(conn)
        add_beds(conn)
        add_patient_assignment_to_bed(conn)
        add_patients_to_queue(conn)
    else:
        logger.info("Skipping data generation")

    conn.close()
