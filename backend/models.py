from pydantic import BaseModel


class BedAssignment(BaseModel):
    bed_id: int
    patient_id: int
    patient_name: str
    sickness: str
    days_of_stay: int


class PatientQueue(BaseModel):
    place_in_queue: int
    patient_id: int
    patient_name: str


class NoShow(BaseModel):
    patient_id: int
    patient_name: str


class ListOfTables(BaseModel):
    BedAssignment: list[BedAssignment]
    PatientQueue: list[PatientQueue]
    NoShows: list[NoShow]
