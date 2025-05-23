import json
import logging.config
import random
import traceback
from pathlib import Path
from typing import Dict, List

from db_operations import get_session
from fastapi import FastAPI, Query
from models import Bed, BedAssignment, ListOfTables, NoShow, Patient, PatientQueue, Statistics

logger = logging.getLogger("hospital_logger")
config_file = Path("logger_config.json")
with open(config_file) as f:
    config = json.load(f)
logging.config.dictConfig(config)

app = FastAPI()
day_for_simulation = 1
last_change = 1
patients_consent_dictionary: dict[int, list[int]] = {1: []}
calls_in_time: dict[str, list] = {"Date": [1], "CallsNumber": [0]}


@app.get("/get-current-day", response_model=Dict[str, int])
def get_current_day() -> Dict[str, int]:
    """
    Returns the current day of the simulation as per it's state on the server to keep the frontend and backend in sync.
    :return: JSON object with the current day of the simulation.
    """
    global day_for_simulation
    return {"day": day_for_simulation}


@app.get("/update-day", response_model=Dict[str, int])
def update_day(delta: int = Query(...)) -> Dict[str, int]:
    """
    Updates the current day of the simulation.
    :param delta: Either -1 or 1 to signal a rollback or a forward.
    :return: Returns the day resolved on the server side.
    """
    global day_for_simulation, last_change
    if delta not in (-1, 1):
        return {"error": "Invalid delta value. Use -1 or 1."}
    if delta == 1 and day_for_simulation < 20 or delta == -1 and day_for_simulation > 1:
        day_for_simulation += delta
        last_change = delta
        if delta == 1:
            patients_consent_dictionary[day_for_simulation] = []
            calls_in_time["Date"].append(day_for_simulation)
            calls_in_time["CallsNumber"].append(0)
        else:
            patients_consent_dictionary.pop(day_for_simulation + 1)
            calls_in_time["Date"].pop(day_for_simulation)
            calls_in_time["CallsNumber"].pop(day_for_simulation)
    return {"day": day_for_simulation}


@app.get("/get-tables-and-statistics", response_model=ListOfTables)
def get_tables_and_statistics() -> ListOfTables:
    """
    Returns the current state of the simulation.
    :return: A JSON object with three lists: BedAssignment, PatientQueue, and NoShows.
    """

    day = day_for_simulation
    rollback_flag = last_change
    consent_dict = patients_consent_dictionary.copy()
    calls_numbers_dict = calls_in_time.copy()
    occupancy_in_time = {"Date": [1], "Occupancy": [100]}
    no_shows_in_time = {"Date": [1], "NoShows": [0]}
    stay_lengths = {}

    def decrement_days_of_stay():
        for ba in session.query(BedAssignment).all():
            ba.days_of_stay -= 1

    def print_patients_to_be_released(log: bool):
        patients_to_release = (
            session.query(Patient)
            .filter(Patient.patient_id.in_(session.query(BedAssignment.patient_id).filter(BedAssignment.days_of_stay <= 0)))
            .all()
        )
        if log and patients_to_release:
            logger.info(
                "Patients to be released from hospital:\n"
                + "\n".join(f"Patient ID: {p.patient_id}, Name: {p.first_name} {p.last_name}" for p in patients_to_release)
            )

    def delete_patients_to_be_released():
        session.query(BedAssignment).filter(BedAssignment.days_of_stay <= 0).delete(synchronize_session="auto")

    def assign_bed_to_patient(bed_id: int, patient_id: int, days: int, log: bool):
        assignment = BedAssignment(bed_id=bed_id, patient_id=patient_id, days_of_stay=days)
        session.add(assignment)
        if log:
            logger.info(f"Assigned bed {bed_id} to patient {patient_id} for {days} days")

    def check_if_patient_has_bed(patient_id: int) -> bool:
        return session.query(BedAssignment).filter_by(patient_id=patient_id).first() is not None

    def delete_patient_by_id_from_queue(patient_id: int):
        entry = session.query(PatientQueue).filter_by(patient_id=patient_id).order_by(PatientQueue.queue_id).first()
        if entry:
            session.delete(entry)
            queue = session.query(PatientQueue).order_by(PatientQueue.queue_id).all()
            for i, entry in enumerate(queue):
                entry.queue_id = i + 1

    def get_patient_name_by_id(patient_id: int) -> str:
        patient = session.query(Patient).filter_by(patient_id=patient_id).first()
        return f"{patient.first_name} {patient.last_name}" if patient else "Unknown"

    def get_beds_number() -> int:
        return session.query(Bed).count()

    def calculate_average_in_dictionary(data: dict) -> float:
        total_sum = sum(sum(v) for v in data.values() if isinstance(v, list))
        total_items_number = sum(len(v) for v in data.values() if isinstance(v, list))
        logger.info(str(total_sum) + ", " + str(total_items_number))
        return total_sum / total_items_number

    def calculate_statistics() -> Statistics:
        # Calculation of average length of stay
        avg_stay_length = calculate_average_in_dictionary(stay_lengths)
        if len(stay_lengths) != 1:
            max_key = max(stay_lengths.keys())
            stay_lengths.pop(max_key)
            avg_stay_length_diff = avg_stay_length - calculate_average_in_dictionary(stay_lengths)
        else:
            avg_stay_length_diff = 0

        # Hospital occupancy calculations
        occupancy_data = occupancy_in_time["Occupancy"].copy()

        if len(occupancy_data) != 1:
            occupancy = occupancy_data[-1]
            occupancy_diff = occupancy_data[-1] - occupancy_data[-2]

            avg_occupancy = sum(occupancy_data) / len(occupancy_data)
            occupancy_data.pop(-1)
            avg_occupancy_diff = avg_occupancy - (sum(occupancy_data) / len(occupancy_data))
        else:
            occupancy = occupancy_data[0]
            occupancy_diff = 0

            avg_occupancy = occupancy_data[0]
            avg_occupancy_diff = 0

        # No-shows calculations
        no_shows_data = no_shows_in_time["NoShows"].copy()

        if len(no_shows_data) != 1:
            no_shows_perc = no_shows_data[-1]
            no_shows_perc_diff = no_shows_data[-1] - no_shows_data[-2]

            avg_no_shows_perc = sum(no_shows_data) / len(no_shows_data)
            no_shows_data.pop(-1)
            avg_no_shows_perc_diff = avg_no_shows_perc - (sum(no_shows_data) / len(no_shows_data))
        else:
            no_shows_perc = no_shows_data[0]
            no_shows_perc_diff = 0

            avg_no_shows_perc = no_shows_data[0]
            avg_no_shows_perc_diff = 0

        # Calls calculations
        percentage_list = []
        for i in range(len(calls_numbers_dict["CallsNumber"])):
            if calls_numbers_dict["CallsNumber"][i] != 0:
                percentage_list.append(len(consent_dict[i + 1]) / calls_numbers_dict["CallsNumber"][i] * 100)
            else:
                percentage_list.append("No calls made")

        consent_percentage = percentage_list[-1]
        consent_percentage_diff = (
            percentage_list[-1] - percentage_list[-2]
            if percentage_list[-1] != "No calls made" and percentage_list[-2] != "No calls made"
            else "No calls made"
        )

        total_sum = sum(x for x in percentage_list if x != "No calls made")
        items_number = sum(1 for x in percentage_list if x != "No calls made")
        avg_consent_perc = total_sum / items_number if items_number != 0 else "No calls made"

        percentage_list.pop(-1)

        total_sum = sum(x for x in percentage_list if x != "No calls made")
        items_number = sum(1 for x in percentage_list if x != "No calls made")
        avg_consent_perc_diff = total_sum / items_number if items_number != 0 else "No calls made"

        return Statistics(
            OccupancyInTime=occupancy_in_time,
            Occupancy=f"{occupancy:.3f}".rstrip("0").rstrip(".") + "%",
            OccupancyDifference=f"{occupancy_diff:.3f}".rstrip("0").rstrip(".") + "%",
            AverageOccupancy=f"{avg_occupancy:.3f}".rstrip("0").rstrip(".") + "%",
            AverageOccupancyDifference=f"{avg_occupancy_diff:.3f}".rstrip("0").rstrip(".") + "%",
            AverageStayLength=f"{avg_stay_length:.3f}".rstrip("0").rstrip("."),
            AverageStayLengthDifference=f"{avg_stay_length_diff:.3f}".rstrip("0").rstrip("."),
            NoShowsInTime=no_shows_in_time,
            NoShowsPercentage=f"{no_shows_perc:.3f}".rstrip("0").rstrip(".") + "%",
            NoShowsPercentageDifference=f"{no_shows_perc_diff:.3f}".rstrip("0").rstrip(".") + "%",
            AverageNoShowsPercentage=f"{avg_no_shows_perc:.3f}".rstrip("0").rstrip(".") + "%",
            AverageNoShowsPercentageDifference=f"{avg_no_shows_perc_diff:.3f}".rstrip("0").rstrip(".") + "%",
            CallsInTime=calls_numbers_dict,
            ConsentsPercentage=f"{consent_percentage:.3f}".rstrip("0").rstrip(".") + "%"
            if consent_percentage != "No calls made"
            else "No calls made",
            ConsentsPercentageDifference=f"{consent_percentage_diff:.3f}".rstrip("0").rstrip(".") + "%"
            if consent_percentage_diff != "No calls made"
            else "No calls made",
            AverageConstentsPercentage=f"{avg_consent_perc:.3f}".rstrip("0").rstrip(".") + "%"
            if avg_consent_perc != "No calls made"
            else "No calls made",
            AverageConstentsPercentageDifference=f"{avg_consent_perc_diff:.3f}".rstrip("0").rstrip(".") + "%"
            if avg_consent_perc_diff != "No calls made"
            else "No calls made",
        )

    try:
        rnd = random.Random()
        rnd.seed(43)
        session = get_session()

        stay_lengths[1] = [d[0] for d in session.query(BedAssignment.days_of_stay).all()]

        beds_number = get_beds_number()

        if rollback_flag == 1:
            logger.info(f"Current simulation day: {day}")
        else:
            logger.info(f"Rollback of simulation to day {day}")

        no_shows_list: List[NoShow] = []

        for iteration in range(day - 1):
            should_log = iteration == day - 2 and rollback_flag == 1
            should_give_no_shows = iteration == day - 2

            decrement_days_of_stay()
            print_patients_to_be_released(log=should_log)
            delete_patients_to_be_released()

            assigned_beds = session.query(BedAssignment.bed_id).scalar_subquery()
            bed_ids = [b.bed_id for b in session.query(Bed).filter(~Bed.bed_id.in_(assigned_beds)).all()]

            occupied_beds_number = beds_number - len(bed_ids)
            no_shows_number = 0

            queue = session.query(PatientQueue).order_by(PatientQueue.queue_id).all()
            bed_iterator = 0

            for i in range(min(len(queue), len(bed_ids))):
                entry = queue[i]
                patient_id = entry.patient_id
                will_come = rnd.choice([True] * 4 + [False])
                if not will_come:
                    no_shows_number += 1

                    delete_patient_by_id_from_queue(patient_id)
                    no_show = NoShow(patient_id=patient_id, patient_name=get_patient_name_by_id(patient_id))
                    if should_give_no_shows:
                        no_shows_list.append(no_show)
                    if should_log:
                        logger.info(f"No-show: {no_show.patient_name}")
                elif check_if_patient_has_bed(patient_id):
                    if should_log:
                        logger.info(f"Patient {patient_id} already has a bed")
                else:
                    days = rnd.randint(1, 7)

                    if iteration + 2 not in stay_lengths:
                        stay_lengths[iteration + 2] = []
                    stay_lengths[iteration + 2].append(days)

                    assign_bed_to_patient(bed_ids[bed_iterator], patient_id, days, should_log)
                    delete_patient_by_id_from_queue(patient_id)
                    occupied_beds_number += 1
                    bed_iterator += 1

            for patient_id in consent_dict[iteration + 2]:
                if check_if_patient_has_bed(patient_id):
                    if should_log:
                        logger.info(f"Patient {patient_id} already has a bed")
                else:
                    days = rnd.randint(1, 7)

                    if iteration + 2 not in stay_lengths:
                        stay_lengths[iteration + 2] = []
                    stay_lengths[iteration + 2].append(days)

                    assign_bed_to_patient(bed_ids[bed_iterator], patient_id, days, should_log)
                    delete_patient_by_id_from_queue(patient_id)
                    occupied_beds_number += 1
                    bed_iterator += 1

            occupancy_in_time["Date"].append(iteration + 2)
            occupancy_in_time["Occupancy"].append(occupied_beds_number / beds_number * 100)

            no_shows_in_time["Date"].append(iteration + 2)
            no_shows_in_time["NoShows"].append(no_shows_number / len(bed_ids) * 100)

        bed_assignments = []
        for bed in (
            session.query(Bed)
            .join(BedAssignment, Bed.bed_id == BedAssignment.bed_id, isouter=True)
            .join(Patient, BedAssignment.patient_id == Patient.patient_id, isouter=True)
            .order_by(Bed.bed_id)
            .all()
        ):
            ba = session.query(BedAssignment).filter_by(bed_id=bed.bed_id).first()
            patient = ba.patient if ba else None

            patient_name = f"{patient.first_name} {patient.last_name}" if patient else "Unoccupied"
            sickness = patient.sickness if patient else "Unoccupied"
            pesel = patient.pesel if patient else "Unoccupied"
            days_of_stay = ba.days_of_stay if ba else 0

            bed_assignments.append(
                {
                    "bed_id": bed.bed_id,
                    "patient_id": ba.patient_id if ba else 0,
                    "patient_name": patient_name,
                    "sickness": sickness,
                    "pesel": pesel,
                    "days_of_stay": days_of_stay,
                }
            )

        queue_data = []
        for entry in session.query(PatientQueue).order_by(PatientQueue.queue_id).all():
            patient = session.query(Patient).filter_by(patient_id=entry.patient_id).first()
            queue_data.append(
                {
                    "place_in_queue": entry.queue_id,
                    "patient_id": patient.patient_id,
                    "patient_name": f"{patient.first_name} {patient.last_name}",
                    "pesel": f"...{patient.pesel[-3:]}",
                }
            )

        session.rollback()
        session.close()

        return ListOfTables(
            BedAssignment=bed_assignments,
            PatientQueue=queue_data,
            NoShows=[n.model_dump() for n in no_shows_list],
            Statistics=calculate_statistics(),
        )

    except Exception as e:
        error_message = f"Error occurred: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_message)
        return {"error": "Server Error", "message": error_message}


@app.get("/add-patient-to-approvers")
def add_patient_to_approvers(patient_id: int) -> None:
    patients_consent_dictionary[day_for_simulation].append(patient_id)


@app.get("/increase-calls-number")
def increase_calls_number() -> None:
    calls_in_time["CallsNumber"][day_for_simulation - 1] += 1


@app.get("/get-patient-data")
def get_patient_data(patient_id: int):
    session = get_session()
    patient = session.query(Patient).filter_by(patient_id=patient_id).first()
    sickness = patient.sickness
    old_day, new_day = day_for_simulation + random.randint(2, 4), day_for_simulation
    session.rollback()
    session.close()
    return {"sickness": sickness, "old_day": old_day, "new_day": new_day}
