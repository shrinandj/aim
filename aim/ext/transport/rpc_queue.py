import time
import grpc
import queue
import logging
import threading

from aim.ext.cleanup import AutoClean

logger = logging.getLogger(__name__)


class RpcQueueAutoClean(AutoClean):
    PRIORITY = 100  # Priority of RpcQueueAutoClean should be higher than priority of RunAutoClean

    def __init__(self, instance: 'RpcQueueWithRetry') -> None:
        """
        Prepare the `RpcQueueWithRetry` for automatic cleanup.

        Args:
            instance: The `RpcQueueWithRetry` instance to be cleaned up.
        """
        super().__init__(instance)
        self._queue = None
        self._shutdown = None
        self._name = None

    def _close(self):
        """
        Wait until rpc queue is empty
        """
        pending_task_count = self._queue.qsize()
        if pending_task_count:
            logger.warning(f'Processing {pending_task_count} pending tasks in the rpc queue \'{self._name}\'... '
                           f'Please do not kill the process.')
            self._queue.join()
        logger.debug('No pending tasks left.')
        self._shutdown = True


class RpcQueueWithRetry(object):
    def __init__(self, name, max_queue_memory=0,
                 retry_count=0, retry_interval=0):
        self._resources: RpcQueueAutoClean = None

        self.retry_count = retry_count or 1
        self.retry_interval = retry_interval

        self.max_memory_usage = max_queue_memory
        self.current_memory_usage = 0

        self._resources = RpcQueueAutoClean(self)
        self._resources._shutdown = False
        self._resources._queue = queue.Queue()
        self._resources._name = name

        self._thread = threading.Thread(target=self.worker)
        self._thread.daemon = True
        self._thread.start()

    @property
    def _queue(self):
        return self._resources._queue

    @property
    def _shutdown(self):
        return self._resources._shutdown

    def register_task(self, task_f, *args):
        if self._shutdown:
            logger.debug('Cannot register task: rpc task queue is stopped.')
            return

        arg_size = self._calculate_size(args)
        with self._queue.not_full:
            while self.current_memory_usage + arg_size >= self.max_memory_usage:
                self._queue.not_full.wait()

        with self._queue.mutex:
            self.current_memory_usage += arg_size

        self._queue.put((task_f, args))

    def worker(self):
        while True:
            if self._shutdown:
                logger.debug(f'Shutting down worker thread {threading.get_ident()}.')
                break
            task_f, args = self._queue.get()
            if self._try_exec_task(task_f, *args):
                arg_size = self._calculate_size(args)
                with self._queue.mutex:
                    self.current_memory_usage -= arg_size
                # clear the unnecessary references
                task_f, args = None, None
                self._queue.task_done()
            else:
                self._put_front(task_f, args)

    def _try_exec_task(self, task_f, *args):
        retry = 0
        while retry < self.retry_count:
            try:
                task_f(*args)
                return True
            except grpc.RpcError as e:
                if e.code() != grpc.StatusCode.UNAVAILABLE:
                    raise e

                retry += 1
                logger.warning(f'Remote Server is unavailable, please check network connection: {e}, attempt: {retry}')
                time.sleep(self.retry_interval)
        return False

    def _put_front(self, task_f, *args):
        with self._queue.not_full:
            self._queue.queue.appendleft((task_f, args))
            self._queue.not_empty.notify()

    def wait_for_finish(self):
        self._queue.join()

    @staticmethod
    def _calculate_size(args):
        size = 0
        assert type(args) is tuple
        for arg in args[0]:
            assert type(arg) is tuple
            assert len(arg) == 2
            size += len(arg[0]) + len(arg[1])
        return size
