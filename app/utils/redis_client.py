from redis import Redis
from rq import Queue, Worker


class JobError(RuntimeError):
    """
    Job error what used to properly handle traceback
    from failed job because trying to get traceback from executed process
    will cause segmentation fault and you need to get traceback from the job.exc_info
    """

    def __init__(self, job_id, exc_type, exc_value, exc_info):
        self.job_id = job_id
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.exc_info = exc_info


def job_exception_handler(job, exc_type, exc_value, traceback):
    job.meta["exc_type"] = {"exc_type": exc_type}
    job.meta["exc_value"] = {"exc_value": exc_value}
    job.save_meta()


def start_redis_queue(host: str, port: int, db: int):
    redis_conn = Redis(host=host, port=port, db=db)
    queue = Queue(connection=redis_conn)
    return (redis_conn, queue)


def start_rq_worker(host: str, port: int, db: int, queue_name: str):
    connection = Redis(host=host, port=port, db=db)
    queue = Queue(queue_name, connection)
    worker = Worker(queues=[queue], connection=connection, exception_handlers=[job_exception_handler])
    worker.work()
