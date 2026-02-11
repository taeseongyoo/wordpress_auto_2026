
import requests
import re
from src.config.settings import Config
from src.utils.logger import get_logger

logger = get_logger("FixPost2AltText")

def fix_post2_alt_text():
    Config.validate()
    BASE_URL = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2"
    AUTH = (Config.WP_USERNAME, Config.WP_PASSWORD)
    
    POST_ID = 759
    FOCUS_KEYWORD = "AI 자동화" # Manually retrieved from earlier step
    
    print(f"📥 Fetching Post {POST_ID} Content...")
    try:
        r = requests.get(f"{BASE_URL}/posts/{POST_ID}", auth=AUTH)
        r.raise_for_status()
        post_data = r.json()
    except Exception as e:
        logger.error(f"Failed to fetch post: {e}")
        return

    content = post_data['content']['rendered']
    
    # 1. Find all Image IDs in content
    # Pattern: wp-image-(\d+)
    media_ids = re.findall(r'wp-image-(\d+)', content)
    media_ids = list(set(media_ids))
    
    print(f"🔍 Found Media IDs in content: {media_ids}")
    
    # 2. Update Media Alt Text via API
    print("\n🖼 Updating Media Alt Texts...")
    updated_alts = {} # {id: new_alt}
    
    for media_id in media_ids:
        try:
            # Get current media info
            mr = requests.get(f"{BASE_URL}/media/{media_id}", auth=AUTH)
            if mr.status_code != 200: continue
            media_info = mr.json()
            
            original_alt = media_info.get('alt_text', '')
            original_caption = media_info.get('caption', {}).get('raw', '')
            
            # Clean HTML from Alt (Just in case)
            clean_alt = re.sub(r'<[^>]+>', '', original_alt).strip()
            
            # Inject Keyword if missing
            new_alt = clean_alt
            if FOCUS_KEYWORD not in clean_alt:
                new_alt = f"{FOCUS_KEYWORD}: {clean_alt}"
                print(f"   ⚠️ Keyword missing in Media {media_id}. Injecting...")
            else:
                print(f"   ✅ Keyword present in Media {media_id}.")
                
            # Update Media
            update_payload = {
                "alt_text": new_alt,
                "title": new_alt, # Sync title with alt
                "caption": original_caption # Keep caption (or update if needed, but focus is Alt)
            }
            
            # If caption is empty or missing keyword, fix it too (Bonus)
            clean_caption = re.sub(r'<[^>]+>', '', original_caption).strip()
            if FOCUS_KEYWORD not in clean_caption:
                 update_payload["caption"] = f"{FOCUS_KEYWORD} - {clean_caption}"
            
            requests.post(f"{BASE_URL}/media/{media_id}", auth=AUTH, json=update_payload)
            print(f"   💾 Updated Media {media_id} -> '{new_alt}'")
            
            updated_alts[media_id] = new_alt
            
        except Exception as e:
            logger.error(f"Failed to update media {media_id}: {e}")

    # 3. Update Post Content HTML (Alt attributes in <img> tags)
    print("\n📝 Correcting Post Content HTML (Alt Attributes)...")
    new_content = content
    
    for media_id, new_alt in updated_alts.items():
        # Regex to find the img tag for this media_id and replace its alt attribute
        # Target: <img ... class="... wp-image-{media_id} ..." alt="..." ...>
        # This is complex with Regex. 
        # Simpler approach: Replace the specific string knowing the structure or just rely on WP to update? 
        # WP doesn't auto-update embedded HTML when Media changes. We must do it.
        
        # We look for the specific class and then the alt attribute nearby? 
        # Actually, simpler: search for the img tag having this class.
        
        # Pattern: <img [^>]*class="[^"]*wp-image-758[^"]*"[^>]*>
        # Inside that, find alt="[^"]*" and replace.
        
        def replace_alt(match):
            img_tag = match.group(0)
            # Replace alt="..." with alt="new_alt"
            # Be careful about verify logic.
            return re.sub(r'alt="([^"]*)"', f'alt="{new_alt}"', img_tag)
            
        pattern = re.compile(f'<img [^>]*class="[^"]*wp-image-{media_id}[^"]*"[^>]*>')
        new_content = pattern.sub(replace_alt, new_content)

    if new_content != content:
        # Save Post
        print("\n💾 Saving Final Changes to Post...")
        post_update_payload = {
            "content": new_content
        }
        res = requests.post(f"{BASE_URL}/posts/{POST_ID}", auth=AUTH, json=post_update_payload)
        if res.status_code == 200:
            print(f"🎉 Success! Post {POST_ID} Updated.")
            print(f"   Link: {res.json()['link']}")
        else:
            print(f"❌ Failed to update post content: {res.text}")
    else:
        print("   No content changes needed (Alt tags might need manual refresh if regex failed).")

if __name__ == "__main__":
    fix_post2_alt_text()
