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


Faker.seed(42)

sicknesses = [
    "Niewydolność serca",
    "Choroba niedokrwienna serca",
    "Zawał mięśnia sercowego",
    "Migotanie przedsionków",
    "Nadciśnienie tętnicze",
    "Udar mózgu",
    "Krwotok śródczaszkowy",
    "Zator płucny",
    "Zapalenie płuc",
    "Przewlekła obturacyjna choroba płuc (POChP)",
    "Astma oskrzelowa",
    "Rozedma płuc",
    "Odma opłucnowa",
    "Zapalenie opłucnej",
    "Ropień płuca",
    "Gruźlica płuc",
    "Rak płuca",
    "Zapalenie oskrzeli",
    "Ostre zapalenie oskrzeli",
    "Ostre zapalenie gardła",
    "Ostre zapalenie migdałków",
    "Zapalenie zatok przynosowych",
    "Zapalenie ucha środkowego",
    "Zapalenie wyrostka robaczkowego",
    "Ostre zapalenie trzustki",
    "Przewlekłe zapalenie trzustki",
    "Kamica żółciowa",
    "Zapalenie pęcherzyka żółciowego",
    "Marskość wątroby",
    "Ostre zapalenie wątroby",
    "Rak wątroby",
    "Choroba wrzodowa żołądka",
    "Perforacja wrzodu żołądka",
    "Krwawienie z przewodu pokarmowego",
    "Zapalenie jelita grubego",
    "Choroba Leśniowskiego-Crohna",
    "Wrzodziejące zapalenie jelita grubego",
    "Niedrożność jelit",
    "Ostre zapalenie otrzewnej",
    "Przepuklina pachwinowa",
    "Przepuklina pępkowa",
    "Nowotwór jelita grubego",
    "Rak żołądka",
    "Ostre zapalenie nerek",
    "Przewlekła niewydolność nerek",
    "Kamica nerkowa",
    "Infekcja dróg moczowych",
    "Nowotwór nerki",
    "Zapalenie pęcherza moczowego",
    "Przerost prostaty",
]


def generate_fake_patient_data() -> Patient:
    fake = Faker("pl_PL")
    name = fake.first_name()
    surname = fake.last_name()
    random_urgency = fake.enum(Urgency)
    phone_number = fake.phone_number().replace(" ", "").replace("+48", "")
    random_sickness = fake.random_element(sicknesses)
    return Patient(
        first_name=name,
        last_name=surname,
        urgency=random_urgency,
        contact_phone=phone_number,
        sickness=random_sickness,
    )
