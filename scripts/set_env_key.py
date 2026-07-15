"""Set OPENAI_API_KEY in .env file. Run: python scripts/set_env_key.py <key>"""
import sys
import re
import os

if len(sys.argv) < 2:
    print("Usage: python scripts/set_env_key.py <api_key>")
    sys.exit(1)

key = sys.argv[1].strip()
clean_key = ''.join(c for c in key if ord(c) < 128)

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

content = re.sub(r'^OPENAI_API_KEY=.*$', f'OPENAI_API_KEY={clean_key}', content, flags=re.MULTILINE)

with open(env_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Key set successfully (length: {len(clean_key)}, all ASCII: {all(ord(c)<128 for c in clean_key)})")
