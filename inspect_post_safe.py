import requests
import json
import re
from src.config.settings import Config

Config.validate()
BASE_URL = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2/posts"
AUTH = (Config.WP_USERNAME, Config.WP_PASSWORD)

def inspect(post_id):
    print(f"🔍 Inspecting Post {post_id}...")
    r = requests.get(f"{BASE_URL}/{post_id}", auth=AUTH)
    if r.status_code != 200:
        print(f"❌ Failed: {r.status_code}")
        return
    
    data = r.json()
    content = data['content']['rendered']
    
    # Find all img tags
    img_matches = re.findall(r'<img.*?>', content)
    print(f"🖼️ Found {len(img_matches)} images:")
    for img in img_matches:
        print(f" - {img}")
        
    # Check if figure is wrapped
    figure_matches = re.findall(r'<figure.*?>.*?</figure>', content, re.DOTALL)
    print(f"🖼️ Found {len(figure_matches)} figures:")
    for fig in figure_matches:
        print(f" - {fig[:100]}...") # truncated

if __name__ == "__main__":
    inspect(681)
