from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class NoShow(BaseModel):
    patient_id: int
    patient_name: str


class Patient(Base):
    __tablename__ = "patients"
    patient_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    urgency = Column(String)
    contact_phone = Column(String)
    sickness = Column(String)
    pesel = Column(String, unique=True)
    gender = Column(String)

    bed_assignments = relationship("BedAssignment", back_populates="patient")
    queue_entry = relationship("PatientQueue", back_populates="patient")


class Bed(Base):
    __tablename__ = "beds"
    bed_id = Column(Integer, primary_key=True)

    assignments = relationship("BedAssignment", back_populates="bed")


class BedAssignment(Base):
    __tablename__ = "bed_assignments"
    bed_id = Column(Integer, ForeignKey("beds.bed_id"), primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"))
    days_of_stay = Column(Integer)

    bed = relationship("Bed", back_populates="assignments")
    patient = relationship("Patient", back_populates="bed_assignments")


class PatientQueue(Base):
    __tablename__ = "patient_queue"
    queue_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"))
    days_of_stay = Column(Integer)
    admission_day = Column(Integer)

    patient = relationship("Patient", back_populates="queue_entry")
