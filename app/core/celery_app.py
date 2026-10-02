from celery import Celery

# Redis broker va backend sifatida ishlatiladi
celery_app = Celery(
    "med_tasks",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/1",
    include=["app.tasks.reminder_tasks"],
)

celery_app.conf.update(
    timezone="Asia/Tashkent",
    enable_utc=False,
    # Har 10 daqiqada bazani tekshirib eslatmalarni yuborish jadvali
    beat_schedule={
        "check-upcoming-reminders-every-10-mins": {
            "task": "app.tasks.reminder_tasks.send_appointment_reminders",
            "schedule": 600.0,  # 600 soniya = 10 daqiqa
        },
    }
)

celery_app.autodiscover_tasks(["app.tasks"])
