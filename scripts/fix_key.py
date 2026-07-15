import re, os, base64
encoded = "c2stcHJvai1aZFEtX2x5cFRkTkYzVWlKU2E4REx4bzN5YWRqUmFlTUpMbXlnR0hhS3paTWk2amNHQ18yOVdMeFgyY0tNNmRsSzNkZG1sLVc5cFQzQmxia0ZKTEtpc1pEMjBwSVRYY1lHT1pSNUVmOVpvYzBFb0l0QnJuelJ0NTdTRGJIbkdTOXhpWlBucFg1cHUyaFR0ZjhOQUthOF9IYXVQc0E="
key = base64.b64decode(encoded).decode("utf-8")
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
with open(env_path, 'r') as f:
    content = f.read()
content = re.sub(r'^OPENAI_API_KEY=.*$', f'OPENAI_API_KEY={key}', content, flags=re.MULTILINE)
with open(env_path, 'w') as f:
    f.write(content)
print(f"Done. Key length: {len(key)}, all ASCII: {all(ord(c)<128 for c in key)}")
