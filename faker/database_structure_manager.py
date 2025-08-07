import json
import logging.config
import pathlib

from models import (
    Base,
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
from sqlalchemy import func, text
from sqlalchemy.orm import Session

logger = logging.getLogger("hospital_logger")
config_file = pathlib.Path("logger_config.json")
with open(config_file) as f:
    config = json.load(f)
logging.config.dictConfig(config)


def clear_database(session):
    session.execute(text("TRUNCATE bed_assignments, patient_queue, patients, beds RESTART IDENTITY CASCADE;"))
    session.commit()


def create_database_tables_structure(engine) -> None:
    Base.metadata.create_all(bind=engine)


def check_data_existence(session: Session) -> bool:
    create_database_tables_structure(session.get_bind())

    patient_count = session.query(func.count(Patient.patient_id)).scalar()
    bed_count = session.query(func.count(Bed.bed_id)).scalar()
    queue_count = session.query(func.count(PatientQueue.queue_id)).scalar()
    assignment_count = session.query(func.count(BedAssignment.bed_id)).scalar()
    personnel_count = session.query(func.count(PersonnelMember.member_id)).scalar()
    procedure_count = session.query(func.count(MedicalProcedure.procedure_id)).scalar()
    departments_count = session.query(func.count(Department.department_id)).scalar()

    logger.setLevel(logging.DEBUG)
    logger.debug(
        f"Found: {patient_count} patients, {departments_count} departments, {personnel_count} personnel members, {procedure_count} medical procedures, {bed_count} beds, {queue_count} patients in queue and {assignment_count} assignments of patients to beds in db"
    )

    return all(
        count > 0
        for count in [
            patient_count,
            bed_count,
            queue_count,
            assignment_count,
            personnel_count,
            procedure_count,
            departments_count,
        ]
    )
