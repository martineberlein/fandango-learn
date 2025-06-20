from typing import List
from queue import Queue
from threading import Thread
import os
import signal
from multiprocessing import Process, Queue as ProcessQueue, Manager

from fdlearn.logger import LOGGER
from fdlearn.learning.candidate import FandangoConstraintCandidate
from .generator import Generator


class Engine:

    def __init__(
        self,
        generator: Generator,
        workers: int = 10,
    ):
        self.generator = generator
        self.workers = [generator for _ in range(workers)]
        self._check_generator_compatability()

    def _check_generator_compatability(self):
        pass

    def generate(self, candidates: List[FandangoConstraintCandidate]):
        pass


class SingleEngine(Engine):

    def generate(self, candidates: List[FandangoConstraintCandidate]):
        """
        Generate new inputs for the given candidates.
        :param List[Candidate] candidates: The candidates to generate new inputs for.
        :return:
        """
        test_inputs = set()
        for candidate in candidates:
            test_inputs.update(self.generator.generate_test_inputs(candidate=candidate))
        return test_inputs


class ParallelEngine(Engine):

    def generate(self, candidates: List[FandangoConstraintCandidate]):
        """
        Generate new inputs for the given candidates in parallel.
        :param List[Candidate] candidates: The candidates to generate new inputs for.
        :return:
        """

        LOGGER.debug("Generating inputs in parallel...")
        LOGGER.debug(
            f"Number of workers: {len(self.workers)} Number of candidates: {len(candidates)}"
        )

        threads = []
        candidate_queue = Queue()
        output_queue = Queue()
        for candidate in candidates:
            candidate_queue.put(candidate)
        for worker in self.workers:
            thread = Thread(
                target=worker.run_with_engine, args=(candidate_queue, output_queue)
            )
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()  # 10 seconds max
            if thread.is_alive():
                LOGGER.warning("Process took too long. Terminating...")

        test_inputs = set()
        while not output_queue.empty():
            test_inputs.update(output_queue.get())

        return test_inputs


class ProcessBasedParallelEngine(Engine):
    def generate(self, candidates: List[FandangoConstraintCandidate]):
        """
        Generate new inputs for the given candidates in parallel using multiprocessing.
        Includes per-process timeout and forced termination if needed.
        """
        LOGGER.debug("Generating inputs using multiprocessing with timeout control.")
        processes = []
        candidate_queue = ProcessQueue()
        manager = Manager()
        output_list = manager.list()  # Shared list across processes

        for candidate in candidates:
            candidate_queue.put(candidate)

        # Start one process per worker
        for worker in self.workers:
            p = Process(
                target=worker.run_with_engine, args=(candidate_queue, output_list)
            )
            p.start()
            processes.append(p)

        # Monitor and enforce timeout per process
        for p in processes:
            p.join(timeout=1)
            if p.is_alive():
                LOGGER.warning(f"Process {p.pid} exceeded time limit. Terminating.")
                os.kill(p.pid, signal.SIGKILL)
                p.join()

        # Aggregate all test inputs
        test_inputs = set()
        for output in output_list:
            test_inputs.update(output)

        return test_inputs
