
import re
import requests
from src.config.settings import Config
from src.core.wp_client import WordPressClient
from src.utils.logger import get_logger

# Logger
logger = get_logger("FixPostDetails")

def main():
    Config.validate()
    
    # Initialize Client
    wp_client = WordPressClient() # Using our wrapper for easier tag handling
    
    BASE_URL = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2"
    AUTH = (Config.WP_USERNAME, Config.WP_PASSWORD)
    POST_ID = 745
    FOCUS_KEYWORD = "AI 스마트워크"
    TARGET_CATEGORY_ID = 86 # AI 스마트워크 & 수익화

    print(f"🔧 Starting Comprehensive Fix for Post {POST_ID}...")

    # ==============================================================================
    # 1. Prepare Tags (8 Items)
    # ==============================================================================
    print("\n🏷 Preparing Tags...")
    tag_names = [
        "AI 스마트워크",
        "1인 기업 수익화",
        "업무 자동화",
        "2026년 비즈니스 트렌드",
        "챗GPT 활용법",
        "디지털 노마드",
        "시간 관리",
        "생산성 향상"
    ]
    
    # Get/Create Tag IDs
    tag_ids = wp_client.get_or_create_tags(tag_names)
    print(f"✅ Resolved {len(tag_ids)} Tag IDs: {tag_ids}")

    # ==============================================================================
    # 2. Fetch Post Content (for Alt Text Fix)
    # ==============================================================================
    print("\n📥 Fetching Post Content...")
    r = requests.get(f"{BASE_URL}/posts/{POST_ID}", auth=AUTH)
    if r.status_code != 200:
        print("❌ Failed to fetch post.")
        return
    
    post = r.json()
    content = post['content']['rendered']
    
    # Find Image IDs
    image_ids = re.findall(r'wp-image-(\d+)', content)
    # Maintain order, unique-ify
    ordered_ids = []
    seen = set()
    for m in re.finditer(r'wp-image-(\d+)', content):
        img_id = m.group(1)
        if img_id not in seen:
            ordered_ids.append(img_id)
            seen.add(img_id)
            
    print(f"🔍 Found Image IDs in content: {ordered_ids}")

    # ==============================================================================
    # 3. Update Media Metadata (Alt Text)
    # ==============================================================================
    print("\n🖼 Updating Media Alt Texts...")
    
    new_alts_map = {}
    
    def update_media(media_id, alt_text):
        if not media_id: return
        try:
            url = f"{BASE_URL}/media/{media_id}"
            # Only updating Alt Text and Title to be SEO friendly
            data = {
                "alt_text": alt_text,
                "title": alt_text
            }
            res = requests.post(url, auth=AUTH, json=data)
            if res.status_code == 200:
                print(f"   ✅ Media {media_id} updated: {alt_text}")
                new_alts_map[str(media_id)] = alt_text
            else:
                print(f"   ❌ Failed to update Media {media_id}")
        except Exception as e:
            print(f"   ❌ Error updating Media {media_id}: {e}")

    # 3.1 Featured Image
    featured_id = post.get('featured_media')
    if featured_id and featured_id != 0:
        feat_alt = f"{FOCUS_KEYWORD} 1인 기업 수익화 가이드 - 2026년 대표 이미지"
        update_media(featured_id, feat_alt)

    # 3.2 Body Images
    body_alt_templates = [
        f"{FOCUS_KEYWORD}의 핵심 개념과 업무 효율성 혁신",
        f"{FOCUS_KEYWORD}를 통한 1인 기업 수익 자동화 구조도",
        f"{FOCUS_KEYWORD}가 가져올 2026년 미래형 업무 환경"
    ]
    
    for idx, img_id in enumerate(ordered_ids):
        if idx < len(body_alt_templates):
            new_alt = body_alt_templates[idx]
        else:
            new_alt = f"{FOCUS_KEYWORD} 관련 설명 이미지 {idx+1}"
        update_media(img_id, new_alt)

    # ==============================================================================
    # 4. Correct Post Content HTML (Alt Attributes)
    # ==============================================================================
    print("\n📝 Correcting Post Content HTML (Alt Attributes)...")
    new_content = content
    
    for img_id, new_alt in new_alts_map.items():
        # Replace ONLY the alt attribute within the img tag of this ID
        # Regex: Look for <img ... wp-image-{img_id} ...>
        # And replace its alt="..." part OR add it.
        
        # Strategy: Match the whole <img> tag, clean it, rebuild it
        # This is complex with Regex. 
        # Simpler Strategy for this specific HTML mess:
        # The user's screenshot showed `alt="<span class=..."`
        # We can look for `wp-image-{img_id}` and then replace the `alt` attribute nearby?
        # No, let's use the replacement function that acts on the whole tag.
        
        pattern = re.compile(f'(<img [^>]*wp-image-{img_id}[^>]*>)')
        
        def replacer(match):
            tag = match.group(1)
            # 1. Remove any existing alt="..." (greedy or non-greedy depending on quotes)
            # Handle standard double quotes
            tag_clean = re.sub(r'alt="[^"]*"', '', tag)
            # Handle potential single quotes (less common in WP but possible)
            tag_clean = re.sub(r"alt='[^']*'", '', tag_clean)
            
            # 2. Insert new alt right after <img 
            return tag_clean.replace('<img ', f'<img alt="{new_alt}" ')
        
        new_content = pattern.sub(replacer, new_content)

    # ==============================================================================
    # 5. Push Final Update (Content + Category + Tags)
    # ==============================================================================
    print("\n💾 saving Final Changes to Post...")
    
    update_payload = {
        "categories": [TARGET_CATEGORY_ID],  # Set to [86] (AI Smart Work)
        "tags": tag_ids,                     # Set 8 Tags
        "content": new_content               # Updated HTML
    }
    
    res = requests.post(f"{BASE_URL}/posts/{POST_ID}", auth=AUTH, json=update_payload)
    
    if res.status_code == 200:
        r_json = res.json()
        print(f"🎉 Success! Post Updated.")
        print(f"   category: {r_json['categories']} (Expected: [86])")
        print(f"   Tags: {len(r_json['tags'])} items (Expected: 8)")
        print(f"   Link: {r_json['link']}")
    else:
        print(f"❌ Update Failed: {res.status_code}")
        print(res.text[:200])

if __name__ == "__main__":
    main()
