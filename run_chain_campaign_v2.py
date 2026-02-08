import time
import requests
import re
from src.config.settings import Config
from src.core.generator import ContentGenerator
from src.core.image_processor import ImageProcessor
from src.core.wp_client import WordPressClient
from src.utils.logger import get_logger

# Logger setup
logger = get_logger("ChainCampaignV2")

# Configuration
Config.validate()
BASE_URL = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2/posts"
AUTH = (Config.WP_USERNAME, Config.WP_PASSWORD)

def process_images_for_post(post_data, wp_client, image_processor):
    """Generates and uploads images for a post."""
    images_data = post_data.get("images", [])
    if not images_data:
        # Fallback to prompt list if old structure
        raw_prompts = post_data.get("image_prompts", [])
        for idx, p in enumerate(raw_prompts):
            images_data.append({
                "type": "featured" if idx == 0 else "body",
                "prompt": p,
                "alt": f"{post_data.get('rank_math_focus_keyword', 'image')} {idx}",
                "caption": f"Image {idx}"
            })
            
    featured_media_id = None
    body_image_htmls = []
    
    logger.info(f"🎨 Generating {len(images_data)} images for '{post_data['title']}'...")
    
    slug = post_data.get("slug", "post")
    
    for idx, img_meta in enumerate(images_data):
        prompt_raw = img_meta.get("prompt", "")
        prompt_clean = re.sub(r"^(썸네일용|본문이미지\d+):\s*", "", prompt_raw)
        
        file_suffix = "thumb" if idx == 0 else f"body_{idx}"
        file_name = f"{slug}_{file_suffix}.webp"
        
        image_path = image_processor.generate_image(prompt_clean, file_name)
        
        if image_path:
            upload_result = wp_client.upload_image(
                image_path,
                title=post_data['title'] if idx == 0 else f"{post_data.get('rank_math_focus_keyword', 'image')}_{idx}",
                caption=img_meta.get("caption", ""),
                alt_text=img_meta.get("alt", ""),
                description=post_data.get("rank_math_description", "") if idx == 0 else ""
            )
            
            if upload_result:
                if idx == 0:
                    featured_media_id = upload_result['id']
                    logger.info(f"✅ Thumbnail ID: {featured_media_id}")
                else:
                    img_html = (
                        f'\n<figure class="wp-block-image size-large">'
                        f'<img src="{upload_result["source_url"]}" alt="{img_meta.get("alt", "")}" class="wp-image-body-{idx}"/>'
                        f'<figcaption>{img_meta.get("caption", "")}</figcaption>'
                        f'</figure>\n'
                    )
                    body_image_htmls.append(img_html)
                    logger.info(f"✅ Body Image {idx} Uploaded")
        else:
            logger.error(f"❌ Image Generation Failed: {prompt_clean[:20]}...")

    return featured_media_id, body_image_htmls

def insert_body_images(content, body_image_htmls):
    """Inserts body images after H2 tags."""
    if not body_image_htmls: return content
    
    # Clean old placeholders
    cleanup_patterns = [r"\[이미지 설명.*?\]", r"그림 \d+.*?\n", r"\*\*이미지 설명:\*\*.*?\n"]
    for pattern in cleanup_patterns:
        content = re.sub(pattern, "", content, flags=re.IGNORECASE)

    h2_split = re.split(r'(</h2>)', content)
    new_content = ""
    img_idx = 0
    
    for part in h2_split:
        new_content += part
        if part == "</h2>" and img_idx < len(body_image_htmls):
            new_content += body_image_htmls[img_idx]
            img_idx += 1
            
    return new_content

def verify_score_draft(post_id):
    """
    Checks the Rank Math score of a draft post.
    Since we cannot get the computed score via API easily without premium or specific endpoint,
    we will simulate the check based on our `verify_post.py` logic:
    - Length > 2000 chars?
    - H2 count > 4?
    - Focus Keyword present in Title & Content?
    - Meta Description present?
    - Images present?
    """
    logger.info(f"🕵️ Verifying Draft [ID: {post_id}]...")
    try:
        r = requests.get(f"{BASE_URL}/{post_id}", auth=AUTH)
        if r.status_code != 200: return False
        
        post = r.json()
        content = post['content']['rendered']
        title = post['title']['rendered']
        meta = post.get("meta", {})
        fk = meta.get("rank_math_focus_keyword", "")
        
        score_checks = []
        
        # 1. Content Length
        text_len = len(re.sub('<[^<]+?>', '', content))
        score_checks.append(text_len >= 2000)
        logger.info(f"   - Length: {text_len} chars ({'PASS' if text_len>=2000 else 'FAIL'})")
        
        # 2. H2 Count
        h2_count = len(re.findall(r'<h2', content))
        score_checks.append(h2_count >= 4)
        logger.info(f"   - H2 Count: {h2_count} ({'PASS' if h2_count>=4 else 'FAIL'})")
        
        # 3. Focus Keyword
        kw_in_title = fk in title
        kw_in_content = content.count(fk) > 0
        score_checks.append(bool(fk) and kw_in_title and kw_in_content)
        logger.info(f"   - Keyword '{fk}': Title={kw_in_title}, Content={kw_in_content} ({'PASS' if score_checks[-1] else 'FAIL'})")
        
        # 4. Images
        has_thumbnail = post.get("featured_media", 0) > 0
        has_body_images = "<img" in content
        score_checks.append(has_thumbnail and has_body_images)
        logger.info(f"   - Images: Thumb={has_thumbnail}, Body={has_body_images} ({'PASS' if score_checks[-1] else 'FAIL'})")

        if all(score_checks):
            logger.info("🟢 GREEN LIGHT! Post Quality Verification Passed.")
            return True
        else:
            logger.warning("🔴 RED LIGHT! Post Quality Verification Failed.")
            return False

    except Exception as e:
        logger.error(f"Verification Error: {e}")
        return False

def run_chain_v2():
    wp_client = WordPressClient()
    generator = ContentGenerator()
    image_processor = ImageProcessor()

    # Anchor (Existing)
    # ANCHOR_POST = ... (Not used in recovery mode directly)
    
    # --- [RECOVERY MODE] ---
    print("\n🔄 Recovery Mode: Skipping Post 1 & 2 (Already Created)...")
    
    # Post 2 ID (From previous run log/user notification: 675)
    post2_id = 675
    
    try:
        # Fetch Post 2 Info for internal linking
        print(f"🕵️ Fetching Post 2 Info [ID: {post2_id}]...")
        r = requests.get(f"{BASE_URL}/{post2_id}", auth=AUTH)
        if r.status_code != 200:
            print(f"❌ Failed to fetch Post 2. Status: {r.status_code}")
            return
            
        p2 = r.json()
        post2_info = {
            "id": p2['id'],
            "title": p2['title']['rendered'],
            "link": p2['link']
        }
        print(f"✅ Found Post 2: {post2_info['title']}")
        print(f"🔗 Link: {post2_info['link']}")
        
    except Exception as e:
        print(f"❌ Error fetching Post 2: {e}")
        return

    # --- [Execution Phase: Generate Post 3] ---
    print("\n🚀 Resuming Chain: Generating Post 3...")
    
    # Post 3 -> Links to Post 2
    topic3 = "2026년 바뀌는 정부 지원 정책: 놓치면 손해 보는 3가지"
    p3_data = generator.generate_post(topic3, internal_links=[post2_info])
    
    if p3_data:
        fid3, b_imgs3 = process_images_for_post(p3_data, wp_client, image_processor)
        p3_data["content"] = insert_body_images(p3_data["content"], b_imgs3)
        slug3 = p3_data.get("slug")
        if len(slug3) > 75: slug3 = slug3[:75]
        
        tags3 = p3_data.get("tags", [])
        tag_ids3 = wp_client.get_or_create_tags(tags3) if tags3 else []

        res = wp_client.create_post(
            title=p3_data["title"], content=p3_data["content"], status="draft", slug=slug3,
            featured_media_id=fid3, categories=[2], tags=tag_ids3,
            meta_input={"rank_math_focus_keyword": p3_data["rank_math_focus_keyword"], "rank_math_description": p3_data["rank_math_description"]}
        )
        
        if res:
            print(f"✅ Post 3 Created! Chain Complete. Link: {res}")
        else:
            print("❌ Post 3 Creation Failed.")

if __name__ == "__main__":
    run_chain_v2()
