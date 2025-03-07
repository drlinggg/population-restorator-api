# tobedone

import traceback

from redis import Redis
from rq import Queue, Worker

def my_handler(job, exc_type, exc_value, traceback):
    job.meta["exc_type"] = {"exc_type": exc_type}
    job.meta["exc_value"] = {"exc_value": exc_value}
    job.save_meta()


def start_redis_queue():
    redis_conn = Redis(host="localhost", port=6379, db=0)
    queue = Queue(connection=redis_conn)
    return (redis_conn, queue)


def start_rq_worker():
    connection = Redis(host="localhost", port=6379, db=0)
    queue = Queue("default", connection)
    worker = Worker(queues=[queue], connection=connection, exception_handlers=[my_handler])
    worker.work()
