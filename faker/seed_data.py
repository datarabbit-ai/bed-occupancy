import json
import logging.config
import pathlib
import random
import sqlite3

from data_generator import generate_fake_patient_data
from database_structure_manager import check_data_existence, clear_database

logger = logging.getLogger("hospital_logger")
config_file = pathlib.Path("logger_config.json")
with open(config_file) as f:
    config = json.load(f)
logging.config.dictConfig(config)


def add_patients(database_connection: sqlite3.Connection) -> None:
    cur = database_connection.cursor()
    new_patients_number = random.randint(100, 150)

    for _ in range(new_patients_number):
        new_patient = generate_fake_patient_data()
        cur.execute(
            "INSERT INTO patients(patient_id, first_name, last_name, urgency, contact_phone, sickness) VALUES (null, ?, ?, ?, ?, ?)",
            (
                new_patient.first_name,
                new_patient.last_name,
                new_patient.urgency,
                new_patient.contact_phone,
                new_patient.sickness,
            ),
        )

    database_connection.commit()
    logger.info(f"Added {new_patients_number} generated patients to db")


def add_beds(database_connection: sqlite3.Connection) -> None:
    cur = database_connection.cursor()
    new_beds_number = random.randint(15, 20)

    for _ in range(new_beds_number):
        cur.execute("INSERT INTO beds(bed_id) VALUES (null)")

    database_connection.commit()
    logger.info(f"Added {new_beds_number} generated beds to db")


def add_patients_to_queue(database_connection: sqlite3.Connection) -> None:
    cur = database_connection.cursor()

    cur.execute("SELECT patient_id FROM patients")
    all_patient_ids = cur.fetchall()

    cur.execute("SELECT patient_id FROM bed_assignments")
    patients_with_cooldown_ids = cur.fetchall()  # Patients added there will not be added to queue for some time to avoid frequent attempts to assign the patient to a bed once he is in hospital

    if all_patient_ids and patients_with_cooldown_ids:
        new_patients_in_queue_number = random.randint(50, 100)
        cur.execute("SELECT Max(queue_id) AS 'max_queue_position' FROM patient_queue")
        maximum_queue_position = cur.fetchone()["max_queue_position"]

        if not maximum_queue_position:
            maximum_queue_position = 0

        for patient_id in patients_with_cooldown_ids:
            all_patient_ids.remove(patient_id)

        for _ in range(new_patients_in_queue_number):
            patient_added_to_queue = random.choice(all_patient_ids)

            cur.execute(
                "INSERT INTO patient_queue(patient_id, queue_id) VALUES (?, ?)",
                (
                    patient_added_to_queue["patient_id"],
                    maximum_queue_position + 1,
                ),
            )
            maximum_queue_position += 1

            all_patient_ids.remove(patient_added_to_queue)
            patients_with_cooldown_ids.append(patient_added_to_queue)

            if len(patients_with_cooldown_ids) == 60:
                all_patient_ids.append(patients_with_cooldown_ids[0])
                patients_with_cooldown_ids.remove(patients_with_cooldown_ids[0])

        logger.info(f"Added {new_patients_in_queue_number} patients to queue in db")

    database_connection.commit()


def add_patient_assignment_to_bed(database_connection: sqlite3.Connection) -> None:
    cur = database_connection.cursor()

    cur.execute("SELECT bed_id FROM beds")
    all_bed_ids = cur.fetchall()

    cur.execute("SELECT patient_id FROM patients")
    all_patient_ids = cur.fetchall()

    if all_bed_ids and all_patient_ids:
        for row in all_bed_ids:
            bed_id = row["bed_id"]
            random_patient = random.choice(all_patient_ids)

            # The average length of stay is adjusted so that total hospital occupancy is about 20 days
            random_days_amount = random.randint(1, 7)

            cur.execute(
                "INSERT INTO bed_assignments(bed_id, patient_id, days_of_stay) VALUES (?, ?, ?)",
                (
                    bed_id,
                    random_patient["patient_id"],
                    random_days_amount,
                ),
            )

            all_patient_ids.remove(random_patient)

        logger.info(f"Assigned some patients to beds in db")

    database_connection.commit()


if __name__ == "__main__":
    random.seed(43)
    if not check_data_existence("../db/hospital.db"):
        clear_database("../db/hospital.db")

        conn = sqlite3.connect("../db/hospital.db")
        conn.row_factory = sqlite3.Row

        add_patients(conn)
        add_beds(conn)
        add_patient_assignment_to_bed(conn)
        add_patients_to_queue(conn)

        conn.close()
    else:
        logger.info("Skipping data generation")
