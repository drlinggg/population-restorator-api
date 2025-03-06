# tobedone

from redis import Redis
from rq import Queue, Worker


def start_redis_queue():
    redis_conn = Redis(host="localhost", port=6379, db=0)
    queue = Queue(connection=redis_conn)
    return (redis_conn, queue)


def start_rq_worker():
    connection = Redis(host="localhost", port=6379, db=0)
    queue = Queue("default", connection)
    worker = Worker(queues=[queue], connection=connection)
    worker.work()
