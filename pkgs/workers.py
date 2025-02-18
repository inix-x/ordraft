# fmt: off
import os
import sys
import traceback
import queue
import time

from PyQt6.QtCore import (
    QObject, pyqtSignal, pyqtSlot,
    QWaitCondition, QMutex, QMutexLocker,
)

if __name__ == "__main__" or "pkgs" not in sys.modules:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from pkgs.dataclass import Document

# fmt: on


class BackgroundWorker(QObject):
    finished = pyqtSignal(bool)
    error_occured = pyqtSignal(object)

    def __init__(self, name: str, func, *args, interval: float = 0, **kwargs):
        """
        Args:
            name (str): Name identifier for the worker.
            func (callable): The function to be executed repeatedly.
            *args: Positional arguments for the function.
            interval (float): Interval in seconds between executions. Default is 0 (run continuously).
            **kwargs: Keyword arguments for the function.
        """
        super().__init__()
        self.name = name
        if not callable(func):
            raise ValueError("The provided function is not callable.")

        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._interval = interval

        self._running = True
        # ---- Control for processing tasks ----
        # When _processing_allowed is False, the worker will wait before processing the next task.
        self._processing_allowed = False
        self._mutex = QMutex()
        self._condition = QWaitCondition()

    def run(self):
        """This method runs in a separate thread and processes the given task indefinitely."""
        print(f"\nStarting {self.name}")
        while self._running:
            # print(f"Running {self.name}")
            # with QMutexLocker(self._mutex):
            #     while not self._processing_allowed and self._running:
            #         self._condition.wait(self._mutex)
            #     self._processing_allowed = False

            if not self._running:
                break

            if self._func is None:
                self.error_occured.emit("Received an invalid task (None). Stopping...")
                print("Received an invalid task (None). Stopping...")
                break

            try:
                self._func(*self._args, **self._kwargs)
            except Exception as e:
                self.error_occured.emit((e, f"Error in function '{self.name}'"))

            if self._interval > 0:
                time.sleep(self._interval)

        self.finished.emit(True)

    @pyqtSlot()
    def resume(self):
        """Call this slot to allow processing of the next task."""
        with QMutexLocker(self._mutex):
            self._processing_allowed = True
            self._condition.wakeOne()

    @pyqtSlot()
    def stop(self):
        """Call this slot to stop the background worker."""
        self._running = False
        with QMutexLocker(self._mutex):
            self._processing_allowed = True
            self._condition.wakeOne()


class AgentWorker(QObject):
    status_changed = pyqtSignal(Document)
    finished = pyqtSignal(bool)
    error_occured = pyqtSignal(object)

    def __init__(self):
        super().__init__()

        # Private Data
        self._task_queue = queue.Queue()
        self._running = True

        # ---- Control for processing tasks ----
        # When _processing_allowed is False, the worker will wait before processing the next task.
        self._processing_allowed = False
        self._mutex = QMutex()
        self._condition = QWaitCondition()

    # -----Public API-----
    def add_task(self, func, data: Document):
        """Called to add a new task to the queue."""
        was_empty = self._task_queue.empty()
        self._task_queue.put((func, data))
        if was_empty:
            self._auto_unlock()

    def run(self):
        """This method runs in a separate thread and waits for tasks indefinitely."""
        print("\nAgent 2 Running")
        while self._running:
            self._mutex.lock()
            while not self._processing_allowed and self._running:
                self._condition.wait(self._mutex)

            self._processing_allowed = False
            self._mutex.unlock()
            time.sleep(1)
            try:
                func, task_data = self._task_queue.get(timeout=1)
                if func is None:
                    self.error_occured.emit(
                        "Received an invalid task (None). Skipping..."
                    )
                    continue

            except queue.Empty:
                continue

            func(task_data)
            self._task_queue.task_done()

        print("Agent 2 Stopping")
        self.finished.emit(True)

    @pyqtSlot()
    def allow_next_task(self):
        """Call this slot to allow processing of the next queued task."""
        if self._processing_allowed is False:
            self._mutex.lock()
            self._processing_allowed = True
            self._condition.wakeOne()
            self._mutex.unlock()

    # -----Private API-----
    @pyqtSlot(Document)
    def _handle_events(self, data: Document):
        try:
            self.status_changed.emit(data)
        except Exception as e:
            print(traceback.format_exc())
            self.error_occured.emit((e, traceback.format_exc()))

    @pyqtSlot()
    def _auto_unlock(self):
        """Automatically unlock processing if the queue was empty and a new task is added."""
        self._mutex.lock()
        if not self._processing_allowed:
            self._processing_allowed = True
            self._condition.wakeOne()
        self._mutex.unlock()

    def stop(self):
        """Called to stop the worker loop."""
        self._running = False
        self._mutex.lock()
        self._processing_allowed = True
        self._condition.wakeOne()
        self._mutex.unlock()
