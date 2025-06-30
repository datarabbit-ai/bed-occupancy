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


class Patient(BaseModel):
    first_name: str
    last_name: str
    urgency: str
    contact_phone: str
    sickness: str
    pesel: str
    gender: str
    nationality: str


Faker.seed(42)
common_sicknesses = [
    "Endoprotezoplastyka stawu biodrowego",
    "Endoprotezoplastyka stawu kolanowego",
    "Operacja zaćmy",
    "Artroskopia stawu kolanowego",
    "Usunięcie migdałków podniebiennych",
    "Plastyka przegrody nosowej",
    "Cholecystektomia",
    "Operacja przepukliny pachwinowej",
    "Operacja żylaków kończyn dolnych",
    "Operacja kręgosłupa lędźwiowego",
    "Laparoskopia diagnostyczna",
    "Zabieg usunięcia brodawczaka krtani",
    "Adenotomia",
    "Irydektomia",
    "Kraniektomia",
    "Splenektomia",
    "Gastrektomia",
]

male_sicknesses = common_sicknesses + [
    "Prostatektomia",
    "Leczenie raka prostaty",
    "Korekcja wodniaka jądra",
    "Operacja żylaków powrózka nasiennego",
    "Rekonstrukcja cewki moczowej",
]

female_sicknesses = common_sicknesses + [
    "Histerektomia",
    "Zabieg usunięcia torbieli jajnika",
    "Zabieg usunięcia mięśniaków macicy",
    "Zabieg usunięcia guzka piersi",
    "Leczenie endometriozy",
    "Zabieg łyżeczkowania jamy macicy",
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
        random_sickness = fake.random_element(female_sicknesses)
        gender = "kobieta"
    else:
        name = fake.first_name_male().split()[0]
        surname = fake.last_name_male()
        pesel = fake.unique.pesel(date_of_birth=generate_random_date_between_ages(2, 100), sex="M")
        random_sickness = fake.random_element(male_sicknesses)
        gender = "mężczyzna"
    random_urgency = fake.enum(Urgency).value
    random_nationality = fake.enum(Nationality).value
    phone_number = fake.phone_number().replace(" ", "").replace("+48", "")
    return Patient(
        first_name=name,
        last_name=surname,
        urgency=random_urgency,
        contact_phone=phone_number,
        sickness=random_sickness,
        pesel=pesel,
        gender=gender,
        nationality=random_nationality,
    )
