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
    print(f"🆔 ID: {data['id']}")
    print(f"🖼️ Featured Media ID: {data.get('featured_media')}")
    
    content = data['content']['rendered']
    img_count = content.count("<img")
    print(f"📝 Content Length: {len(content)}")
    print(f"🖼️ Images in Content: {img_count}")
    
    if img_count == 0:
        print("❌ No images found in content!")
        print("--- Content H2 Tags Search ---")
        h2_matches = re.findall(r'<h2.*?>.*?</h2>', content)
        print(f"Found {len(h2_matches)} H2 tags.")
        for i, h2 in enumerate(h2_matches[:3]):
            print(f"H2[{i}]: {h2}")
            
        print("--- Content Preview (Start) ---")
        print(content[:500])
    else:
        print("✅ Images found in content.")

if __name__ == "__main__":
    inspect(681)
