#!/usr/bin/env python3
with open('docker-compose.yml', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_until = None
in_ollama_section = False

for i, line in enumerate(lines):
    # Fix Redis port
    if '- "6379:6379"' in line and i > 30 and i < 50:  # Redis section
        new_lines.append(line.replace('"6379:6379"', '"6381:6379"'))
        continue
    
    # Track Ollama section
    if 'container_name: juris_ia_ollama' in line:
        in_ollama_section = True
    
    # Remove healthcheck from Ollama section
    if in_ollama_section and line.strip().startswith('healthcheck:'):
        skip_until = 'networks:'
        continue
    
    if skip_until and skip_until in line:
        skip_until = None
        in_ollama_section = False
    
    if skip_until:
        continue
    
    new_lines.append(line)

with open('docker-compose.yml', 'w') as f:
    f.writelines(new_lines)

print("Fixed!")
