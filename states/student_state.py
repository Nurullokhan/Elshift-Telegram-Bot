from aiogram.fsm.state import StatesGroup, State

class StudentForm(StatesGroup):
    name_surname = State()
    age = State()
    phone = State()
    address_region = State()
    address_district = State()
    previous_job = State()
    previous_salary = State()
    reason_left = State()
    computer_skill = State()
    start_date = State()
    additional = State()
    submitting = State()
