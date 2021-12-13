"""SoundNetwork for Grasshopper."""

import rhino3dm

import play_geometry

import send_sound

from operator import itemgetter


_FORWARD = 0
_REVERSE = 1


def _feature_dict(key, data):
    """Generates dict with key from `edge` tuple and data as entry."""
    if isinstance(data, float):
        return data
    if isinstance(key[0], list):
        key = [*map(tuple, key)]
    return dict(zip(key, data))


def reverse_edges(edges):
    return [e[::-1] for e in edges]


def map_dict_items(f, my_dictionary):
    return {k: f(v) for k, v in my_dictionary.items()}


class Delphi(play_geometry.SoundNetwork):
    """Adds functionality for interacting with Rhino."""

    def set_up(self, nodes, edges):
        """Sets up G with additional edge/node features for performance."""
        self._init_edges = edges

        self.graph = play_geometry._initialize_graph(
            nodes, edges, digraph=True)

        self.set_new_edge_attribute(False, "edge_played")
        self.set_new_edge_attribute(0, "mite_count")

    def update_geometry(self, edge_curve):
        # Add curves going in each direction.
        edges = self._init_edges

        self.set_new_edge_attribute(
            _feature_dict(edges, edge_curve), 'edge_curve')
        self.set_new_edge_attribute(
            _feature_dict(edges, [_FORWARD] * len(edges)), 'curve_direction')

        reversed_edges = reverse_edges(edges)

        self.set_new_edge_attribute(
            _feature_dict(reversed_edges, edge_curve), 'edge_curve')
        self.set_new_edge_attribute(
            _feature_dict(reversed_edges, [_REVERSE] * len(reversed_edges)), 'curve_direction')

    def add_edge_data(self, edges, edge_data, edge_data_names):
        """Adds data associated with edges."""
        reversed_edges = reverse_edges(edges)

        for ed, name in zip(edge_data, edge_data_names):
            print(f"adding {name}")
            self.set_new_edge_attribute(
                _feature_dict(edges, ed), name)
            self.set_new_edge_attribute(
                _feature_dict(reversed_edges, ed), name)

    def add_node_data(self, nodes, node_data, node_data_names):
        """Adds data associated with nodes."""
        for nd, name in zip(node_data, node_data_names):
            self.set_new_node_attribute(_feature_dict(nodes, nd), name)

    def update_tuner(self, A4=None, scale=None):
        if A4 is not None:
            self.tuner._A4 = A4
        if scale is not None:
            self.tuner._scale = scale

    def edge_speed(self, edge):
        """Computes speed for explorer on edge."""
        return self.graph[edge[0]][edge[1]]["speed"]

    def state(self):
        curv = [itemgetter('edge_curve', 'curve_direction')(
            self.graph.get_edge_data(e.node_a, e.node_b)) + (e.location,) for e in self._explorers]

        pos = [c.PointAt(loc) if r == _FORWARD else c.PointAt(
            1-loc) for c, r, loc in curv]
        return pos

    def reset(self):
        self.remove_all_explorers()
        self.set_new_edge_attribute(False, "edge_played")

    def explorer_at_end(self, e, node):
        """End of path behavior."""
        self.play_node(node)
        self.maybe_make_new_player_at_end(e)
        self.remove_explorer(e)

    def play_node(self, node):
        """Programed node."""
        n = self.graph.nodes[node]
        note = send_sound.Note(
            note=int(n['note']),
            volume=int(n['note_velocity']),
            duration=n['duration']
            )
        self.play_note(note)

    def maybe_make_new_player_at_end(self, e):
        """Determines what (if any) new explorers to produce."""

        # Get possible edges.
        # n, ed, edge_data = self.edge_data(e.node_b)
        # current_edge = (e.node_b, e.node_a)

        current_node = e.node_b
        adjacent_nodes, adjacent_edges, _ = self.edge_data(current_node)

        if e.end_behavior == e._EXPLODE:
            # Explode.
            for a_e in adjacent_edges:
                mc = self.graph[a_e[0]][a_e[1]]["mite_count"] + \
                    self.graph[a_e[1]][a_e[0]]["mite_count"]
                if mc < 1:
                    self.add_explorer(a_e, e._natural_speed,
                                      end_behavior=e._end_behavior)

        # # Bounce.
        if e.end_behavior == e._BOUNCE:
            self.add_explorer((e.node_b, e.node_a),
                              natural_speed=e._natural_speed,  end_behavior=e._end_behavior)
