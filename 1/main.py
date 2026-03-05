import osmnx as ox
import os
import json

from utils import (
    create_nodes_pair, 
    compute_travel_time_weights, 
    get_global_max_speed,
)
from Dijkstra import dijkstra
from A_star import a_star, h_Euclidean, h_Haversine, h_Manhattan

NUM_RUNS = 10   # number of random node pairs per city

PLACES = {
    "Aosta": "Aosta, Aosta, Italy",
    #"Turin": "Turin, Piedmont, Italy",
}

HEURISTICS = {
    "manhattan": h_Manhattan,
    "euclidean": h_Euclidean,
    "haversine": h_Haversine,
}


def summarize_iterations(run_outcomes):
    successful_runs = [run for run in run_outcomes if run["iterations"] is not None]
    average_iterations = (
        sum(run["iterations"] for run in successful_runs) / len(successful_runs)
        if successful_runs
        else 0
    )
    iterations_per_run = [run["iterations"] for run in run_outcomes]
    print(f"\n    Steps per run : {iterations_per_run}")
    print(f"    Average steps : {average_iterations:.1f}")
    return round(average_iterations, 2)


def run_algorithm_over_pairs(algorithm_fn, graph, pairs, num_runs, *args, **kwargs):
    run_results = []
    for i, (start, end) in enumerate(pairs[:num_runs], 1):
        steps = algorithm_fn(graph, start, end, *args, **kwargs)
        if steps is None:
            print(f"    Run {i:2d}/{num_runs} | WARNING: no path found for this pair")
            run_results.append({"iterations": None, "distance_km": None})
            continue
        run_results.append({"iterations": steps})
    return run_results


def main():
    all_results = {}
    for city_name, place_query in PLACES.items():
        print(f"\n{'=' * 55}")
        print(f"  CITY  : {city_name}")
        print(f"  Query : {place_query}")
        print(f"  Loading graph...")
        G = ox.graph_from_place(place_query, network_type="drive")

        all_results[city_name] = {
            "nodes": len(G.nodes),
            "edges": len(G.edges),
            "results": {},
        }

        compute_travel_time_weights(G)

        pairs = create_nodes_pair(G, NUM_RUNS)
        os.makedirs("results", exist_ok=True)

        pairs_fp = f"results/pairs_{city_name}.json"
        with open(pairs_fp, "w") as f:
            json.dump(pairs, f, indent=2)

        max_speed = get_global_max_speed(G)
        print(f"  Graph : {len(G.nodes):,} nodes, {len(G.edges):,} edges")
        print(f"  Using {len(pairs)} fixed pairs from Dijkstra run")

        G_original = G.copy()   
        G_projected = ox.project_graph(G)   # Needed for A* Haversine

        run_results = run_algorithm_over_pairs(
            dijkstra,
            G,
            pairs,
            NUM_RUNS,
        )
        avg = summarize_iterations(run_results)

        all_results[city_name]["results"]["dijkstra"] = {
            "runs": run_results,
            "average": avg,
        }

        for h_name, h_func in HEURISTICS.items():
            print(f"\n  {'─'*49}")
            print(f"  Heuristic : A* [{h_name}]")
            print(f"  {'─'*49}")

            if h_name in ["euclidean", "manhattan"]:
                G = G_projected  # use projected graph for these heuristics
            elif h_name == "haversine":
                G = G_original

            run_results = run_algorithm_over_pairs(
                a_star,
                G,
                pairs,
                NUM_RUNS,
                h_func,
                max_speed=max_speed,
            )
            avg = summarize_iterations(run_results)

            all_results[city_name]["results"][f"astar_{h_name}"] = {
                "runs": run_results,
                "average": avg,
            }

        results_fp = "results/results.json"
        with open(results_fp, "w") as f:
            json.dump(all_results, f, indent=2)

    print(f"\n  Results saved : {results_fp}")

if __name__ == "__main__":
    main()