import random

import osmnx as ox


def style_unvisited_edge(graph, edge):
    graph.edges[edge]["color"] = "gray"
    graph.edges[edge]["alpha"] = 1
    graph.edges[edge]["linewidth"] = 0.2


def style_visited_edge(graph, edge):
    graph.edges[edge]["color"] = "green"
    graph.edges[edge]["alpha"] = 1
    graph.edges[edge]["linewidth"] = 1


def style_active_edge(graph, edge):
    graph.edges[edge]["color"] = "red"
    graph.edges[edge]["alpha"] = 1
    graph.edges[edge]["linewidth"] = 1


def style_path_edge(graph, edge):
    graph.edges[edge]["color"] = "white"
    graph.edges[edge]["alpha"] = 1
    graph.edges[edge]["linewidth"] = 5


def plot_graph(graph):
    ox.plot_graph(
        graph,
        node_size=[graph.nodes[node]["size"] for node in graph.nodes],
        edge_color=[graph.edges[edge]["color"] for edge in graph.edges],
        edge_alpha=[graph.edges[edge]["alpha"] for edge in graph.edges],
        edge_linewidth=[graph.edges[edge]["linewidth"] for edge in graph.edges],
        node_color="white",
        bgcolor="black",
    )

def reset_graph(G):
    """Resets node attributes to ensure a clean slate for search algorithms."""
    for node in G.nodes:
        G.nodes[node]["visited"] = False
        G.nodes[node]["distance"] = float("inf")
        G.nodes[node]["previous"] = None
        G.nodes[node]["size"] = 0  # Useful if you are plotting node sizes


def reconstruct_path(graph, orig, dest, plot=False, algorithm=None):
    for edge in graph.edges:
        style_unvisited_edge(graph, edge)

    total_distance_m = 0
    current_node = dest
    while current_node != orig:
        previous_node = graph.nodes[current_node]["previous"]
        if previous_node is None:
            return None

        edge = (previous_node, current_node, 0)
        total_distance_m += graph.edges[edge]["length"]
        style_path_edge(graph, edge)

        if algorithm:
            usage_key = f"{algorithm}_uses"
            graph.edges[edge][usage_key] = graph.edges[edge].get(usage_key, 0) + 1

        current_node = previous_node

    return total_distance_m / 1000


def _parse_maxspeed_kmh(raw_maxspeed, default_kmh=40):
    if isinstance(raw_maxspeed, list):
        parsed_speeds = [_parse_maxspeed_kmh(item, default_kmh=1) for item in raw_maxspeed]
        return min(parsed_speeds) if parsed_speeds else default_kmh

    if isinstance(raw_maxspeed, str):
        token = raw_maxspeed.split()[0].strip().lower()
        if token == "walk":
            return 1
        if token.isdigit():
            return int(token)
        return default_kmh

    if isinstance(raw_maxspeed, (int, float)) and raw_maxspeed > 0:
        return float(raw_maxspeed)

    return float(default_kmh)


def compute_travel_time_weights(graph):
    for u, v, k in graph.edges(keys=True):
        edge = (u, v, k)
        maxspeed_kmh = _parse_maxspeed_kmh(graph.edges[edge].get("maxspeed", 40))
        maxspeed_ms = maxspeed_kmh / 3.6

        graph.edges[edge]["maxspeed_kmh"] = maxspeed_kmh
        graph.edges[edge]["weight"] = graph.edges[edge]["length"] / maxspeed_ms


def clean_graph(graph):
    compute_travel_time_weights(graph)
    for edge in graph.edges:
        graph.edges[edge]["dijkstra_uses"] = 0


def create_nodes_pair(graph, n_pairs):
    node_ids = list(graph.nodes)
    return [[random.choice(node_ids), random.choice(node_ids)] for _ in range(n_pairs)]


def get_global_max_speed(graph):
    max_speed_kmh = 1.0
    for _, _, data in graph.edges(data=True):
        current_edge_speed = _parse_maxspeed_kmh(data.get("maxspeed", 1), default_kmh=1)
        if current_edge_speed > max_speed_kmh:
            max_speed_kmh = current_edge_speed

    return max_speed_kmh / 3.6
