import json
from pathlib import Path
from graphify.extract import collect_files, extract

if __name__ == '__main__':
    root = Path('.')
    files = collect_files(root)
    print(f'Files to extract: {len(files)}')

    result = extract(files, cache_root=Path('.'), parallel=False)

    print(f'Nodes: {len(result.get("nodes", []))}')
    print(f'Edges: {len(result.get("edges", []))}')
    print(f'Files processed: {len(result.get("files", []))}')

    with open('graphify-out/graphify_extract.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, default=str)
    print('Written to graphify-out/graphify_extract.json')
