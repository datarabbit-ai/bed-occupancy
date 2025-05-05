import sqlite3
import random
from data_generator import Patient, Urgency, generate_fake_patient_data


def clear_database(path_to_database: str):
    conn = sqlite3.connect(path_to_database)

    cur = conn.cursor()

    cur.executescript("""
    DELETE FROM beds;
    DELETE FROM bed_assignments;
    DELETE FROM patients;
    DELETE FROM patient_queue;
    DELETE FROM sqlite_sequence WHERE name='beds';
    DELETE FROM sqlite_sequence WHERE name='bed_assignments';
    DELETE FROM sqlite_sequence WHERE name='patients';
    DELETE FROM sqlite_sequence WHERE name='patient_queue';
    """)

    conn.commit()

    conn.close()


def add_patients(database_connection: sqlite3.Connection):
    cur = database_connection.cursor()
    new_patients_number = random.randint(100, 150)

    for _ in range(new_patients_number):
        new_patient = generate_fake_patient_data()
        cur.execute("INSERT INTO patients(patient_id, first_name, last_name, urgency, contact_phone, sickness) VALUES (null, ?, ?, ?, ?, ?)", (new_patient.first_name, new_patient.last_name, new_patient.urgency, new_patient.contact_phone, new_patient.sickness,))
    
    database_connection.commit()


def add_beds(database_connection: sqlite3.Connection):
    cur = database_connection.cursor()
    new_beds_number = random.randint(10, 20)

    for _ in range(new_beds_number):
        cur.execute("INSERT INTO beds(bed_id) VALUES (null)")
    
    database_connection.commit()


def add_patients_to_queue(database_connection: sqlite3.Connection):
    cur = database_connection.cursor()

    cur.execute("SELECT patient_id FROM patients")
    all_patients_ids = cur.fetchall()

    if all_patients_ids:
        new_patients_in_queue_number = random.randint(150, 200)
        cur.execute("SELECT Max(queue_id) AS 'max_queue_position' FROM patient_queue")
        maximum_queue_position = cur.fetchone()['max_queue_position']
        
        for _ in range(new_patients_in_queue_number):
            cur.execute("INSERT INTO patient_queue(patient_id, queue_id) VALUES (?, ?)", (random.choice(all_patients_ids)["patient_id"], maximum_queue_position + 1,))
            maximum_queue_position += 1
        

clear_database('../db/hospital.db')