import json

def summarize(path):
    clusters = json.load(open(path))
    sizes = [len(v) for v in clusters.values()]
    total = sum(sizes)
    print(f"Soubor: {path}")
    print(f"  Clustrů: {len(sizes)}")
    print(f"  Vzorků celkem: {total}")
    print(f"  Velikost clusteru – min/avg/max: {min(sizes)}/{total/len(sizes):.2f}/{max(sizes)}")
    print(f"  Top 10 clusterů: {sorted(sizes, reverse=True)[:10]}")

summarize("clusters_with_norm.json")
summarize("clusters_without_norm.json")