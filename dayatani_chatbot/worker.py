import os
import redis
from rq import Worker, Queue, Connection
import os
import django

listen = ["whatsapp_chatbot_queue"]
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
conn = redis.from_url(redis_url)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dayatani_chatbot.settings')
django.setup()

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()