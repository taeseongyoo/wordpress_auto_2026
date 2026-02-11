
import time
import requests
from src.config.settings import Config
from src.core.generator import ContentGenerator
from src.utils.logger import get_logger

# Logger setup
logger = get_logger("AISmartWorkCampaign")

# Configuration
Config.validate()
BASE_URL = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2/posts"
AUTH = (Config.WP_USERNAME, Config.WP_PASSWORD)

def create_post_draft(title, topic, internal_links):
    """Generates content and saves it as a Draft in WordPress."""
    generator = ContentGenerator()
    
    print(f"\n🚀 Starting generation for: {title}")
    post_data = generator.generate_post(topic, internal_links)
    
    if not post_data:
        logger.error(f"❌ Failed to generate content for: {title}")
        return None

    # Tags & Category (Finalized via PROGRESS.md)
    CATEGORY_ID = [86] # AI 스마트워크 & 수익화
    TAG_IDS = [230, 99, 275, 169, 111, 320, 351, 90] # Optimized High-Volume Tags

    # [NEW] Image Generation & Upload Logic
    from src.core.image_processor import ImageProcessor
    from src.core.wp_client import WordPressClient
    import re
    
    img_processor = ImageProcessor()
    wp_client = WordPressClient()
    
    # 1. Generate & Upload Images based on metadata
    images_meta = post_data.get("images", [])
    uploaded_images = {} # {type_idx: media_id}
    
    print(f"🎨 Generating {len(images_meta)} images...")
    
    for idx, img in enumerate(images_meta):
        # Filename safe slug
        safe_slug = post_data["slug"]
        if idx == 0 and img["type"] == "featured":
            fname = f"{safe_slug}-thumb.webp"
        else:
            fname = f"{safe_slug}-body-{idx}.webp"
            
        print(f"   Generating: {fname}...")
        local_path = img_processor.generate_image(img["prompt"], fname)
        
        if local_path:
            # Upload
            media_info = wp_client.upload_image(
                image_path=local_path,
                caption=img["caption"],
                title=img["alt"], # SEO: Title = Alt
                alt_text=img["alt"],
                description=img["prompt"]
            )
            if media_info:
                img["media_id"] = media_info["id"]
                img["source_url"] = media_info["source_url"]
                print(f"   ✅ Uploaded: ID {media_info['id']}")
            else:
                print("   ❌ Upload Failed")
        else:
            print("   ❌ Generation Failed")

    # 2. Insert Images into Content (Simple H2 injection)
    # Re-using logic from repair script
    content = post_data["content"]
    parts = re.split(r'(</h2>)', content)
    new_content = ""
    h2_counter = 0
    
    body_imgs = [img for img in images_meta if img["type"] == "body" and "media_id" in img]
    # Distribute: After H2 #1, #3, #6...
    # Simple mapping: 0->1st H2, 1->3rd H2, 2->6th H2 (approx)
    mappings = {0: 0, 1: 2, 2: 5}
    
    for i in range(0, len(parts)):
        part = parts[i]
        new_content += part
        if part == "</h2>":
            # Check if we need to insert image
            # Find which image maps to this h2_counter
            for img_idx, target_h2 in mappings.items():
                if h2_counter == target_h2 and img_idx < len(body_imgs):
                    img = body_imgs[img_idx]
                    block_html = (
                        f'\n\n<!-- wp:image {{"id":{img["media_id"]},"sizeSlug":"large","linkDestination":"none"}} -->\n'
                        f'<figure class="wp-block-image size-large">'
                        f'<img src="{img["source_url"]}" alt="{img["alt"]}" class="wp-image-{img["media_id"]}"/>'
                        f'<figcaption>{img["caption"]}</figcaption>'
                        f'</figure>\n'
                        f'<!-- /wp:image -->\n\n'
                    )
                    new_content += block_html
            h2_counter += 1
            
    post_data["content"] = new_content
    
    # Featured Image ID
    featured_media_id = 0
    for img in images_meta:
        if img["type"] == "featured" and "media_id" in img:
            featured_media_id = img["media_id"]

    # WordPress Payload
    payload = {
        "title": post_data["title"],
        "content": post_data["content"],
        "status": "draft",
        "slug": post_data["slug"],
        "categories": CATEGORY_ID,
        "tags": TAG_IDS,
        "featured_media": featured_media_id, # Set Featured Image
        "meta": {
            "rank_math_focus_keyword": post_data["rank_math_focus_keyword"],
            "rank_math_description": post_data["rank_math_description"]
        }
    }
    
    try:
        response = requests.post(BASE_URL, auth=AUTH, json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"✅ Draft Saved! [ID: {result['id']}] {result['title']['rendered']}")
        print(f"🔗 Permalink: {result['link']}")
        return {"id": result['id'], "link": result['link'], "title": result['title']['rendered']}
    except Exception as e:
        logger.error(f"❌ Failed to save draft: {e}")
        return None

def fetch_recent_posts(exclude_ids=[]):
    """Fetches recent posts from WP to fill the internal link quota (Target: 5)."""
    try:
        # Fetch 10 recent posts
        url = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2/posts?per_page=10&status=publish" # Only published posts usually, but for dev we might check draft too? Let's stick to published for safety or fetch query.
        # Check published + draft if needed, but linking to drafts is risky if not published soon. 
        # For now, let's assume we want to link to *existing* content.
        r = requests.get(url, auth=AUTH)
        if r.status_code == 200:
            posts = r.json()
            candidates = []
            for p in posts:
                if p['id'] not in exclude_ids:
                     candidates.append({
                        "id": p['id'],
                        "title": p['title']['rendered'],
                        "link": p['link']
                    })
            return candidates
    except Exception as e:
        print(f"⚠️ Failed to fetch recent posts: {e}")
    return []

def run_ai_smartwork_chain():
    # 0. Anchor Post (Existing)
    # [ID: 710] AI 전자책 수익화 2026: 지식 창업 성공 가이드
    ANCHOR_POST = {
        "id": 710,
        "title": "AI 전자책 수익화 2026: 지식 창업 성공 가이드",
        "link": "https://smart-work-solution.com/ai-ebook-monetization-2026/" 
    }
    
    # [Smart Fetch] Get Pool of Links
    recent_posts = fetch_recent_posts(exclude_ids=[710])
    print(f"📚 Fetched {len(recent_posts)} recent posts for linking pool.")
    
    # Helper to mix Mandatory Links + Random Recent Links to hit quota (5)
    def prepare_links(mandatory_links):
        # Start with mandatory
        final_links = mandatory_links.copy()
        current_ids = [l['id'] for l in mandatory_links]
        
        # Fill up to 5
        import random
        random.shuffle(recent_posts)
        for p in recent_posts:
            if len(final_links) >= 5: break
            if p['id'] not in current_ids:
                final_links.append(p)
                current_ids.append(p['id'])
        return final_links

    # Chain Execution Order
    
    # 1. Post 1 (The Hub) -> Links to Anchor
    # [Already Generated: ID 745]
    POST1_INFO = {
        "id": 745,
        "title": "AI 스마트워크로 1인 기업 수익화 시작하는 법: 2026년 필승 가이드",
        "link": "https://smart-work-solution.com/?p=745"
    }
    print(f"\n✅ Post 1 (Hub) Already Exists: {POST1_INFO['link']}")
    
    # 2. Post 2 (The Spoke: Tools) -> Links to Post 1
    # [Already Generated: ID 759]
    POST2_INFO = {
        "id": 759,
        "title": "2026년 1인 기업 필수 AI 자동화 툴 추천 TOP 5: 비용은 줄이고 수익은 늘리는 비법",
        "link": "https://smart-work-solution.com/?p=759"
    }
    print(f"\n✅ Post 2 (Neighbor) Already Exists: {POST2_INFO['link']}")
    
    # 3. Post 3 (The Spoke: Success Stories) -> Links to Post 1 & Post 2
    print("\n--- [Step 3] Generating Post 3 (Topic: AI Success Stories) ---")
    
    # [Smart Link Logic]
    # Mandatory: Hub (Post 1) + Neighbor (Post 2) + Anchor (Post 710)
    # We want at least 5 links.
    mandatory_links = [POST1_INFO, POST2_INFO, ANCHOR_POST]
    final_internal_links = prepare_links(mandatory_links)
    
    print(f"🔗 Internal Links Prepared: {[l['id'] for l in final_internal_links]} (Total: {len(final_internal_links)})")
    
    post3 = create_post_draft(
        title="2026 AI 스마트워크 성공 사례: 1인 기업이 연봉 1억을 달성한 현실적인 방법 (Updated)", # Updated title to distinguish or just overwrite
        topic="AI 스마트워크 성공 사례 수익화",
        internal_links=final_internal_links # Link to Hub, Neighbor, Anchor + Random Recent
    )
    if not post3: return
    
    # End of Chain
    print("\n✨ AI Smart Work Campaign Completed Successfully (Posts 1, 2, 3)!")

if __name__ == "__main__":
    run_ai_smartwork_chain()
