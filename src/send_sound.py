"""Sends Midi data to bus."""

import mido
import time
import multiprocessing as mp
import os


# TODO: don't hardcode.
_PORT = mido.open_output('virtual_midi Bus 1')


def play_note(note, delay, port=_PORT):
    """Plays note for given amount of time."""

    start_msg = mido.Message('note_on', note=note)
    end_msg = mido.Message('note_off', note=note)

    port.send(start_msg)

    # Wait.
    time.sleep(delay)

    port.send(end_msg)


def play_from_queue(queue):
    while True:
        item = queue.get()
        if item is None:
            queue.task_done()
            break
        else:
            n, d = item
        play_note(n, d)
        queue.task_done()
    print(f"closed {os.getpid()}")


class Player(object):
    """Supervises sending midi data."""

    _thread_count = None
    _threadpool = None
    _play_queue = None

    def __init__(self, thread_count=12 * 10):
        self._play_queue = mp.JoinableQueue()
        self._thread_count = thread_count
        self._threadpool = mp.Pool(
            thread_count, play_from_queue, (self._play_queue,))

    def play_notes(self, notes):
        """Adds notes to queue to be played."""
        for n in notes:
            self._play_queue.put(n)

    def wait_until_finished(self):
        for _ in range(self._thread_count):
            self._play_queue.put(None)

        self._threadpool.close()
        print("pool closed")
        self._threadpool.join()
        print("pool joined")

        self._play_queue.close()
        print("closed")
        self._play_queue.join()
        print("joined")
