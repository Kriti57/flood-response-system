"""Offline tests for routing behavior; no OSM download is required."""

import json
import unittest

import networkx as nx

from route import RoutingError, find_route, get_blocked_edges_from_flood_data, route_assignments


def make_graph(include_alternate: bool = True) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    graph.add_node("start", x=85.0, y=27.0)
    graph.add_node("middle", x=85.01, y=27.0)
    graph.add_node("end", x=85.02, y=27.0)
    graph.add_node("detour", x=85.01, y=27.01)
    graph.add_edge("start", "middle", length=1000, speed_kph=30)
    graph.add_edge("middle", "end", length=1000, speed_kph=30)
    if include_alternate:
        graph.add_edge("start", "detour", length=1500, speed_kph=30)
        graph.add_edge("detour", "end", length=1500, speed_kph=30)
    graph.graph["crs"] = "EPSG:4326"
    return graph


class RouteTests(unittest.TestCase):
    def test_shortest_route_uses_road_distance_and_schema(self) -> None:
        graph = make_graph()
        result = find_route(graph, 27.0, 85.0, 27.0, 85.02, "Team-1")
        self.assertEqual(result["route"], [[27.0, 85.0], [27.0, 85.01], [27.0, 85.02]])
        self.assertEqual(result["resource_id"], "Team-1")
        self.assertEqual(result["eta_minutes"], 4)
        self.assertEqual(set(result), {"resource_id", "route", "eta_minutes"})
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_blocked_edge_uses_alternate_and_preserves_graph(self) -> None:
        graph = make_graph()
        result = find_route(graph, 27.0, 85.0, 27.0, 85.02, blocked_edges=[["start", "middle"]])
        self.assertEqual(result["route"], [[27.0, 85.0], [27.01, 85.01], [27.0, 85.02]])
        self.assertTrue(graph.has_edge("start", "middle"))

    def test_unreachable_route_returns_clear_error(self) -> None:
        graph = make_graph(include_alternate=False)
        with self.assertRaisesRegex(RoutingError, "No route exists"):
            find_route(graph, 27.0, 85.0, 27.0, 85.02, blocked_edges=[["start", "middle"]])

    def test_invalid_coordinates_are_rejected(self) -> None:
        with self.assertRaisesRegex(RoutingError, "latitude"):
            find_route(make_graph(), 95, 85, 27.0, 85.02)

    def test_flood_threshold_maps_only_supplied_edges(self) -> None:
        flood_data = [{"zone_id": "Z1", "flood_pct": 0.75}, {"zone_id": "Z2", "flood_pct": 0.2}]
        edges = get_blocked_edges_from_flood_data(flood_data, {"Z1": [["a", "b"]], "Z2": [["c", "d"]]})
        self.assertEqual(edges, [["a", "b"]])

    def test_assignment_routes_to_zone_destination(self) -> None:
        assignments = [{
            "resource_id": "Team-2",
            "assigned_zone": "Z1",
            "base_lat": 27.0,
            "base_lng": 85.0,
        }]
        results = route_assignments(make_graph(), assignments, {"Z1": {"lat": 27.0, "lng": 85.02}})
        self.assertEqual(results[0]["resource_id"], "Team-2")
        self.assertEqual(results[0]["route"][-1], [27.0, 85.02])

    def test_out_of_range_flood_percentage_is_rejected(self) -> None:
        with self.assertRaisesRegex(RoutingError, "between 0 and 1"):
            get_blocked_edges_from_flood_data([{"zone_id": "Z1", "flood_pct": 1.2}])


if __name__ == "__main__":
    unittest.main()