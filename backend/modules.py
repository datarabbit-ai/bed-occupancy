from pydantic import BaseModel


class BedAssignment(BaseModel):
    bed_id: int
    patient_id: int
    patient_name: str
    sickness: str
    days_of_stay: int


class PatientQueue(BaseModel):
    patient_id: int
    patient_name: str
    queue_id: int


class NoShows(BaseModel):
    patient_id: int
    patient_name: str


class TupleOfTables(BaseModel):
    tables_tuple: tuple[PatientQueue, NoShows, BedAssignment]
