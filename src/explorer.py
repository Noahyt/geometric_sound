"""Defines `Explorer` class.

The Explorer interacts with a graph and defines musical responses."""


class Explorer(object):
    """The `Explorer` class exists on edges of a graph and moves over time."""

    _a = None
    _b = None
    _speed = None
    _location = None
    _at_start = False
    _at_end = False

    def __init__(self, node_a, node_b, speed, location=0):
        self._a = node_a
        self._b = node_b
        self._speed = speed
        self._location = location
        if self.location == 0:
            self._at_start = True

    @property
    def node_a(self):
        return self._a

    @property
    def node_b(self):
        return self._b

    @property
    def speed(self):
        return self._speed

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, loc):
        self._location = loc

    @property
    def at_start(self):
        return self._at_start

    @property
    def at_end(self):
        return self._at_end

    def update_location(self, dt):
        """Updates location of player."""
        if not self._at_end:
            self.location = min(1, self.location + self.speed * dt)

        if self._at_start:
            if self.location != 0:
                self._at_start = False

        if self.location == 1:
            self._at_end = True
