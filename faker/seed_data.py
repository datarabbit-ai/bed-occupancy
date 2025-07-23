import json
import logging.config
import os
import pathlib
import random

from data_generator import generate_fake_patient_data, generate_fake_personnel_data
from database_structure_manager import check_data_existence, clear_database
from dotenv import load_dotenv
from models import (
    Bed,
    BedAssignment,
    Department,
    MedicalProcedure,
    Patient,
    PatientQueue,
    PersonnelMember,
    PersonnelQueueAssignment,
    StayPersonnelAssignment,
)
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
    ("Operacja zaćmy", "Okulistyka", 1, 2, 1, 1),
    ("Laserowa korekcja wzroku", "Okulistyka", 1, 1, 1, 1),
    ("Usunięcie migdałków podniebiennych", "Laryngologia", 2, 4, 1, 2),
    ("Septoplastyka", "Laryngologia", 2, 4, 1, 2),
    ("Operacja przepukliny pachwinowej", "Chirurgia", 2, 6, 2, 2),
    ("Wycięcie wyrostka robaczkowego", "Chirurgia", 3, 7, 2, 3),
]


def add_departments(session):
    departments = list(set(procedure[1] for procedure in common_medical_procedures))
    for department in departments:
        session.add(Department(name=department))


def add_personnel(session):
    new_personnel_number = 14 * session.query(func.count(Department.department_id)).scalar()
    for _ in range(new_personnel_number):
        personnel_member = generate_fake_personnel_data(
            random.choice([d.department_id for d in session.query(Department).all()])
        )
        session.add(PersonnelMember(**personnel_member.model_dump()))
    logger.info(f"Added {new_personnel_number} generated personnel members to db")


def add_medical_procedures(session):
    for procedure in common_medical_procedures:
        department = session.query(Department).filter(Department.name == procedure[1]).first()
        session.add(
            MedicalProcedure(
                department_id=department.department_id,
                name=procedure[0],
                min_days_of_stay=procedure[2],
                max_days_of_stay=procedure[3],
                doctors_number=procedure[4],
                nurses_number=procedure[5],
            )
        )
    logger.info(f"Added {len(common_medical_procedures)} generated medical procedures to db")


def add_patients(session):
    departments_count = session.query(func.count(Department.department_id)).scalar()
    new_patients_number = random.randint(100 * departments_count, 150 * departments_count)
    for _ in range(new_patients_number):
        p = generate_fake_patient_data()
        session.add(Patient(**p.model_dump()))
    logger.info(f"Added {new_patients_number} generated patients to db")


def add_beds(session):
    department_ids = [department.department_id for department in session.query(Department).all()]
    all_beds_number = 0
    for department_id in department_ids:
        new_beds_number = random.randint(15, 20)
        beds = [Bed(department_id=department_id) for _ in range(new_beds_number)]
        session.add_all(beds)
        all_beds_number += new_beds_number
    logger.info(f"Added {all_beds_number} generated beds to db")


def add_patients_to_queue(session, free_beds_numbers, doctors_patients_numbers, nurses_patients_numbers):
    def calculate_least_occupied_department(admission_day, free_beds):
        best_department = max(free_beds, key=lambda k: free_beds[k][admission_day])
        return best_department

    all_patient_ids = [p.patient_id for p in session.query(Patient).all()]
    cooldown_ids = [b.patient_id for b in session.query(BedAssignment).all()]
    departments_count = session.query(func.count(Department.department_id)).scalar()

    if not all_patient_ids:
        return

    new_patients_in_queue_number = random.randint(90 * departments_count, 100 * departments_count)
    max_queue_position = session.query(func.max(PatientQueue.queue_id)).scalar() or 0

    available_ids = list(set(all_patient_ids) - set(cooldown_ids))
    queue_lenth = 0

    admission_day = 0

    for _ in range(new_patients_in_queue_number):
        if not available_ids:
            break

        if admission_day >= len(free_beds_numbers[1]):
            break
        while free_beds_numbers[calculate_least_occupied_department(admission_day, free_beds_numbers)][
            admission_day
        ] == 0 and admission_day + 1 < len(free_beds_numbers[1]):
            admission_day += 1

        selected = random.choice(available_ids)
        max_queue_position += 1

        least_occupied_department = calculate_least_occupied_department(admission_day, free_beds_numbers)

        medical_procedures = (
            session.query(MedicalProcedure).filter(MedicalProcedure.department_id == least_occupied_department).all()
        )
        medical_procedure = random.choice(medical_procedures)

        days_of_stay = random.randint(medical_procedure.min_days_of_stay, medical_procedure.max_days_of_stay)

        if admission_day + days_of_stay >= len(free_beds_numbers[least_occupied_department]):
            exit_day = len(free_beds_numbers[least_occupied_department])
        else:
            exit_day = admission_day + days_of_stay

        for i in range(admission_day, exit_day):
            free_beds_numbers[least_occupied_department][i] -= 1

        session.add(
            PatientQueue(
                patient_id=selected,
                queue_id=max_queue_position,
                procedure_id=medical_procedure.procedure_id,
                days_of_stay=days_of_stay,
                admission_day=admission_day + 1,
            )
        )
        queue_lenth += 1

        doctors_number = medical_procedure.doctors_number
        nurses_number = medical_procedure.nurses_number

        for _ in range(doctors_number):
            min_doctors_patients = min(
                value[admission_day] for value in doctors_patients_numbers[medical_procedure.department_id].values()
            )
            least_busy_doctor_id = random.choice(
                [
                    key
                    for key, value in doctors_patients_numbers[medical_procedure.department_id].items()
                    if value[admission_day] == min_doctors_patients
                ]
            )
            session.add(PersonnelQueueAssignment(queue_id=max_queue_position, member_id=least_busy_doctor_id))
            for i in range(admission_day, exit_day):
                doctors_patients_numbers[medical_procedure.department_id][least_busy_doctor_id][i] += 1

        for _ in range(nurses_number):
            min_nurses_patients = min(
                value[admission_day] for value in nurses_patients_numbers[medical_procedure.department_id].values()
            )
            least_busy_nurse_id = random.choice(
                [
                    key
                    for key, value in nurses_patients_numbers[medical_procedure.department_id].items()
                    if value[admission_day] == min_nurses_patients
                ]
            )
            session.add(PersonnelQueueAssignment(queue_id=max_queue_position, member_id=least_busy_nurse_id))
            for i in range(admission_day, exit_day):
                nurses_patients_numbers[medical_procedure.department_id][least_busy_nurse_id][i] += 1

        available_ids.remove(selected)
        cooldown_ids.append(selected)
        if len(cooldown_ids) >= 60 * departments_count:
            available_ids.append(cooldown_ids[0])
            cooldown_ids.pop(0)

    logger.info(f"Added {queue_lenth} patients to queue in db")


def add_patient_assignment_to_bed(session):
    beds = session.query(Bed).all()
    departments_beds = (
        session.query(Department.department_id, func.count(Bed.bed_id)).join(Bed).group_by(Department.department_id).all()
    )
    patient_ids = [p.patient_id for p in session.query(Patient).all()]
    free_beds_numbers = {department_id: [count for _ in range(20)] for department_id, count in departments_beds}

    doctors_patients_numbers = {}
    nurses_patients_numbers = {}

    assignments = 0
    for bed in beds:
        if bed.department_id not in doctors_patients_numbers and bed.department_id not in nurses_patients_numbers:
            doctors_patients_numbers[bed.department_id] = {}
            for doctor in (
                session.query(PersonnelMember)
                .filter(PersonnelMember.role == "doctor", PersonnelMember.department_id == bed.department_id)
                .all()
            ):
                doctors_patients_numbers[bed.department_id][doctor.member_id] = [0 for _ in range(20)]

            nurses_patients_numbers[bed.department_id] = {}
            for nurse in (
                session.query(PersonnelMember)
                .filter(PersonnelMember.role == "nurse", PersonnelMember.department_id == bed.department_id)
                .all()
            ):
                nurses_patients_numbers[bed.department_id][nurse.member_id] = [0 for _ in range(20)]

        if not patient_ids:
            break
        patient_id = random.choice(patient_ids)
        medical_procedures = session.query(MedicalProcedure).filter(MedicalProcedure.department_id == bed.department_id).all()

        medical_procedure = random.choice(medical_procedures)
        days_of_stay = random.randint(medical_procedure.min_days_of_stay, medical_procedure.max_days_of_stay)

        doctors_number = medical_procedure.doctors_number
        nurses_number = medical_procedure.nurses_number

        for i in range(0, days_of_stay):
            free_beds_numbers[bed.department_id][i] -= 1
        session.add(
            BedAssignment(
                bed_id=bed.bed_id,
                patient_id=patient_id,
                procedure_id=medical_procedure.procedure_id,
                days_of_stay=days_of_stay,
            )
        )

        assignments += 1

        for _ in range(doctors_number):
            min_doctors_patients = min(value[0] for value in doctors_patients_numbers[bed.department_id].values())
            least_busy_doctor_id = random.choice(
                [key for key, value in doctors_patients_numbers[bed.department_id].items() if value[0] == min_doctors_patients]
            )
            session.add(StayPersonnelAssignment(bed_id=bed.bed_id, member_id=least_busy_doctor_id))
            for i in range(0, days_of_stay):
                doctors_patients_numbers[bed.department_id][least_busy_doctor_id][i] += 1

        for _ in range(nurses_number):
            min_nurses_patients = min(value[0] for value in nurses_patients_numbers[bed.department_id].values())
            least_busy_nurse_id = random.choice(
                [key for key, value in nurses_patients_numbers[bed.department_id].items() if value[0] == min_nurses_patients]
            )
            session.add(StayPersonnelAssignment(bed_id=bed.bed_id, member_id=least_busy_nurse_id))
            for i in range(0, days_of_stay):
                nurses_patients_numbers[bed.department_id][least_busy_nurse_id][i] += 1

        patient_ids.remove(patient_id)

    logger.info(f"Assigned {assignments} patients to beds in db")
    return (free_beds_numbers, doctors_patients_numbers, nurses_patients_numbers)


def main():
    random.seed(44)
    session = SessionLocal()
    try:
        if not check_data_existence(session):
            clear_database(session)
            add_departments(session)
            add_personnel(session)
            add_medical_procedures(session)
            add_patients(session)
            add_beds(session)
            generated_simulation_data = add_patient_assignment_to_bed(session)
            add_patients_to_queue(
                session, generated_simulation_data[0], generated_simulation_data[1], generated_simulation_data[2]
            )
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
