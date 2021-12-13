"""Testing flask with `Hops` for Grasshopper."""

import flask
from flask import request
import threading
import time

app = flask.Flask(__name__)


class Sonic(object):
    """General Purpose class to run geometric sound.

    Implements multiple processes to """


lock = threading.Lock()
event_start = threading.Event()
event_stop = threading.Event()
i = [0]


def increment(inx):
    """Test incrementer."""
    while True:
        if event_start.is_set():
            event_start.clear()
            while True:
                with lock:
                    print(inx)
                    inx[0] = inx[0]+1
                    time.sleep(2)
                # Stop updating
                if event_stop.is_set():
                    i[0] = 0
                    event_stop.clear()
                    break
        time.sleep(1)
        print('waiting')


def read_number(inx):
    with lock:
        return inx[0]


@app.route("/test")
def test():
    return f"{read_number(i)}"


def start_counter():
    """Starts counter."""
    print("start")
    event_start.set()


def stop_counter():
    """Stops counter."""
    print("stop")
    event_stop.set()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        if "start" in request.form:
            start_counter()
        if "stop" in request.form:
            stop_counter()
    return flask.render_template('index.html')


def run_app():
    app.run(threaded=True)


if __name__ == "__main__":
    t1 = threading.Thread(target=run_app)
    t2 = threading.Thread(target=increment, args=(i,))
    t1.start()
    t2.start()
