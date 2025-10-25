from aiogram.fsm.state import StatesGroup, State

class ApprenticeForm(StatesGroup):
    name_surname = State()
    age = State()
    phone = State()
    address_region = State()
    address_district = State()
    previous_job = State()
    previous_salary = State()
    reason_left = State()
    expected_salary = State()
    goal = State()
    math_skill = State()
    hardworking = State()
    start_date = State()
    additional = State()
    submitting = State()