"""Download and save a drivable OpenStreetMap graph for a place."""

import argparse
import sys
from pathlib import Path


CITY = "Trishuli, Nuwakot, Nepal"
DEFAULT_OUTPUT = Path(__file__).parent / "data" / "road_network.graphml"
DEFAULT_SPEED_KPH = 30
DEFAULT_DISTANCE_METERS = 5000


def build_graph(
    city: str,
    output_path: Path,
    make_plot: bool = False,
    distance_meters: int = DEFAULT_DISTANCE_METERS,
) -> None:
    if not city or not city.strip():
        raise ValueError("City must not be empty.")

    try:
        import osmnx as ox
    except ImportError as exc:
        raise RuntimeError(
            "OSMnx is not installed. Install dependencies with "
            "'python -m pip install -r requirements.txt'."
        ) from exc

    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if distance_meters <= 0:
        raise ValueError("Download radius must be a positive number of meters.")

    graph = ox.graph_from_address(
        city.strip(),
        dist=distance_meters,
        network_type="drive",
        simplify=True,
    )
    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        raise RuntimeError(f"OpenStreetMap returned an empty road graph for {city!r}.")

    graph = ox.routing.add_edge_speeds(graph, fallback=DEFAULT_SPEED_KPH)
    graph = ox.routing.add_edge_travel_times(graph)
    ox.save_graphml(graph, filepath=output_path)

    print(f"City: {city.strip()}")
    print(f"Nodes: {graph.number_of_nodes()}")
    print(f"Edges: {graph.number_of_edges()}")
    print(f"Download radius: {distance_meters} m")
    print(f"Output: {output_path}")

    if make_plot:
        try:
            ox.plot_graph(graph, show=True, close=True)
        except Exception as exc:
            print(f"Graph saved, but visualization failed: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", default=CITY, help=f"Place to download (default: {CITY})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="GraphML output path")
    parser.add_argument(
        "--distance-meters",
        type=int,
        default=DEFAULT_DISTANCE_METERS,
        help=f"Download radius around the place center (default: {DEFAULT_DISTANCE_METERS})",
    )
    parser.add_argument("--plot", action="store_true", help="Show an optional graph plot")
    args = parser.parse_args()

    try:
        build_graph(args.city, args.output, args.plot, args.distance_meters)
    except Exception as exc:
        print(f"Could not build road graph: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())