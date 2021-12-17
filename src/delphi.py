"""Test for hops."""


from flask import Flask
import ghhops_server as hs
import threading
import time
import re

import rhino_delphi
import send_sound
import hops_utils

import multiprocessing as mp


import logging
log = logging.getLogger('Hops')
log.disabled = True
log2 = logging.getLogger('werkzeug')
log2.setLevel(logging.ERROR)

# register hops app as middleware
app = Flask(__name__)
hops = hs.Hops(app)

lock = threading.Lock()
event_start = threading.Event()
event_stop = threading.Event()
sn = rhino_delphi.Delphi(None, None)
GLOBAL_SPEED = [1]


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


def delphi_updater(audio_pipe):

    print(f"sn {sn}")

    while True:
        t = time.time()

        # Audio events.
        audio_pipe.send(t)

        if event_start.is_set():
            last_update = t
            while True:
                t = time.time()
                # Audio events.
                audio_pipe.send(t)
                # Update positions every dt.
                dt = t - last_update
                with lock:
                    sn.update(dt * GLOBAL_SPEED[0])
                # Stop updating
                if event_stop.is_set():
                    event_start.clear()
                    event_stop.clear()
                    break

                last_update = t
                # Sleep until next time.
                time.sleep(1/50 - time.time() * 50 % 1 / 50)

        # Sleep until next time.
        time.sleep(1/50 - time.time() * 50 % 1 / 50)


@app.route("/explorer_count")
def test():
    with lock:
        e = len(sn._explorers)
    return e


@hops.component(
    '/delphi_add_mite',
    name="Delphi Add Oracle",
    inputs=[hs.HopsBoolean("Add", "Add", "If `True`, Adds Mite."),
            hs.HopsInteger("Edges", "E", access=hs.HopsParamAccess.TREE),
            hs.HopsNumber("Speed", "Speed", access=hs.HopsParamAccess.TREE),
            hs.HopsInteger("End Behavior", "EB", access=hs.HopsParamAccess.TREE)],
)
def delphi_add_explorer(trigger, edges, speed, end_behavior):
    """Adds explorers to edges specified."""
    edges = hops_utils.list_from_tree(edges)
    speed = hops_utils.list_from_tree(speed)[0]
    end_behavior = hops_utils.list_from_tree(end_behavior)[0]
    if trigger:
        for e, s, eb in zip(edges, speed, end_behavior):
            with lock:
                sn.add_explorer(e, natural_speed=s, end_behavior=eb)


@hops.component(
    "/delphi_update_geometry",
    name="Delphi Update Geometry",
    description="Update Geometry.",
    inputs=[
        hs.HopsBoolean("Trigger", "Trigger", "Updates topology."),
        hs.HopsCurve("Edge Curves", "Edge Curves",
                     access=hs.HopsParamAccess.TREE),
        hs.HopsNumber("Speed", "Speed", access=hs.HopsParamAccess.TREE),
        hs.HopsNumber("Note", "Note", access=hs.HopsParamAccess.TREE),
        hs.HopsNumber("Note Velocity", "Note Velocity",
                      access=hs.HopsParamAccess.TREE),
        hs.HopsNumber("Duration", "Duration",
                      access=hs.HopsParamAccess.TREE)
        ],
    outputs=[]
        )
def delphi_update_geometry(trigger, edge_path, speed, note, note_velocity, duration):
    if trigger:
        edge_path = hops_utils.list_from_tree(edge_path)[0]
        speed = hops_utils.list_from_tree(speed)[0]
        note = hops_utils.list_from_tree(note)[0]
        note = [*map(lambda x: clamp(x, 0, 127), note)]
        note_velocity = hops_utils.list_from_tree(note_velocity)[0]

        duration = hops_utils.list_from_tree(duration)[0]

        if len(speed) == 1:
            speed = speed[0]
        if len(note) == 1:
            note = note[0]
        if len(note_velocity) == 1:
            note_velocity = note_velocity[0]
        if len(duration) == 1:
            duration = duration[0]

        with lock:
            sn.add_node_data(sn.graph.nodes, [note, note_velocity, duration], [
                             "note", "note_velocity", "duration"])

            sn.update_geometry(edge_path)
            sn.add_edge_data(
                sn._init_edges, [speed], ["speed"])


@hops.component(
    "/delphi_setup",
    name="Delphi Setup",
    description="Set up Delphi.",
    inputs=[
        hs.HopsBoolean("Setup", "Setup", "Updates topology."),
        hs.HopsInteger("Nodes", "N", access=hs.HopsParamAccess.TREE),
        hs.HopsInteger("Edges", "E", access=hs.HopsParamAccess.TREE)
        ],
    outputs=[]
        )
def delphi_setup(trigger, nodes, edges):
    if trigger:
        nodes = hops_utils.list_from_tree(nodes)[0]
        edges = hops_utils.list_from_tree(edges)

        # Validate nodes.
        if not all([isinstance(o, int) for o in nodes]):
            raise ValueError("Invalid nodes.")

        with lock:
            sn.set_up(nodes, edges)


@ hops.component(
    "/delphi_state",
    name="Delphi State",
    description="Get state of Delphi",
    inputs=[],
    outputs=[hs.HopsPoint("I", "I", "Status of Delphi.",
                          access=hs.HopsParamAccess.TREE)]
    )
def delphi_state():
    with lock:
        try:
            s = sn.state()
        except Exception:
            s = 0
        return s


@hops.component(
    "/run_delphi",
    name="run_delphi",
    description="Controls Delphi",
    inputs=[
        hs.HopsBoolean("Start", "Start", "If `True`, starts counter."),
        hs.HopsBoolean("Pause", "Pause", "If `True`, starts counter."),
        hs.HopsBoolean("Reset", "Reset", "If `True`, starts counter."),
                hs.HopsNumber("Speed", "Speed",
                              "Controls speed of explorers on graph.")
        ],
    outputs=[]
    )
def run_delphi(start, pause, reset, speed):
    """Controls starting and stopping of delphi."""
    if start:
        event_start.set()
    with lock:
        if speed != GLOBAL_SPEED[0]:
            GLOBAL_SPEED[0] = speed
    if pause:
        event_stop.set()
    if reset:
        with lock:
            sn.reset()
    return None


def run_app():
    app.run(threaded=True)


def audio(audio_pipe):

    sq = send_sound.Squeaker()

    while True:
        t_or_n = audio_pipe.recv()

        # Is a time stamp.
        if isinstance(t_or_n, float):
            sq.tick(t_or_n)

        # Is a note.
        if isinstance(t_or_n, send_sound.Note):
            print(f'received {t_or_n}')
            sq.play_note(t_or_n)


class AudioRouter(object):

    def __init__(self, pipe):
        self.audio_pipe = pipe

    def play_notes(self, notes):
        for n in notes:
            self.audio_pipe.send(n)


def delphi_run(audio_pipe):

    ar = AudioRouter(audio_pipe)
    sn._player = ar

    # Flask.
    first_thread = threading.Thread(target=run_app)

    # Update things.
    second_thread = threading.Thread(
        target=delphi_updater, args=(audio_pipe,))

    first_thread.start()
    second_thread.start()


if __name__ == "__main__":

    parent_conn, child_conn = mp.Pipe()

    p_audio = mp.Process(target=audio, args=(child_conn,))
    p_delphi = mp.Process(target=delphi_run, args=(parent_conn,))

    p_audio.start()
    p_delphi.start()
