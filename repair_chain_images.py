import requests, json, sys, re, time
from src.config.settings import Config

def main():
    Config.validate()
    print("Config Validated")
    
    BASE_URL = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2"
    AUTH = (Config.WP_USERNAME, Config.WP_PASSWORD)
    
    # Posts to Repair
    posts = [
        {"id": 673, "slug": "government-subsidies-types-application-period-2026"}, # Post 1 (Korean keyword title)
        {"id": 675, "slug": "government-funding-business-plan-2026"}, # Post 2 (Korean keyword title)
        {"id": 681, "slug": "government-support-policies-2026"}, # Post 3 (Korean keyword title)
        {"id": 681, "slug": "government-grants-application-2026"} # Wait, Post 1 slug was government-grants-application (from logs). No wait, I should check.
    ]
    
    # Re-verify slugs from logs:
    # Post 1: government-grants-application-2026 (logs step 253)
    # Post 2: government-funding-business-plan-2026 (logs step 292)
    # Post 3: government-support-policies-2026 (logs step 344)
    
    posts = [
        {"id": 673, "slug": "government-grants-application-2026"},
        {"id": 675, "slug": "government-funding-business-plan-2026"},
        {"id": 681, "slug": "government-support-policies-2026"}
    ]

    print("\n📦 Fetching recent media (100 items)...")
    media_pool = []
    # Fetch 100 recent media
    mr = requests.get(f"{BASE_URL}/media", auth=AUTH, params={'per_page': 100})
    if mr.status_code == 200:
        media_pool = mr.json()
        print(f"✅ Loaded {len(media_pool)} media items.")
    else:
        print(f"❌ Failed to fetch media: {mr.status_code}")
        return

    for p in posts:
        pid = p['id']
        slug = p['slug']
        
        print(f"\n🔧 Repairing Post {pid} (Slug: {slug})...")
        
        # 1. Fetch Post Content
        try:
            r = requests.get(f"{BASE_URL}/posts/{pid}", auth=AUTH)
            if r.status_code != 200:
                print(f"❌ Failed to fetch Post {pid}: {r.status_code}")
                continue
            
            post_data = r.json()
            original_content = post_data['content']['rendered']
            
            # Strip existing figures/imgs/wp attributes
            clean_content = re.sub(r'<figure.*?</figure>', '', original_content, flags=re.DOTALL)
            clean_content = re.sub(r'<img.*?>', '', clean_content)
            clean_content = re.sub(r'<!-- wp:image.*?-->', '', clean_content, flags=re.DOTALL)
            clean_content = re.sub(r'<!-- /wp:image -->', '', clean_content)
            
            # Clean empty lines
            clean_content = re.sub(r'\n\s*\n', '\n\n', clean_content)
            
            # 2. Find Media in Pool
            body_imgs = {}
            found_count = 0
            
            # Expected filenames: SLUG_body_1, 2, 3
            targets = {
                1: f"{slug}_body_1",
                2: f"{slug}_body_2", 
                3: f"{slug}_body_3"
            }
            
            for m in media_pool:
                src = m['source_url']
                fname = src.split('/')[-1]
                
                for idx, target in targets.items():
                    if target in fname:
                        body_imgs[idx] = m
                        found_count += 1
            
            print(f"✅ Found {found_count} Body Images for {slug}.")
            
            if found_count == 0:
                print("⚠️ No images found! Searching deeper? No, skipping.")
                # Maybe fallback to keyword search if slug mismatch?
                # But logs confirm filenames use slug.
                continue

            # 3. Insert Images (Gutenberg Format)
            parts = re.split(r'(</h2>)', clean_content)
            final_content = ""
            img_idx = 1
            
            for part in parts:
                final_content += part
                if part == "</h2>":
                    if img_idx in body_imgs:
                        m = body_imgs[img_idx]
                        src = m['source_url']
                        alt = m['alt_text']
                        caption = m['caption']['rendered']
                        mid = m['id']
                        
                        block_html = (
                            f'\n<!-- wp:image {{"id":{mid},"sizeSlug":"large","linkDestination":"none"}} -->\n'
                            f'<figure class="wp-block-image size-large">'
                            f'<img src="{src}" alt="{alt}" class="wp-image-{mid}"/>'
                            f'<figcaption>{caption}</figcaption>'
                            f'</figure>\n'
                            f'<!-- /wp:image -->\n'
                        )
                        final_content += block_html
                        print(f"   -> Inserted Image {img_idx} (ID: {mid})")
                        img_idx += 1
            
            # 4. Update Post
            ur = requests.post(f"{BASE_URL}/posts/{pid}", auth=AUTH, json={'content': final_content})
            if ur.status_code == 200:
                print(f"🎉 Post {pid} Updated Successfully!")
            else:
                print(f"❌ Update Failed: {ur.status_code}")
                print(ur.text[:200])

        except Exception as e:
            print(f"❌ Error repairing post {pid}: {e}")

if __name__ == "__main__":
    main()
