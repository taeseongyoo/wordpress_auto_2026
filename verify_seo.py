import os
import requests
from dotenv import load_dotenv

load_dotenv()

WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

POST_ID = 844

def verify_post(post_id):
    url = f"{WP_URL.rstrip('/')}/wp-json/wp/v2/posts/{post_id}"
    response = requests.get(url, auth=(WP_USERNAME, WP_PASSWORD))
    if response.status_code != 200:
        print(f"Failed to fetch: {response.status_code}")
        return

    data = response.json()
    title = data['title']['rendered']
    content = data['content']['rendered']
    meta = data.get('meta', {})
    
    print(f"--- POST {post_id} ---")
    print(f"Title: {title}")
    print(f"Status: {data['status']}")
    print(f"Categories: {data['categories']}")
    print(f"Tags: {data['tags']}")
    
    # rank_math_focus_keyword
    focus_kw = meta.get('rank_math_focus_keyword')
    print(f"Rank Math Focus Keyword: {focus_kw}")
    
    # Check if keyword is in title
    if focus_kw and focus_kw in title:
        print("✅ Keyword in Title")
    else:
        print("❌ Keyword NOT in Title")

    # Check content length
    print(f"Content Length: {len(content)} characters")
    if len(content) > 2000:
        print("✅ Content length is sufficient")
    else:
        print("❌ Content length is too short")
        
    # Check external links to ensure no 404s snuck in
    import re
    links = re.findall(r'<a.*?href="(https?://[^"]+)".*?>(.*?)</a>', content)
    print(f"\nFound {len(links)} links in content:")
    for link, text in links:
        print(f" - [{text}]({link})")
        
    print(f"\nMeta Keys: {list(meta.keys())}")

if __name__ == '__main__':
    verify_post(POST_ID)
