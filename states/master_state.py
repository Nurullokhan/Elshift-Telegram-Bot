from aiogram.fsm.state import StatesGroup, State

class MasterForm(StatesGroup):
    name_surname = State()
    age = State()
    phone = State()
    address_region = State()
    address_district = State()
    specialty = State()
    experience_years = State()
    team_management = State()
    portfolio_link = State()
    more_portfolio = State()
    expected_salary_usta = State()
    hardworking_usta = State()
    start_date_usta = State()
    submitting = State()