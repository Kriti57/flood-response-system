"""Find shortest drivable routes for allocated response resources."""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

import networkx as nx

try:
    import osmnx as ox
except ImportError:  # The in-memory routing tests do not require OSMnx.
    ox = None


FLOOD_THRESHOLD = 0.50
DEFAULT_SPEED_KPH = 30.0
GRAPH_PATH = Path(__file__).parent / "data" / "road_network.graphml"


class RoutingError(ValueError):
    """Raised when a requested route cannot be calculated."""


def _validate_coordinate(latitude: float, longitude: float, label: str) -> None:
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise RoutingError(f"{label} latitude must be between -90 and 90.")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise RoutingError(f"{label} longitude must be between -180 and 180.")


def _nearest_node(graph: nx.Graph, latitude: float, longitude: float) -> Any:
    if graph.number_of_nodes() == 0:
        raise RoutingError("The road graph contains no nodes.")

    if ox is not None and graph.graph.get("crs"):
        try:
            return ox.distance.nearest_nodes(graph, X=longitude, Y=latitude)
        except (ImportError, ValueError, nx.NetworkXException):
            pass

    nodes = []
    for node_id, data in graph.nodes(data=True):
        if "x" not in data or "y" not in data:
            raise RoutingError(f"Graph node {node_id!r} is missing x/y coordinates.")
        nodes.append((node_id, float(data["y"]), float(data["x"])))
    if not nodes:
        raise RoutingError("The road graph contains no coordinate-bearing nodes.")
    return min(nodes, key=lambda node: (node[1] - latitude) ** 2 + (node[2] - longitude) ** 2)[0]


def _numeric(value: Any) -> float | None:
    if isinstance(value, (list, tuple)):
        return _numeric(value[0]) if value else None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def _edge_attribute_records(graph: nx.Graph, start: Any, end: Any) -> list[dict[str, Any]]:
    data = graph.get_edge_data(start, end)
    if data is None:
        return []
    if graph.is_multigraph():
        return list(data.values())
    return [data]


def _block_edge(graph: nx.Graph, edge: Iterable[Any]) -> None:
    edge = tuple(edge)
    if len(edge) not in (2, 3):
        raise RoutingError("Each blocked edge must be [start_node, end_node] or [start_node, end_node, key].")
    start, end = edge[:2]
    key = edge[2] if len(edge) == 3 else None
    for source, target in ((start, end), (end, start)):
        if not graph.has_edge(source, target):
            continue
        if graph.is_multigraph():
            if key is not None:
                if graph.has_edge(source, target, key):
                    graph.remove_edge(source, target, key)
            else:
                graph.remove_edges_from((source, target, edge_key) for edge_key in list(graph[source][target]))
        else:
            graph.remove_edge(source, target)


def find_route(
    graph: nx.Graph,
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    resource_id: str = "",
    blocked_edges: Iterable[Iterable[Any]] | None = None,
    default_speed_kph: float = DEFAULT_SPEED_KPH,
) -> dict[str, Any]:
    """Return one schema-compliant route, raising RoutingError if unreachable."""
    try:
        start_lat, start_lng = float(start_lat), float(start_lng)
        end_lat, end_lng = float(end_lat), float(end_lng)
    except (TypeError, ValueError) as exc:
        raise RoutingError("Start and destination coordinates must be numbers.") from exc
    _validate_coordinate(start_lat, start_lng, "Start")
    _validate_coordinate(end_lat, end_lng, "Destination")
    if not math.isfinite(default_speed_kph) or default_speed_kph <= 0:
        raise RoutingError("Default speed must be a positive number of km/h.")

    start_node = _nearest_node(graph, start_lat, start_lng)
    end_node = _nearest_node(graph, end_lat, end_lng)
    route_graph = graph.copy()
    for edge in blocked_edges or ():
        _block_edge(route_graph, edge)

    try:
        node_path = nx.shortest_path(route_graph, start_node, end_node, weight="length", method="dijkstra")
    except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
        raise RoutingError(f"No route exists for {resource_id or 'resource'} after applying blocked roads.") from exc

    distance_m = 0.0
    travel_time_seconds = 0.0
    for start, end in zip(node_path, node_path[1:]):
        edge_records = _edge_attribute_records(route_graph, start, end)
        if not edge_records:
            raise RoutingError(f"Road graph is missing edge data for {start!r} -> {end!r}.")
        selected = min(edge_records, key=lambda item: _numeric(item.get("length")) or 0.0)
        length_m = _numeric(selected.get("length"))
        if length_m is None:
            raise RoutingError(f"Road edge {start!r} -> {end!r} has no valid length.")
        distance_m += length_m

        travel_time = _numeric(selected.get("travel_time"))
        speed_kph = _numeric(selected.get("speed_kph"))
        if travel_time is not None:
            travel_time_seconds += travel_time
        else:
            travel_time_seconds += length_m / ((speed_kph or default_speed_kph) * 1000 / 3600)

    coordinates = []
    for node_id in node_path:
        node_data = graph.nodes[node_id]
        coordinates.append([float(node_data["y"]), float(node_data["x"])])

    return {
        "resource_id": resource_id,
        "route": coordinates,
        "eta_minutes": int(math.ceil(travel_time_seconds / 60)),
    }


def get_blocked_edges_from_flood_data(
    flood_data: Iterable[dict[str, Any]],
    zone_edges: dict[str, list[list[Any]]] | None = None,
    threshold: float = FLOOD_THRESHOLD,
) -> list[list[Any]]:
    """Map flooded zones to supplied graph edges; does not infer geography."""
    if not 0 <= threshold <= 1:
        raise RoutingError("Flood threshold must be between 0 and 1.")
    zone_edges = zone_edges or {}
    blocked = []
    for zone in flood_data:
        try:
            flood_pct = float(zone["flood_pct"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RoutingError("Each flood record must include a numeric flood_pct.") from exc
        if not math.isfinite(flood_pct) or not 0 <= flood_pct <= 1:
            raise RoutingError("Flood percentages must be between 0 and 1.")
        if flood_pct >= threshold:
            blocked.extend(zone_edges.get(str(zone.get("zone_id", "")), []))
    return blocked


def route_assignments(
    graph: nx.Graph,
    assignments: Iterable[dict[str, Any]],
    zone_destinations: dict[str, Any] | None = None,
    blocked_edges: Iterable[Iterable[Any]] | None = None,
    flood_data: Iterable[dict[str, Any]] | None = None,
    zone_edges: dict[str, list[list[Any]]] | None = None,
    flood_threshold: float = FLOOD_THRESHOLD,
    default_speed_kph: float = DEFAULT_SPEED_KPH,
) -> list[dict[str, Any]]:
    """Route Person C assignments to supplied zone destinations."""
    all_blocked_edges = list(blocked_edges or ())
    all_blocked_edges.extend(get_blocked_edges_from_flood_data(flood_data or (), zone_edges, flood_threshold))
    results = []
    for assignment in assignments:
        if not isinstance(assignment, dict):
            raise RoutingError("Each assignment must be a JSON object.")
        resource_id = str(assignment.get("resource_id", ""))
        zone_id = str(assignment.get("assigned_zone", ""))
        destination = zone_destinations.get(zone_id) if zone_destinations else None
        if "destination_lat" in assignment and "destination_lng" in assignment:
            destination_lat = assignment["destination_lat"]
            destination_lng = assignment["destination_lng"]
        elif isinstance(destination, dict):
            destination_lat = destination.get("lat")
            destination_lng = destination.get("lng")
        elif isinstance(destination, (list, tuple)) and len(destination) == 2:
            destination_lat, destination_lng = destination
        else:
            raise RoutingError(f"No destination coordinates supplied for zone {zone_id!r}.")
        if "base_lat" not in assignment or "base_lng" not in assignment:
            raise RoutingError(f"Assignment {resource_id!r} must include base_lat and base_lng.")
        try:
            results.append(
                find_route(
                    graph,
                    assignment["base_lat"],
                    assignment["base_lng"],
                    destination_lat,
                    destination_lng,
                    resource_id=resource_id,
                    blocked_edges=all_blocked_edges,
                    default_speed_kph=default_speed_kph,
                )
            )
        except RoutingError as exc:
            raise RoutingError(f"{resource_id or 'Resource'}: {exc}") from exc
    return results


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(__file__).parent / "sample_input.json")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "sample_output.json")
    parser.add_argument("--graph", type=Path, default=GRAPH_PATH)
    parser.add_argument("--default-speed-kph", type=float, default=DEFAULT_SPEED_KPH)
    args = parser.parse_args()

    try:
        if not args.graph.is_file():
            raise RoutingError(f"Road graph not found at {args.graph}. Run build_graph.py first.")
        if ox is None:
            raise RoutingError("OSMnx is required to load GraphML. Install requirements.txt first.")
        graph = ox.load_graphml(filepath=args.graph)
        input_data = _load_json(args.input)
        if isinstance(input_data, list):
            assignments = input_data
            options = {}
        elif isinstance(input_data, dict):
            assignments = input_data.get("assignments", [])
            options = input_data
        else:
            raise RoutingError("Input JSON must be an assignment list or an object with an assignments list.")
        if not isinstance(assignments, list):
            raise RoutingError("The assignments field must be a JSON list.")
        routes = route_assignments(
            graph,
            assignments,
            options.get("zone_destinations"),
            options.get("blocked_edges"),
            options.get("flood_data"),
            options.get("zone_edges"),
            options.get("flood_threshold", FLOOD_THRESHOLD),
            args.default_speed_kph,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as file:
            json.dump(routes, file, indent=2)
            file.write("\n")
        print(f"Wrote {len(routes)} routes to {args.output}")
    except (OSError, json.JSONDecodeError, RoutingError, nx.NetworkXException) as exc:
        print(f"Routing failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())