"""Sends Midi data to bus."""

import mido
import time
import multiprocessing as mp
import os
from dataclasses import dataclass


# TODO: don't hardcode.
_PORT = mido.open_output('virtual_midi Bus 1')


@dataclass
class Note:
    """Keeps track of notes"""
    note: int
    volume: float
    end_time: float = 0
    duration: float = 0


def start_note(note, port=_PORT):
    """Plays note for given amount of time."""
    start_msg = mido.Message('note_on', note=note.note)
    print("sending")
    port.send(start_msg)


def end_note(note, port=_PORT):
    end_msg = mido.Message('note_off', note=note.note)
    port.send(end_msg)


class Squeaker(object):

    _play_notes = []
    _hold_notes = []

    def __init__(self):
        pass

    def play_note(self, note):
        print(f"playing note {note}")
        self._play_notes.append(note)

    def tick(self, t):
        """Performs playing operations based on external clock `t`"""
        h_, e_ = self.check_end_notes(t)

        # End old nodes.
        for n in e_:
            print("ending")
            print(n)
            end_note(n)

        self._hold_notes = h_
        just_queued = []
        # Play new notes.
        for n in self._play_notes:
            print("starting ")
            print(n)
            start_note(n)
            n.end_time = t + n.duration
            self._hold_notes.append(n)
        self._play_notes.clear()

    def check_end_notes(self, t):
        h_ = []
        e_ = []
        for n in self._hold_notes:
            h_.append(n) if n.end_time > t else e_.append(n)

        # Don't end notes that are still in queu. Playing takes priority.
        playing_notes = map(lambda x: x.note, h_)

        for n in e_:
            if n.note in playing_notes:
                e_.remove(n)

        return h_, e_
