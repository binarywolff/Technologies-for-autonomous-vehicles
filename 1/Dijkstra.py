#The script loads a driving network from OpenStreetMap (using osmnx), sets each edge’s travel time as its 
#weight (length / maxspeed), runs a Dijkstra shortest-path search (using heapq) between two randomly chosen nodes, 
#styles edges/nodes for visualization while the algorithm runs, reconstructs the found path, increments an 
#edge usage counter (dijkstra_uses) for the path, and finally draws a graph visualization showing visited/active/path 
#edges. The graph object G is a global osmnx MultiDiGraph.

"""Dijkstra shortest-path runner.

This module can be executed independently (python Dijkstra.py) and does not
require importing or running A*.
"""
import osmnx as ox
import heapq
import numpy as np

from utils import (
    style_unvisited_edge,
    style_visited_edge,
    style_active_edge,
    create_nodes_pair,
    compute_travel_time_weights,
    reset_graph,
)

NUM_RUNS = 10
PLACES = {
    "Aosta": "Aosta, Aosta, Italy",
    "Turin": "Turin, Piedmont, Italy",
}


def initialize_search_state(G, origin, destination):
    for node in G.nodes:
        G.nodes[node]["visited"] = False
        G.nodes[node]["distance"] = float("inf")
        G.nodes[node]["previous"] = None
        G.nodes[node]["size"] = 0

    for edge in G.edges:
        style_unvisited_edge(G, edge)

    G.nodes[origin]["distance"] = 0
    G.nodes[origin]["size"] = 50
    G.nodes[destination]["size"] = 50


def dijkstra(G, origin, destination):
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
            if G.nodes[neighbor]["distance"] > G.nodes[node]["distance"] + weight:
                G.nodes[neighbor]["distance"] = G.nodes[node]["distance"] + weight
                G.nodes[neighbor]["previous"] = node
                heapq.heappush(priority_queue, (G.nodes[neighbor]["distance"], neighbor))
                for edge2 in G.out_edges(neighbor):
                    style_active_edge(G, (edge2[0], edge2[1], 0))
        iterations += 1

    return None


def dijkstra_multiple(G, pairs):
    compute_travel_time_weights(G)
    print("Running Dijkstra")
    print("Nodes:", len(G.nodes))
    print("Edges:", len(G.edges))

    iteration_counts = np.empty(len(pairs))
    for i, (start, end) in enumerate(pairs):
        iteration_counts[i] = dijkstra(G, start, end)

    return np.mean(iteration_counts)


def run_city_benchmark(city_name, place_query, num_pairs):
    print(f"Loading {city_name}...")
    graph = ox.graph_from_place(place_query, network_type="drive")
    node_pairs = create_nodes_pair(graph, num_pairs)
    average_steps = dijkstra_multiple(graph, node_pairs)
    print(f"Average iterations for {city_name}: {average_steps:.2f}")


def main():
    print(f"Running Dijkstra on {NUM_RUNS} random node pairs per city")
    for city_name, place_query in PLACES.items():
        run_city_benchmark(city_name, place_query, NUM_RUNS)

if __name__ == "__main__":
    main()