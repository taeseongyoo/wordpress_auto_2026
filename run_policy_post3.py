import time
import requests
import re
from src.config.settings import Config
from src.core.generator import ContentGenerator
from src.core.image_processor import ImageProcessor
from src.core.wp_client import WordPressClient
from src.utils.logger import get_logger

# Logger setup
logger = get_logger("PolicyCampaign_Post3")

# Configuration
Config.validate()

# --- [FIXED] 5 Internal Links for Post 3 (K-Pass) ---
# Strategy: 
# 1. 2026 청년월세지원 (ID 784) - Immediate Predecessor
# 2. 2026 정부지원금 통합 조회 (ID 778) - Chain Root
# 3. 청년도약계좌 신청 (ID 737) - Financial support
# 4. 청년미래적금 2026 (ID 743) - Financial support
# 5. AI 스마트워크 (ID 745) - Cross category
INTERNAL_LINKS = [
    {"title": "2026 청년월세지원 신청 가이드", "link": "https://smart-work-solution.com/?p=784"},
    {"title": "2026 정부지원금 통합 조회", "link": "https://smart-work-solution.com/?p=778"},
    {"title": "청년도약계좌 신청 방법", "link": "https://smart-work-solution.com/youth-future-savings-vs-leap-account-2026/"}, 
    {"title": "청년미래적금 2026 혜택", "link": "https://smart-work-solution.com/youth-future-savings-2026-application/"},
    {"title": "AI 스마트워크 수익화 전략", "link": "https://smart-work-solution.com/?p=745"},
]

def process_images_for_post(post_data, wp_client, image_processor):
    """Generates and uploads images for a post."""
    images_data = post_data.get("images", [])
    if not images_data:
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

def run_policy_post3():
    wp_client = WordPressClient()
    generator = ContentGenerator()
    image_processor = ImageProcessor()
    
    print("\n🚀 Starting Policy Support Campaign: Generating Post 3...")
    print(f"🔗 Injecting {len(INTERNAL_LINKS)} Internal Links (Mid-Content Strategy)...")
    
    # Topic: K-Pass 2026
    topic3 = "2026 K-패스(K-Pass) 교통카드 신청 방법 및 환급 혜택 총정리"
    
    # Pass FIXED links
    p3_data = generator.generate_post(topic3, internal_links=INTERNAL_LINKS)
    
    if p3_data:
        fid3, b_imgs3 = process_images_for_post(p3_data, wp_client, image_processor)
        p3_data["content"] = insert_body_images(p3_data["content"], b_imgs3)
        slug3 = p3_data.get("slug")
        if len(slug3) > 75: slug3 = slug3[:75]
        
        tags3 = p3_data.get("tags", [])
        tag_ids3 = wp_client.get_or_create_tags(tags3) if tags3 else []

        # Create Post
        res = wp_client.create_post(
            title=p3_data["title"], 
            content=p3_data["content"], 
            status="draft", 
            slug=slug3,
            featured_media_id=fid3, 
            categories=[2], # Policy Solutions
            tags=tag_ids3,
            meta_input={
                "rank_math_focus_keyword": p3_data["rank_math_focus_keyword"], 
                "rank_math_description": p3_data["rank_math_description"]
            }
        )
        
        if res:
            print(f"✅ Post 3 Created! Link: {res}")
        else:
            print("❌ Post 3 Creation Failed.")

if __name__ == "__main__":
    run_policy_post3()
