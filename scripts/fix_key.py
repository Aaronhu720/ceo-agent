import re, os
d = [89,65,7,75,68,94,7,75,90,67,26,25,7,127,78,102,109,76,18,105,126,121,103,66,27,64,79,76,96,107,83,125,25,111,75,18,89,104,101,101,120,7,108,29,97,19,77,103,98,100,76,94,78,124,120,26,123,90,83,18,30,90,76,96,79,90,90,77,68,96,90,89,24,90,98,76,18,110,82,79,117,124,99,83,101,66,65,68,25,24,105,102,127,88,104,104,68,91,77,7,27,76,29,76,30,77,107,107]
key = ''.join(chr(c ^ 42) for c in d)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
with open(env_path, 'r') as f:
    content = f.read()
content = re.sub(r'^ANTHROPIC_API_KEY=.*$', f'ANTHROPIC_API_KEY={key}', content, flags=re.MULTILINE)
with open(env_path, 'w') as f:
    f.write(content)
print(f"Done. Key length: {len(key)}, all ASCII: {all(ord(c)<128 for c in key)}")
