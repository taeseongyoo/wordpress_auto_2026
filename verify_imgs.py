import requests, json, sys, re
from src.config.settings import Config

def main():
    Config.validate()
    print("Config Validated")
    sys.stdout.flush()

    try:
        url = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2/posts/681"
        r = requests.get(url, auth=(Config.WP_USERNAME, Config.WP_PASSWORD))
        print(f"Status Code: {r.status_code}")
        
        data = r.json()
        content = data['content']['rendered']
        print(f"Content Length: {len(content)}")
        
        matches = re.finditer(r'(<img[^>]+>)', content)
        count = 0
        for m in matches:
            count += 1
            print(f"IMG[{count}]: {m.group(1)[:200]}...") # Truncate long URLs
            
        if count == 0:
            print("NO IMAGES FOUND!")
        else:
            print(f"Total Images: {count}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
