#The script loads a driving network from OpenStreetMap (using osmnx), sets each edge’s travel time as its 
#weight (length / maxspeed), runs a Dijkstra shortest-path search (using heapq) between two randomly chosen nodes, 
#styles edges/nodes for visualization while the algorithm runs, reconstructs the found path, increments an 
#edge usage counter (dijkstra_uses) for the path, and finally draws a graph visualization showing visited/active/path 
#edges. The graph object G is a global osmnx MultiDiGraph.

"""A* shortest-path runner.

This module can be executed independently (python A_star.py) and does not
require importing or running Dijkstra.
"""


import osmnx as ox
import random
import heapq
import numpy as np
import math

import numpy as np
import osmnx as ox

from utils import (
    compute_travel_time_weights,
    create_nodes_pair,
    get_global_max_speed,
    style_active_edge,
    style_unvisited_edge,
    style_visited_edge,
    reset_graph,
)

NUM_RUNS = 10
PLACES = {
    "Aosta": "Aosta, Aosta, Italy",
    "Turin": "Turin, Piedmont, Italy",
}


def h_Manhattan(G, destination, neighbor):
    return abs(G.nodes[destination]["x"] - G.nodes[neighbor]["x"]) + abs(
        G.nodes[destination]["y"] - G.nodes[neighbor]["y"]
    )


def h_Euclidean(G, destination, neighbor):
    dx = G.nodes[destination]["x"] - G.nodes[neighbor]["x"]
    dy = G.nodes[destination]["y"] - G.nodes[neighbor]["y"]
    return math.sqrt(dx**2 + dy**2)


def h_Haversine(G, destination, neighbor):
    phi_1 = math.radians(G.nodes[destination]["y"])
    lambda_1 = math.radians(G.nodes[destination]["x"])
    phi_2 = math.radians(G.nodes[neighbor]["y"])
    lambda_2 = math.radians(G.nodes[neighbor]["x"])

    delta_phi = phi_1 - phi_2
    delta_lambda = lambda_1 - lambda_2
    a_value = (math.sin(delta_phi / 2) ** 2) + (
        math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2) ** 2
    )
    c_value = 2 * math.atan2(math.sqrt(a_value), math.sqrt(1 - a_value))
    earth_radius_m = 6371 * 1000
    return earth_radius_m * c_value


HEURISTICS = {
    "manhattan": h_Manhattan,
    "euclidean": h_Euclidean,
    "haversine": h_Haversine,
}


def initialize_search_state(graph, origin, destination):
    for node in graph.nodes:
        graph.nodes[node]["visited"] = False
        graph.nodes[node]["distance"] = float("inf")
        graph.nodes[node]["previous"] = None
        graph.nodes[node]["size"] = 0

    for edge in graph.edges:
        style_unvisited_edge(graph, edge)

    graph.nodes[origin]["distance"] = 0
    graph.nodes[origin]["size"] = 50
    graph.nodes[destination]["size"] = 50


def a_star(G, origin, destination, h_function, max_speed=1, plot=False):
    reset_graph(G)
    initialize_search_state(G, origin, destination)

    priority_queue = [(0, origin)]
    iterations = 0
    while priority_queue:
        _, node = heapq.heappop(priority_queue)

        if node == destination:
            print("Iterations:", iterations)
            return iterations

        if G.nodes[node]["visited"]:
            continue

        G.nodes[node]["visited"] = True
        for edge in G.out_edges(node):
            style_visited_edge(G, (edge[0], edge[1], 0))
            neighbor = edge[1]
            weight = G.edges[(edge[0], edge[1], 0)]["weight"]

            candidate_distance = G.nodes[node]["distance"] + weight
            if G.nodes[neighbor]["distance"] > candidate_distance:
                G.nodes[neighbor]["distance"] = candidate_distance
                G.nodes[neighbor]["previous"] = node
                heuristic_value = h_function(G, neighbor, destination) / max_speed
                priority = candidate_distance + heuristic_value
                heapq.heappush(priority_queue, (priority, neighbor))

                for outgoing_edge in G.out_edges(neighbor):
                    style_active_edge(G, (outgoing_edge[0], outgoing_edge[1], 0))

        iterations += 1

    return None


def a_star_multiple(G, pairs, h_function, max_speed):
    print("Running A*")
    print("Nodes:", len(G.nodes))
    print("Edges:", len(G.edges))

    iteration_counts = np.empty(len(pairs))
    for i, (start, end) in enumerate(pairs):
        iteration_counts[i] = a_star(G, start, end, h_function, max_speed=max_speed)

    return np.mean(iteration_counts)


def run_city_benchmark(city_name, place_query, num_pairs):
    print(f"Loading {city_name}...")
    base_graph = ox.graph_from_place(place_query, network_type="drive")
    compute_travel_time_weights(base_graph)
    node_pairs = create_nodes_pair(base_graph, num_pairs)
    max_speed = get_global_max_speed(base_graph)

    projected_graph = ox.project_graph(base_graph)
    compute_travel_time_weights(projected_graph)

    for heuristic_name, heuristic in HEURISTICS.items():
        print(f"\n  Heuristic: A* [{heuristic_name}]")
        graph_for_heuristic = projected_graph if heuristic_name in {"manhattan", "euclidean"} else base_graph
        average_iterations = a_star_multiple(
            graph_for_heuristic,
            node_pairs,
            heuristic,
            max_speed,
        )
        print(f"Average iterations for {city_name} [{heuristic_name}]: {average_iterations:.2f}")


def main():
    print(f"Running A* standalone on {NUM_RUNS} random node pairs per city")
    for city_name, place_query in PLACES.items():
        run_city_benchmark(city_name, place_query, NUM_RUNS)


if __name__ == "__main__":
    main()