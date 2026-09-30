from aiogram.filters.callback_data import CallbackData

class ClinicSelectCallback(CallbackData, prefix="clinic"):
    action: str        # 'view', 'select', 'page'
    clinic_id: int = 0
    page: int = 1

class RegionSelectCallback(CallbackData, prefix="region"):
    region_id: int
