
import re
import requests
from src.config.settings import Config
from src.utils.logger import get_logger

# Logger
logger = get_logger("FixAltText")

def main():
    Config.validate()
    
    BASE_URL = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2"
    AUTH = (Config.WP_USERNAME, Config.WP_PASSWORD)
    POST_ID = 745
    FOCUS_KEYWORD = "AI 스마트워크"

    print(f"🔧 Starting Alt Text Fix for Post {POST_ID}...")

    # 1. Fetch Post Content
    r = requests.get(f"{BASE_URL}/posts/{POST_ID}", auth=AUTH)
    if r.status_code != 200:
        print("❌ Failed to fetch post.")
        return
    
    post = r.json()
    content = post['content']['rendered']
    
    # 2. Extract Image IDs from content
    # Look for wp-image-{id} class or data-id
    # Also find current alt usage to debug
    
    # Regex to find image blocks and extract ID and current ALT
    # Pattern: <img ... class="... wp-image-(\d+) ..." ... alt="(.*?)" ...>
    # Note: Attributes order varies.
    
    # Simpler approach: Find all image IDs first
    image_ids = re.findall(r'wp-image-(\d+)', content)
    unique_ids = sorted(list(set(image_ids)))
    
    print(f"🔍 Found Image IDs in content: {unique_ids}")
    
    # Define New Alt Texts (Order matters? No, we map by ID if possible, but we don't know which ID is which position easily without parsing order)
    # Let's parse order of appearance
    
    # Re-find IDs in order of appearance
    ordered_ids = []
    for m in re.finditer(r'wp-image-(\d+)', content):
        ordered_ids.append(m.group(1))
        
    print(f"🔍 Ordered Image IDs: {ordered_ids}")
    
    # Mapping Strategy
    # We have 3 body images in content. Plus maybe Featured Image (not in content body usually, but handled separately).
    # The user screenshot shows Body images have the issue.
    # We will update ALL images found in the post content + the Featured Media.
    
    new_alts_map = {}
    
    # Helper to update media
    def update_media_alt(media_id, new_alt):
        if not media_id: return
        try:
            url = f"{BASE_URL}/media/{media_id}"
            data = {
                "alt_text": new_alt,
                "title": new_alt, # Sync title too
                "caption": new_alt # Sync caption too? Maybe keep caption different. User complained about Alt.
                # Let's keep caption as is (it was manually set nicely before), only fix Alt and Title.
            }
            # Actually, user screenshot shows 'Caption' field might be ok, but 'Alt Text' is broken.
            # We will strictly fix Alt Text.
            
            res = requests.post(url, auth=AUTH, json={"alt_text": new_alt})
            if res.status_code == 200:
                print(f"   ✅ Media {media_id} updated: {new_alt}")
            else:
                print(f"   ❌ Failed to update Media {media_id}")
        except Exception as e:
            print(f"   ❌ Error updating Media {media_id}: {e}")

    # 3. Fix Featured Image
    featured_id = post.get('featured_media')
    if featured_id and featured_id != 0:
        feat_alt = f"{FOCUS_KEYWORD} 1인 기업 수익화 가이드 - 2026년 대표 이미지"
        print(f"\n🖼 Processing Featured Image {featured_id}...")
        update_media_alt(featured_id, feat_alt)
        new_alts_map[str(featured_id)] = feat_alt

    # 4. Fix Body Images
    # We assume the order is: Body 1, Body 2, Body 3
    body_alt_templates = [
        f"{FOCUS_KEYWORD}의 핵심 개념과 업무 효율성",
        f"{FOCUS_KEYWORD}를 통한 수익 자동화 구조도",
        f"{FOCUS_KEYWORD}가 가져올 2026년 미래 업무 환경"
    ]
    
    print(f"\n🖼 Processing Body Images ({len(ordered_ids)} found)...")
    
    for idx, img_id in enumerate(ordered_ids):
        if idx < len(body_alt_templates):
            new_alt = body_alt_templates[idx]
        else:
            new_alt = f"{FOCUS_KEYWORD} 관련 설명 이미지 {idx+1}"
            
        update_media_alt(img_id, new_alt)
        new_alts_map[str(img_id)] = new_alt
        
    # 5. Fix Post Content HTML
    # We need to replace `alt="..."` attributes in the content for these images.
    # The current alt tags likely contain messy HTML escaped chars.
    
    print("\n📝 Correcting Post Content HTML...")
    new_content = content
    
    for img_id, new_alt in new_alts_map.items():
        # Regex to match the img tag for this specific ID and replace its alt
        # <img ... wp-image-{img_id} ... alt="OLD_ALT" ...>
        # This is tricky because attributes order.
        # Safer: Find the whole tag, modify it, put it back.
        
        # Pattern: <img [^>]*wp-image-{img_id}[^>]*>
        pattern = re.compile(f'(<img [^>]*wp-image-{img_id}[^>]*>)')
        
        def replacer(match):
            tag = match.group(1)
            # Check if alt exists
            if 'alt="' in tag:
                # Replace alt content
                # Be careful with quotes. WP usually uses double quotes.
                new_tag = re.sub(r'alt="[^"]*"', f'alt="{new_alt}"', tag)
                return new_tag
            else:
                # Add alt
                return tag.replace('<img ', f'<img alt="{new_alt}" ')
                
        new_content = pattern.sub(replacer, new_content)

    # 6. Push Update to Post
    if new_content != content:
        res = requests.post(f"{BASE_URL}/posts/{POST_ID}", auth=AUTH, json={"content": new_content})
        if res.status_code == 200:
             print("✨ Post Content HTML Updated Successfully!")
        else:
             print("❌ Failed to update Post Content.")
    else:
        print("⚠️ No changes detected in content HTML.")

if __name__ == "__main__":
    main()
