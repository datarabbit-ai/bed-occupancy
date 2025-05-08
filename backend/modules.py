from pydantic import BaseModel


class BedAssignment(BaseModel):
    bed_id: int
    patient_id: int
    patient_name: str
    sickness: str
    days_of_stay: int
