"""Extract all dependencies from monorepo pyproject.toml files."""
import tomllib
import os
import sys

paths = sys.argv[1:] if len(sys.argv) > 1 else [
    '/packages/ai/pyproject.toml',
    '/packages/database/pyproject.toml',
    '/packages/hermes/pyproject.toml',
    '/packages/integrations/pyproject.toml',
    '/packages/bots/pyproject.toml',
    '/app/apps/api/pyproject.toml',
]

deps = set()
for path in paths:
    if not os.path.exists(path):
        continue
    with open(path, 'rb') as f:
        data = tomllib.load(f)
    for dep in data.get('project', {}).get('dependencies', []):
        clean = dep.strip().strip('"').strip("'")
        if clean:
            deps.add(clean)
    # Dev deps for api package
    if 'api' in path:
        for dep in data.get('project', {}).get('optional-dependencies', {}).get('dev', []):
            clean = dep.strip().strip('"').strip("'")
            if clean:
                deps.add(clean)

with open('/tmp/requirements.txt', 'w') as f:
    f.write('\n'.join(sorted(deps)))

print(f'{len(deps)} dependencies extracted')
