"""Defines `Explorer` class.

The Explorer interacts with a graph and defines musical responses."""


class Explorer(object):
    """The `Explorer` class exists on edges of a graph and moves over time."""

    _edge = None
    _a = None
    _b = None
    _speed = None
    _natural_speed = None
    _location = None
    _at_start = False
    _at_end = False
    _BOUNCE = 0
    _EXPLODE = 1
    _RANDOM = 2

    def __init__(self, edge, speed, natural_speed, location=0, end_behavior=_BOUNCE):
        self._edge = edge
        self._a = edge[0]
        self._b = edge[1]
        self._speed = speed
        self._natural_speed = natural_speed
        self._location = location
        self._end_behavior = end_behavior
        if self.location == 0:
            self._at_start = True

    @property
    def node_a(self):
        return self._a

    @property
    def node_b(self):
        return self._b

    @property
    def edge(self):
        return self._edge

    @property
    def speed(self):
        return self._speed

    @property
    def end_behavior(self):
        return self._end_behavior

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
