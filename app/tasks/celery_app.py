from celery import Celery

# Docker'da aylanib turgan Redis'imizning manzili.
# "1" - bu Redis ichidagi alohida bazaning tartib raqami (0 dan 15 gacha bo'ladi)
REDIS_URL = "redis://localhost:6379/1"

celery_app = Celery(
    "med_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks.reminders']  # Kelajakda yozadigan tasklarimiz joylashuvi
)

# O'zbekiston vaqti bilan to'g'ri ishlashi uchun sozlamalar
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tashkent',
    enable_utc=False,
)
