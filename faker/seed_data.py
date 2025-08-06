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


common_medical_procedures = {
    "ENT": [
        ("sleep apnea monitoring", 3, 1, 2),
        ("hearing test battery", 1, 1, 1),
        ("tympanometry", 1, 1, 1),
        ("laryngoscopy", 2, 1, 2),
        ("nasal endoscopy", 2, 1, 2),
        ("allergy skin testing", 2, 1, 1),
        ("sinus CT scan", 1, 1, 1),
        ("vestibular function test", 2, 1, 2),
        ("rhinomanometry", 1, 1, 1),
    ],
    "Ophthalmology": [
        ("OCT scan", 1, 1, 1),
        ("fundus photography", 1, 1, 1),
        ("corneal topography", 1, 1, 1),
        ("intraocular pressure check", 1, 1, 1),
        ("pupil dilation exam", 1, 1, 1),
        ("fluorescein angiography", 1, 1, 1),
        ("A-scan biometry", 1, 1, 1),
        ("pachymetry", 1, 1, 1),
        ("tear film assessment", 1, 1, 1),
        ("retinal imaging", 1, 1, 1),
        ("electroretinography", 1, 1, 2),
    ],
    "Surgery": [
        ("cardiac stress test", 1, 1, 1),
        ("echocardiogram", 1, 1, 1),
        ("EKG monitoring", 1, 1, 1),
        ("blood work panel", 1, 1, 1),
        ("abdominal ultrasound", 1, 1, 1),
        ("wound assessment", 1, 1, 2),
        ("nutritional consultation", 1, 1, 1),
        ("anesthesia consultation", 1, 1, 1),
    ],
    "Cardiology": [
        ("holter monitoring", 2, 1, 1),
        ("event monitor setup", 1, 1, 1),
        ("cardiac catheterization prep", 1, 2, 2),
        ("stress echocardiogram", 1, 1, 2),
        ("cardiac MRI", 1, 1, 1),
        ("coronary angiography", 1, 2, 2),
        ("heart rhythm analysis", 1, 1, 1),
        ("blood pressure monitoring", 2, 1, 1),
        ("lipid profile testing", 1, 1, 1),
        ("cardiac enzyme testing", 1, 1, 1),
        ("exercise tolerance test", 1, 1, 1),
    ],
    "Neurology": [
        ("EEG monitoring", 3, 1, 2),
        ("nerve conduction study", 1, 1, 1),
        ("EMG testing", 1, 1, 1),
        ("brain MRI", 1, 1, 1),
        ("lumbar puncture", 1, 2, 2),
        ("cognitive assessment", 2, 1, 1),
        ("sleep study", 2, 1, 2),
        ("evoked potential testing", 1, 1, 1),
        ("transcranial doppler", 1, 1, 1),
        ("neuropsychological testing", 2, 1, 2),
        ("balance disorder evaluation", 1, 1, 1),
    ],
    "Radiology": [
        ("CT scan", 1, 1, 1),
        ("MRI scan", 1, 1, 1),
        ("ultrasound examination", 1, 1, 1),
        ("X-ray imaging", 1, 1, 1),
        ("mammography", 1, 1, 1),
        ("bone density scan", 1, 1, 1),
        ("contrast study", 1, 1, 1),
        ("fluoroscopy", 1, 1, 1),
        ("nuclear medicine scan", 1, 2, 2),
        ("PET scan", 1, 2, 2),
        ("biopsy guidance", 1, 2, 2),
    ],
    "Gynecology": [
        ("mammography", 1, 1, 1),
        ("bone density scan", 1, 1, 1),
        ("HPV testing", 1, 1, 1),
        ("colposcopy", 2, 1, 2),
        ("fertility assessment", 1, 1, 1),
        ("menstrual cycle monitoring", 2, 1, 1),
        ("hormone level testing", 3, 1, 1),
        ("STI screening panel", 1, 1, 1),
        ("pregnancy monitoring", 4, 1, 2),
        ("contraception consultation", 1, 1, 1),
        ("menopause evaluation", 2, 1, 1),
    ],
}


def add_departments(session):
    for department in common_medical_procedures.keys():
        session.add(Department(name=department))


def add_personnel(session):
    new_personnel_number = 12 * session.query(func.count(Department.department_id)).scalar()
    for _ in range(new_personnel_number):
        personnel_member = generate_fake_personnel_data(
            random.choice([d.department_id for d in session.query(Department).all()])
        )
        session.add(PersonnelMember(**personnel_member.model_dump()))
    logger.info(f"Added {new_personnel_number} generated personnel members to db")


def add_medical_procedures(session):
    procedures_added = 0
    for department_name, procedures in common_medical_procedures.items():
        department = session.query(Department).filter(Department.name == department_name).first()
        for procedure in procedures:
            session.add(
                MedicalProcedure(
                    department_id=department.department_id,
                    name=procedure[0],
                    days_of_stay=procedure[1],
                    doctors_number=procedure[2],
                    nurses_number=procedure[3],
                )
            )
            procedures_added += 1
    logger.info(f"Added {procedures_added} generated medical procedures to db")


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
        new_beds_number = random.randint(16, 18)
        beds = [Bed(department_id=department_id) for _ in range(new_beds_number)]
        session.add_all(beds)
        all_beds_number += new_beds_number
    logger.info(f"Added {all_beds_number} generated beds to db")


def add_patients_to_queue(session, free_beds_numbers, doctors_patients_numbers, nurses_patients_numbers):
    def calculate_least_occupied_department(
        admission_day: int, free_beds: dict, gynecology_department_id: int, females_number: int
    ):
        departments_to_consider = (
            free_beds.keys()
            if females_number > 0 and gynecology_department_id != 0
            else [k for k in free_beds if k != gynecology_department_id]
        )

        best_department = max(departments_to_consider, key=lambda k: free_beds[k][admission_day])
        return best_department

    all_patient_ids = [p.patient_id for p in session.query(Patient).all()]
    all_female_ids = [f.patient_id for f in session.query(Patient).filter(Patient.gender == "female").all()]
    cooldown_ids = [b.patient_id for b in session.query(BedAssignment).all()]
    departments_count = session.query(func.count(Department.department_id)).scalar()
    should_exit = False

    if not all_patient_ids:
        return

    new_patients_in_queue_number = random.randint(200 * departments_count, 230 * departments_count)
    max_queue_position = session.query(func.max(PatientQueue.queue_id)).scalar() or 0

    available_ids = list(set(all_patient_ids) - set(cooldown_ids))
    queue_lenth = 0

    admission_day = 0

    gynecology_department = session.query(Department).filter(Department.name == "Gynecology").first()
    gynecology_department_id = gynecology_department.department_id if gynecology_department else 0

    for _ in range(new_patients_in_queue_number):
        if not available_ids:
            break

        if admission_day >= len(free_beds_numbers[1]):
            break

        while (
            free_beds_numbers[
                calculate_least_occupied_department(
                    admission_day,
                    free_beds_numbers,
                    gynecology_department_id,
                    len(list(set(all_female_ids) & set(available_ids))),
                )
            ][admission_day]
            == 0
        ):
            if admission_day + 1 < len(free_beds_numbers[1]):
                admission_day += 1
            else:
                logger.info(f"Added {queue_lenth} patients to queue in db")
                should_exit = True
                break

        if should_exit:
            break

        max_queue_position += 1

        least_occupied_department = calculate_least_occupied_department(
            admission_day, free_beds_numbers, gynecology_department_id, len(list(set(all_female_ids) & set(available_ids)))
        )

        medical_procedures = (
            session.query(MedicalProcedure).filter(MedicalProcedure.department_id == least_occupied_department).all()
        )
        medical_procedure = random.choice(medical_procedures)

        if least_occupied_department == gynecology_department_id:
            selected = random.choice(list(set(all_female_ids) & set(available_ids)))
        else:
            selected = random.choice(available_ids)

        days_of_stay = medical_procedure.days_of_stay

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
        if len(cooldown_ids) >= 80 * departments_count:
            available_ids.append(cooldown_ids[0])
            cooldown_ids.pop(0)

    logger.info(f"Added {queue_lenth} patients to queue in db")


def add_patient_assignment_to_bed(session):
    beds = session.query(Bed).all()
    departments_beds = (
        session.query(Department.department_id, func.count(Bed.bed_id)).join(Bed).group_by(Department.department_id).all()
    )
    patient_ids = [p.patient_id for p in session.query(Patient).all()]
    all_female_ids = [f.patient_id for f in session.query(Patient).filter(Patient.gender == "female").all()]
    free_beds_numbers = {department_id: [count for _ in range(20)] for department_id, count in departments_beds}

    doctors_patients_numbers = {}
    nurses_patients_numbers = {}

    gynecology_department = session.query(Department).filter(Department.name == "Gynecology").first()

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

        if gynecology_department is not None and bed.department_id == gynecology_department.department_id:
            patient_id = random.choice(list(set(all_female_ids) & set(patient_ids)))
        else:
            patient_id = random.choice(patient_ids)

        medical_procedures = session.query(MedicalProcedure).filter(MedicalProcedure.department_id == bed.department_id).all()

        medical_procedure = random.choice(medical_procedures)
        days_of_stay = medical_procedure.days_of_stay

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
