import random
import sqlite3

from data_generator import generate_fake_patient_data
from database_structure_manager import (
    check_data_existence,
    clear_database,
)


def add_patients(database_connection: sqlite3.Connection):
    cur = database_connection.cursor()
    new_patients_number = random.randint(50, 100)

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


def add_beds(database_connection: sqlite3.Connection):
    cur = database_connection.cursor()
    new_beds_number = random.randint(15, 20)

    for _ in range(new_beds_number):
        cur.execute("INSERT INTO beds(bed_id) VALUES (null)")

    database_connection.commit()


def add_patients_to_queue(database_connection: sqlite3.Connection):
    cur = database_connection.cursor()

    cur.execute("SELECT patient_id FROM patients")
    all_patient_ids = cur.fetchall()

    if all_patient_ids:
        new_patients_in_queue_number = random.randint(50, 100)
        cur.execute("SELECT Max(queue_id) AS 'max_queue_position' FROM patient_queue")
        maximum_queue_position = cur.fetchone()["max_queue_position"]

        if not maximum_queue_position:
            maximum_queue_position = 0

        for _ in range(new_patients_in_queue_number):
            # The chance that the patient will not come is about 4.5%, it's based on data from NFZ
            if random.randint(1, 22) == 1:
                will_come = 0
            else:
                will_come = 1

            cur.execute(
                "INSERT INTO patient_queue(patient_id, queue_id, will_come) VALUES (?, ?, ?)",
                (
                    random.choice(all_patient_ids)["patient_id"],
                    maximum_queue_position + 1,
                    will_come,
                ),
            )
            maximum_queue_position += 1

    database_connection.commit()


def add_patient_assignment_to_bed(database_connection: sqlite3.Connection):
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

    database_connection.commit()


if not check_data_existence("../db/hospital.db"):
    clear_database("../db/hospital.db")
    conn = sqlite3.connect("../db/hospital.db")
    conn.row_factory = sqlite3.Row

    add_patients(conn)
    add_beds(conn)
    add_patients_to_queue(conn)
    add_patient_assignment_to_bed(conn)

    conn.close()
