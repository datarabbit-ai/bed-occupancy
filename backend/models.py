from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class BedAssignmentResponse(BaseModel):
    bed_id: int
    patient_id: int
    patient_name: str
    medical_procedure: str
    pesel: str
    nationality: str
    days_of_stay: int
    personnel: Optional[dict]


class PatientQueueResponse(BaseModel):
    place_in_queue: int
    patient_id: int
    patient_name: str
    pesel: str
    nationality: str
    admission_day: int
    days_of_stay: int
    medical_procedure: str
    department: str


class NoShow(BaseModel):
    patient_id: int
    patient_name: str


class Statistics(BaseModel):
    OccupancyInTime: dict[str, list]
    Occupancy: str
    OccupancyDifference: str
    AverageOccupancy: str
    AverageOccupancyDifference: str
    AverageStayLength: str
    AverageStayLengthDifference: str
    NoShowsInTime: dict[str, list]
    NoShowsPercentage: str
    NoShowsPercentageDifference: str
    AverageNoShowsPercentage: str
    AverageNoShowsPercentageDifference: str
    CallsInTime: dict[str, list]
    ConsentsPercentage: str
    ConsentsPercentageDifference: str
    AverageConstentsPercentage: str
    AverageConstentsPercentageDifference: str


class DataForReplacement(BaseModel):
    DaysOfStay: Optional[list[int]]
    MedicalProcedures: Optional[list[str]]
    Departments: Optional[list[str]]


class ListOfTables(BaseModel):
    DepartmentAssignments: dict[str, BedAssignmentResponse]
    AllBedAssignments: BedAssignmentResponse
    PatientQueue: list[PatientQueueResponse]
    NoShows: list[NoShow]
    Statistics: Statistics
    ReplacementData: DataForReplacement


class Patient(Base):
    __tablename__ = "patients"
    patient_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    urgency = Column(String)
    contact_phone = Column(String)
    pesel = Column(String, unique=True)
    gender = Column(String)
    nationality = Column(String)

    bed_assignments = relationship("BedAssignment", back_populates="patient")
    queue_entry = relationship("PatientQueue", back_populates="patient")


class Bed(Base):
    __tablename__ = "beds"
    bed_id = Column(Integer, primary_key=True)
    department_id = Column(Integer, ForeignKey("departments.department_id"))

    assignments = relationship("BedAssignment", back_populates="bed")
    department = relationship("Department", back_populates="bed")


class BedAssignment(Base):
    __tablename__ = "bed_assignments"
    bed_id = Column(Integer, ForeignKey("beds.bed_id"), primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"))
    procedure_id = Column(Integer, ForeignKey("medical_procedures.procedure_id"))
    days_of_stay = Column(Integer)

    bed = relationship("Bed", back_populates="assignments")
    patient = relationship("Patient", back_populates="bed_assignments")
    medical_procedure = relationship("MedicalProcedure", back_populates="assignments")
    stay_personnel_assignment = relationship("StayPersonnelAssignment", back_populates="bed_assignment", passive_deletes=True)


class PatientQueue(Base):
    __tablename__ = "patient_queue"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"))
    procedure_id = Column(Integer, ForeignKey("medical_procedures.procedure_id"))
    queue_id = Column(Integer)
    days_of_stay = Column(Integer)
    admission_day = Column(Integer)

    patient = relationship("Patient", back_populates="queue_entry")
    medical_procedure = relationship("MedicalProcedure", back_populates="queue_entry")
    personnel_queue_assignment = relationship("PersonnelQueueAssignment", back_populates="queue_entry")


class MedicalProcedure(Base):
    __tablename__ = "medical_procedures"
    procedure_id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.department_id"))
    name = Column(String)

    queue_entry = relationship("PatientQueue", back_populates="medical_procedure")
    assignments = relationship("BedAssignment", back_populates="medical_procedure")
    department = relationship("Department", back_populates="medical_procedure")


class PersonnelMember(Base):
    __tablename__ = "personnel_members"
    member_id = Column(Integer, primary_key=True, autoincrement=True)
    department_id = Column(Integer, ForeignKey("departments.department_id"))
    first_name = Column(String)
    last_name = Column(String)
    role = Column(String)

    department = relationship("Department", back_populates="personnel_member")
    personnel_queue_assignment = relationship("PersonnelQueueAssignment", back_populates="personnel_member")
    stay_personnel_assignment = relationship("StayPersonnelAssignment", back_populates="personnel_member")


class PersonnelQueueAssignment(Base):
    __tablename__ = "personnel_queue_assignments"
    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    queue_id = Column(Integer, ForeignKey("patient_queue.id", onupdate="CASCADE", ondelete="CASCADE"))
    member_id = Column(Integer, ForeignKey("personnel_members.member_id"))

    personnel_member = relationship("PersonnelMember", back_populates="personnel_queue_assignment")
    queue_entry = relationship("PatientQueue", back_populates="personnel_queue_assignment")


class StayPersonnelAssignment(Base):
    __tablename__ = "stay_personnel_assignments"
    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    bed_id = Column(Integer, ForeignKey("bed_assignments.bed_id", ondelete="CASCADE"))
    member_id = Column(Integer, ForeignKey("personnel_members.member_id"))

    personnel_member = relationship("PersonnelMember", back_populates="stay_personnel_assignment")
    bed_assignment = relationship("BedAssignment", back_populates="stay_personnel_assignment")


class Department(Base):
    __tablename__ = "departments"
    department_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

    personnel_member = relationship("PersonnelMember", back_populates="department")
    medical_procedure = relationship("MedicalProcedure", back_populates="department")
    bed = relationship("Bed", back_populates="department")
