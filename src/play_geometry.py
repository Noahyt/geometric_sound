"""Play music based on graph.

Contains functions to coordinate the various aspects of graph-based music
generation."""


import networkx as nx
import numpy as np

import send_sound
import explorer


class Graph(object):

    def __init__(
        self,
        nodes: np.ndarray,
        edges,
        positions=None,
        displacement=None,
    ):
        """
        Class constructor.
        Args:
            nodes: List of nodes.
            edge: List of edges with shape `[edge_count]`
        """
        self.G = self._initialize_graph(nodes, edges)
        self.positions = positions

        if self.positions is not None:
            self.add_length()

    def _initialize_graph(self, nodes, edges):
        G = nx.Graph()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        return G

    @property
    def positions(self):
        return self._positions

    @positions.setter
    def positions(self, positions):
        self._positions = positions

    def add_length(self):
        add_length(self.G, self.positions)

    def edge_data(self, node):
        adjacent_nodes = [*self.G[node]]
        adjacent_edges = [[node, n] for n in adjacent_nodes]
        adjacent_data = [self.G[node][n] for n in adjacent_nodes]
        return adjacent_nodes, adjacent_edges, adjacent_data


def _add_edge_feature_to_graph(graph, feature, name):
    """Utility to add `feature` as list to edges in `network`."""
    # Convert `feature` to a dict.
    f = dict(zip(list(graph.edges), feature))
    nx.set_edge_attributes(graph, f, name=name)


def _edge_list(graph):
    """Utility to get edges as a list of lists."""
    return [list(a) for a in list(graph.edges)]


def _edge_length(graph, positions):
    """Utility to compute edge lengths in network."""
    edges = np.array(_edge_list(graph))
    Ra = positions[edges[:, 0]]
    Rb = positions[edges[:, 1]]
    return np.linalg.norm(Ra - Rb, axis=-1)


def add_length(graph, positions, name="length"):
    """Adds `length` attribute to network.

    Computes length between nodes using euclidean norm."""
    length = _edge_length(graph, positions)
    _add_edge_feature_to_graph(graph, length, name=name)


class SoundNetwork(object):
    """Coordinates sound generation using `Players` on a graph.

    Each time step consists of a sequence of actions:

    1. Update Explorer locations.
    2. Perform operations associated with Explorers.
    3. Generate sound.

    Note that we process all sound events at the end of the time step to ensure that they are played by the `Player` as synchronized as possible."""

    _graph = None
    _explorers = None
    _play_queue = None
    _player = None

    def __init__(self, graph, **audio_kwargs):
        self._graph = graph
        self._explorers = []
        self._play_queue = []
        self.initialize_audio(**audio_kwargs)
        self.set_up(self)

    def initialize_audio(self, **audio_kwargs):
        self._player = send_sound.Player(**audio_kwargs)

    def set_up(self):
        pass

    @property
    def graph(self):
        return self._graph

    def end(self):
        self._player.wait_until_finished()

    def remove_all_explorers(self):
        """Removes all explorers from graph."""
        self._explorers = []

    def add_explorer(self, node_a, node_b, speed):
        e = explorer.Explorer(node_a, node_b, speed)
        self._explorers.append(e)

    def play_note(self, note):
        self._play_queue.append(note)

    def play_sounds(self):
        """Plays sounds in queue."""
        self._player.play_notes(self._play_queue)

        # Clear `play_queue` and wait for next time step.
        self._play_queue = []

    def update(self, dt):
        # Update locations of players.
        self.update_explorers(dt)

        # Perform position-specific operations on players.
        self.operate_explorers()

        # Trigger audio operations.
        self.play_sounds()

    def update_explorers(self, dt):
        """Updates locations of explorers."""
        [e.update_location(dt) for e in self._explorers]

    def remove_explorer(self, e):
        self._explorers.remove(e)

    def operate_explorers(self):
        """Defines operation of `Explorer` based on location."""
        for e in self._explorers:
            if e.at_start:
                self.explorer_at_start(e, e.node_a)
            if e.at_end:
                self.explorer_at_end(e, e.node_b)

    def explorer_at_start(self, e, node):
        """Defines behavior when explorer is at start node."""

    def explorer_at_end(self, e, node):
        """Defines behavior when explorer is at end node."""

    def play_node(self, node):
        """Defines behaviour for playing node."""

    def initialize_new_explorers(self, node):
        """Defines procedure for generating new explorers."""
