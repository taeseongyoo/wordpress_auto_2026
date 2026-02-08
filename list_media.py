import requests, json, sys
from src.config.settings import Config

def main():
    Config.validate()
    
    BASE_URL = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2"
    AUTH = (Config.WP_USERNAME, Config.WP_PASSWORD)
    
    # Fetch 50 recent media
    mr = requests.get(f"{BASE_URL}/media", auth=AUTH, params={'per_page': 50})
    if mr.status_code == 200:
        media_pool = mr.json()
        print(f"✅ Loaded {len(media_pool)} media items.")
        
        for m in media_pool:
            print(f"- ID: {m['id']}, Source: {m['source_url']}")
    else:
        print(f"❌ Failed to fetch media: {mr.status_code}")

if __name__ == "__main__":
    main()
