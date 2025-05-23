import datetime
import random
from enum import Enum

from pydantic import BaseModel

from faker import Faker


class Urgency(str, Enum):
    URGENT = "pilny"
    STABLE = "stabilny"


class Patient(BaseModel):
    first_name: str
    last_name: str
    urgency: Urgency
    contact_phone: str
    sickness: str
    pesel: str
    gender: str


Faker.seed(42)

sicknesses = [
    "Zapalenie płuc",
    "Udar",
    "Zawał",
    "Niewydolność serca",
    "Grypa",
    "COVID-19",
    "Astma",
    "Zapalenie oskrzeli",
    "Zapalenie opłucnej",
    "Zapalenie opon",
    "Sepsa",
    "Odwodnienie",
    "Cukrzyca",
    "Zapalenie trzustki",
    "Zapalenie wątroby",
    "Zapalenie nerek",
    "Niewydolność nerek",
    "Kamica nerkowa",
    "Kamica żółciowa",
    "Zapalenie wyrostka",
    "Wrzody",
    "Padaczka",
    "Borelioza",
    "Złamanie nogi",
    "Złamanie ręki",
    "Złamanie biodra",
    "Skręcenie kostki",
    "Zwichnięcie barku",
    "Oparzenie",
    "Odmrożenie",
    "Zatrucie",
    "Migdałki",
    "Choroba Parkinsona",
    "Choroba Crohna",
    "Wrzodziejące jelito",
    "Zapalenie stawów",
    "Tężec",
    "Nadciśnienie",
    "Niedociśnienie",
]

fake = Faker("pl_PL")


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
        gender = "kobieta"
    else:
        name = fake.first_name_male().split()[0]
        surname = fake.last_name_male()
        pesel = fake.unique.pesel(date_of_birth=generate_random_date_between_ages(2, 100), sex="M")
        gender = "mążczyzna"
    random_urgency = fake.enum(Urgency)
    phone_number = fake.phone_number().replace(" ", "").replace("+48", "")
    random_sickness = fake.random_element(sicknesses)
    return Patient(
        first_name=name,
        last_name=surname,
        urgency=random_urgency,
        contact_phone=phone_number,
        sickness=random_sickness,
        pesel=pesel,
        gender=gender,
    )
