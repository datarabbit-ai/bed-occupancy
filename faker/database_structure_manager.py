import sqlite3


def clear_database(path_to_database: str):
    conn = sqlite3.connect(path_to_database)

    cur = conn.cursor()

    cur.executescript(
        """
    DELETE FROM beds;
    DELETE FROM bed_assignments;
    DELETE FROM patients;
    DELETE FROM patient_queue;
    DELETE FROM sqlite_sequence WHERE name='beds';
    DELETE FROM sqlite_sequence WHERE name='bed_assignments';
    DELETE FROM sqlite_sequence WHERE name='patients';
    DELETE FROM sqlite_sequence WHERE name='patient_queue';
    """
    )

    conn.commit()

    conn.close()


def create_database_tables_structure(database_connection: sqlite3.Connection):
    with open("init_database.sql", "r", encoding="utf-8") as file:
        sql_script = file.read()

    cur = database_connection.cursor()

    cur.executescript(sql_script)

    database_connection.commit()


def check_data_existence(path_to_database: str) -> bool:
    conn = sqlite3.connect(path_to_database)
    create_database_tables_structure(conn)

    cur = conn.cursor()

    cur.execute(
        "SELECT Count(patients.patient_id), Count(beds.bed_id), Count(patient_queue.queue_id), Count(bed_assignments.bed_id) FROM patients, beds, patient_queue, bed_assignments"
    )
    result = cur.fetchone()
    conn.commit()

    conn.close()

    if result[0] == 0 or result[1] == 0 or result[2] == 0 or result[3] == 0:
        return False
    return True
