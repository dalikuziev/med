from aiogram.fsm.state import State, StatesGroup

class BookingFlow(StatesGroup):
    choosing_clinic = State()      # Klinika tanlash jarayoni
    choosing_department = State()  # Bo'lim / Yo'nalish tanlash
    choosing_doctor = State()      # Shifokor tanlash
    choosing_date = State()        # Sana tanlash
    choosing_time = State()        # Vaqt (slot) tanlash
    confirming = State()           # Tasdiqlash
