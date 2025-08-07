import datetime
import random
from enum import Enum

from pydantic import BaseModel

from faker import Faker


class Urgency(str, Enum):
    URGENT = "pilny"
    STABLE = "stabilny"


class Nationality(str, Enum):
    POLISH = "polska"
    UKRAINIAN = "ukraińska"


class Gender(str, Enum):
    FEMALE = "female"
    MALE = "male"


class Patient(BaseModel):
    first_name: str
    last_name: str
    urgency: str
    contact_phone: str
    pesel: str
    gender: str
    nationality: str


class PersonnelMember(BaseModel):
    department_id: int
    first_name: str
    last_name: str
    role: str


Faker.seed(42)

fake = Faker("pl_PL")
nationality_generator = random.Random()
nationality_generator.seed(45)


def generate_random_date_between_ages(min_age, max_age):
    today = datetime.date.today()
    earliest_date = datetime.date(today.year - max_age, today.month, today.day)
    latest_date = datetime.date(today.year - min_age, today.month, today.day)

    earliest_days = earliest_date.toordinal()
    latest_days = latest_date.toordinal()

    return datetime.date.fromordinal(random.randint(earliest_days, latest_days))


def generate_fake_patient_data() -> Patient:
    if random.randint(1, 2) == 1:
        name = fake.first_name_female().split()[0]
        surname = fake.last_name_female()
        pesel = fake.unique.pesel(date_of_birth=generate_random_date_between_ages(2, 100), sex="F")
        gender = Gender.FEMALE.value
    else:
        name = fake.first_name_male().split()[0]
        surname = fake.last_name_male()
        pesel = fake.unique.pesel(date_of_birth=generate_random_date_between_ages(2, 100), sex="M")
        gender = Gender.MALE.value
    random_urgency = fake.enum(Urgency).value
    if nationality_generator.randint(1, 10) < 9:
        random_nationality = Nationality.POLISH.value
    else:
        random_nationality = Nationality.UKRAINIAN.value
    phone_number = fake.phone_number().replace(" ", "").replace("+48", "")
    return Patient(
        first_name=name,
        last_name=surname,
        urgency=random_urgency,
        contact_phone=phone_number,
        pesel=pesel,
        gender=gender,
        nationality=random_nationality,
    )


def generate_fake_personnel_data(department_id: int) -> PersonnelMember:
    return PersonnelMember(
        department_id=department_id,
        first_name=fake.first_name().split()[0],
        last_name=fake.last_name(),
        role=random.choice(["doctor", "nurse"]),
    )
