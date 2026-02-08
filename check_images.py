import requests, json, sys, re
from src.config.settings import Config

def main():
    Config.validate()
    print("Config Validated")
    sys.stdout.flush()

    # The 3 posts:
    posts = [673, 675, 681]
    
    for pid in posts:
        try:
            url = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2/posts/{pid}"
            r = requests.get(url, auth=(Config.WP_USERNAME, Config.WP_PASSWORD))
            print(f"Post {pid} Status: {r.status_code}")
            
            data = r.json()
            content = data['content']['rendered']
            print(f"Content Length: {len(content)}")
            
            matches = re.findall(r'<img[^>]+>', content)
            print(f"Image Tags Found: {len(matches)}")
            
            for m in matches:
                print(f" - {m[:100]}...") # Truncated
            
            # Check figure tags
            figs = re.findall(r'<figure[^>]*>', content)
            print(f"Figure Tags Found: {len(figs)}")
            
            # Check wp-image class
            wp_imgs = re.findall(r'wp-image-(\d+)', content)
            print(f"WP Image IDs in content: {wp_imgs}")
            
            print("-" * 20)
            
        except Exception as e:
            print(f"Post {pid} Error: {e}")

if __name__ == "__main__":
    main()
