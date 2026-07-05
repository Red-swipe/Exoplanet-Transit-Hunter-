import json, os, sys
from pathlib import Path
from graphify.build import build
from graphify.cluster import cluster, score_all, cohesion_score
from graphify.analyze import god_nodes, surprising_connections
from graphify.export import to_json, to_html
from graphify.report import generate

root = Path('.')
out_dir = Path('graphify-out')
out_dir.mkdir(parents=True, exist_ok=True)

# Load extraction
with open(out_dir / 'graphify_extract.json') as f:
    ext = json.load(f)

# Step 4: Build + Cluster + Score
print('Building graph...')
G = build([ext], root=root)
print(f'  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')

print('Clustering...')
communities = cluster(G, resolution=1.0)
print(f'  Found {len(communities)} communities')

print('Scoring communities...')
cs = score_all(G, communities)

# Step 4b: Analysis
print('Analyzing...')
gods = god_nodes(G, top_n=15)
surprises = surprising_connections(G, communities, top_n=10)
print(f'  God nodes: {len(gods)}')
print(f'  Surprising connections: {len(surprises)}')

# Step 5: Label communities
# No LLM backend available, use heuristic labeling
print('Labelling communities (heuristic)...')
community_labels = {}
for cid, nodes in communities.items():
    prefixes = {}
    for node_id in nodes:
        parts = node_id.split('/')
        if len(parts) >= 2:
            prefix = parts[0]
        else:
            prefix = node_id.split(':')[0] if ':' in node_id else node_id
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
    if prefixes:
        best = max(prefixes, key=prefixes.get)
        community_labels[cid] = f'{best} ({len(nodes)} nodes)'
    else:
        community_labels[cid] = f'Community {cid}'

# Step 6: Export
print('Exporting...')
to_json(G, communities, str(out_dir / 'graph.json'), community_labels=community_labels, force=True)
to_html(G, communities, str(out_dir / 'graph.html'), community_labels=community_labels)

# Step 7: Generate report
print('Generating report...')
token_cost = {'input_tokens': ext.get('input_tokens', 0), 'output_tokens': ext.get('output_tokens', 0)}
report_md = generate(
    G, communities, cs, community_labels, gods, surprises,
    detection_result={'total_files': 27, 'total_words': 18700},
    token_cost=token_cost,
    root=str(root.resolve()),
    suggested_questions=None
)
with open(out_dir / 'graphify_report.md', 'w', encoding='utf-8') as f:
    f.write(report_md)

print('Done!')
print(f'  graph.json: {out_dir / "graph.json"}')
print(f'  graph.html: {out_dir / "graph.html"}')
print(f'  graphify_report.md: {out_dir / "graphify_report.md"}')
