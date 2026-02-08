import requests
from src.config.settings import Config
from src.utils.logger import get_logger

# Initialize
Config.validate()
base_url = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2/posts"
auth = (Config.WP_USERNAME, Config.WP_PASSWORD)

def find_posts():
    search_keywords = ["지원금", "정책", "정부", "수당", "복지"]
    found_posts = []

    print(f"🔍 Searching for posts with keywords: {search_keywords}")
    
    # Fetch posts (limit to 50 recent to scan)
    params = {
        "per_page": 50,
        "status": "publish"
    }
    
    try:
        response = requests.get(base_url, auth=auth, params=params)
        posts = response.json()
        
        for post in posts:
            title = post['title']['rendered']
            content = post['content']['rendered']
            # Check if any keyword matches title
            if any(k in title for k in search_keywords):
                found_posts.append({
                    "id": post['id'],
                    "title": title,
                    "link": post['link'],
                    "date": post['date']
                })
        
        if found_posts:
            print(f"✅ Found {len(found_posts)} related posts:")
            for p in found_posts:
                print(f"- [ID: {p['id']}] {p['title']} ({p['date'][:10]})")
        else:
            print("❌ No related posts found in the last 50 published posts.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_posts()
