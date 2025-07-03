import json
import logging.config
import os
import pathlib
import random

from data_generator import generate_fake_doctor_data, generate_fake_patient_data
from database_structure_manager import check_data_existence, clear_database
from dotenv import load_dotenv
from models import Bed, BedAssignment, Doctor, MedicalProcedure, Patient, PatientQueue
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

load_dotenv()

logger = logging.getLogger("hospital_logger")
config_file = pathlib.Path("logger_config.json")
with open(config_file) as f:
    config = json.load(f)
logging.config.dictConfig(config)

DB_USER = os.getenv("POSTGRES_USERNAME", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_NAME", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# common_sicknesses = [
#     "Endoprotezoplastyka stawu biodrowego",
#     "Endoprotezoplastyka stawu kolanowego",
#     "Operacja zaćmy",
#     "Artroskopia stawu kolanowego",
#     "Usunięcie migdałków podniebiennych",
#     "Plastyka przegrody nosowej",
#     "Cholecystektomia",
#     "Operacja przepukliny pachwinowej",
#     "Operacja żylaków kończyn dolnych",
#     "Operacja kręgosłupa lędźwiowego",
#     "Laparoskopia diagnostyczna",
#     "Zabieg usunięcia brodawczaka krtani",
#     "Adenotomia",
#     "Irydektomia",
#     "Kraniektomia",
#     "Splenektomia",
#     "Gastrektomia",
# ]

# male_sicknesses = common_sicknesses + [
#     "Prostatektomia",
#     "Leczenie raka prostaty",
#     "Korekcja wodniaka jądra",
#     "Operacja żylaków powrózka nasiennego",
#     "Rekonstrukcja cewki moczowej",
# ]

# female_sicknesses = common_sicknesses + [
#     "Histerektomia",
#     "Zabieg usunięcia torbieli jajnika",
#     "Zabieg usunięcia mięśniaków macicy",
#     "Zabieg usunięcia guzka piersi",
#     "Leczenie endometriozy",
#     "Zabieg łyżeczkowania jamy macicy",
# ]


common_medical_procedures = [
    "Usunięcie migdałków podniebiennych",
    "Operacja kręgosłupa lędźwiowego",
    "Operacja zaćmy",
    "Operacja przepukliny pachwinowej",
    "Operacja żylaków kończyn dolnych",
]


def add_doctors(session):
    new_doctors_number = 5
    for _ in range(new_doctors_number):
        doctor = generate_fake_doctor_data()
        session.add(Doctor(**doctor.model_dump()))
    logger.info(f"Added {new_doctors_number} generated doctors to db")


def add_medical_procedures(session):
    all_doctor_ids = [doctor.doctor_id for doctor in session.query(Doctor).all()]
    assigned_doctors_number = 0
    for procedure in common_medical_procedures:
        session.add(MedicalProcedure(doctor_id=all_doctor_ids[assigned_doctors_number], name=procedure))
        if assigned_doctors_number >= len(all_doctor_ids):
            assigned_doctors_number = 0
        else:
            assigned_doctors_number += 1
    logger.info(f"Added {len(common_medical_procedures)} generated medical procedures to db")


def add_patients(session):
    new_patients_number = random.randint(100, 150)
    for _ in range(new_patients_number):
        p = generate_fake_patient_data()
        session.add(Patient(**p.model_dump()))
    logger.info(f"Added {new_patients_number} generated patients to db")


def add_beds(session):
    new_beds_number = random.randint(15, 20)
    beds = [Bed() for _ in range(new_beds_number)]
    session.add_all(beds)
    logger.info(f"Added {new_beds_number} generated beds to db")


def add_patients_to_queue(session, free_beds_numbers):
    all_patient_ids = [p.patient_id for p in session.query(Patient).all()]
    cooldown_ids = [b.patient_id for b in session.query(BedAssignment).all()]
    medical_procedure_ids = [procedure.procedure_id for procedure in session.query(MedicalProcedure).all()]

    if not all_patient_ids:
        return

    new_patients_in_queue_number = random.randint(50, 100)
    max_queue_position = session.query(func.max(PatientQueue.queue_id)).scalar() or 0

    available_ids = list(set(all_patient_ids) - set(cooldown_ids))
    queue = []

    admission_day = 0

    for _ in range(new_patients_in_queue_number):
        if not available_ids:
            break

        if admission_day >= len(free_beds_numbers):
            break
        while free_beds_numbers[admission_day] == 0 and admission_day < len(free_beds_numbers):
            admission_day += 1

        selected = random.choice(available_ids)
        max_queue_position += 1

        days_of_stay = random.randint(1, 7)
        medical_procedure_id = random.choice(medical_procedure_ids)
        if admission_day + days_of_stay >= len(free_beds_numbers):
            exit_day = len(free_beds_numbers) - 1
        else:
            exit_day = admission_day + days_of_stay

        for i in range(admission_day, exit_day):
            free_beds_numbers[i] -= 1

        queue.append(
            PatientQueue(
                patient_id=selected,
                queue_id=max_queue_position,
                procedure_id=medical_procedure_id,
                days_of_stay=days_of_stay,
                admission_day=admission_day + 1,
            )
        )
        available_ids.remove(selected)
        cooldown_ids.append(selected)
        if len(cooldown_ids) >= 60:
            available_ids.append(cooldown_ids[0])
            cooldown_ids.pop(0)

    session.add_all(queue)
    logger.info(f"Added {len(queue)} patients to queue in db")


def add_patient_assignment_to_bed(session):
    bed_ids = [b.bed_id for b in session.query(Bed).all()]
    patient_ids = [p.patient_id for p in session.query(Patient).all()]
    free_beds_numbers = [len(bed_ids) for _ in range(20)]
    medical_procedure_ids = [procedure.procedure_id for procedure in session.query(MedicalProcedure).all()]

    assignments = []
    for bed_id in bed_ids:
        if not patient_ids:
            break
        patient_id = random.choice(patient_ids)
        medical_procedure_id = random.choice(medical_procedure_ids)
        days_of_stay = random.randint(1, 7)
        for i in range(0, days_of_stay):
            free_beds_numbers[i] -= 1
        assignments.append(
            BedAssignment(bed_id=bed_id, patient_id=patient_id, procedure_id=medical_procedure_id, days_of_stay=days_of_stay)
        )
        patient_ids.remove(patient_id)

    session.add_all(assignments)
    logger.info(f"Assigned {len(assignments)} patients to beds in db")
    return free_beds_numbers


def main():
    random.seed(44)
    session = SessionLocal()
    try:
        if not check_data_existence(session):
            clear_database(session)
            add_doctors(session)
            add_medical_procedures(session)
            add_patients(session)
            add_beds(session)
            free_beds_numbers = add_patient_assignment_to_bed(session)
            add_patients_to_queue(session, free_beds_numbers)
            session.commit()
        else:
            logger.info("Skipping data generation")
    except Exception as e:
        session.rollback()
        logger.error(f"Error during data generation: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
