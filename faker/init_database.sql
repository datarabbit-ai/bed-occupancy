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
    will_come TINYINT(1) NOT NULL CHECK (will_come IN (0, 1)),
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
