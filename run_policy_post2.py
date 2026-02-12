import time
import requests
import re
from src.config.settings import Config
from src.core.generator import ContentGenerator
from src.core.image_processor import ImageProcessor
from src.core.wp_client import WordPressClient
from src.utils.logger import get_logger

# Logger setup
logger = get_logger("PolicyCampaign_Post2")

# Configuration
Config.validate()

# --- [FIXED] 5 Internal Links (Hardcoded for Walled Garden + Recent) ---
INTERNAL_LINKS = [
    {"title": "2026년 정부지원금 통합 조회 및 신청 방법", "link": "https://smart-work-solution.com/?p=778"}, # Post 1 (Immediate Predecessor)
    {"title": "청년미래적금 혜택 및 금리 비교 2026", "link": "https://smart-work-solution.com/youth-future-savings-vs-leap-account-2026/"}, # ID 743
    {"title": "청년미래적금 2026 신청 기간 및 방법", "link": "https://smart-work-solution.com/youth-future-savings-2026-application/"}, # ID 737
    {"title": "AI 전자책 수익화 2026: 지식 창업 가이드", "link": "https://smart-work-solution.com/ai-ebook-monetization-2026/"}, # ID 710 (Categories Cross-link)
    {"title": "AI 유튜브 수익화 2026: 채널 성공 공식", "link": "https://smart-work-solution.com/ai-youtube-monetization-2026/"}, # ID 704
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
        # Clean specific korean prefixes if exist
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

def run_policy_post2():
    wp_client = WordPressClient()
    generator = ContentGenerator()
    image_processor = ImageProcessor()
    
    print("\n🚀 Starting Policy Support Campaign: Generating Post 2...")
    print(f"🔗 Injecting {len(INTERNAL_LINKS)} Internal Links (Fixed Strategy)...")
    
    # Topic: Youth Rent Support
    topic2 = "2026년 청년 월세 특별 지원: 조건, 신청 방법 및 지급일 총정리"
    
    # Pass FIXED links
    p2_data = generator.generate_post(topic2, internal_links=INTERNAL_LINKS)
    
    if p2_data:
        fid2, b_imgs2 = process_images_for_post(p2_data, wp_client, image_processor)
        p2_data["content"] = insert_body_images(p2_data["content"], b_imgs2)
        slug2 = p2_data.get("slug")
        if len(slug2) > 75: slug2 = slug2[:75]
        
        tags2 = p2_data.get("tags", [])
        tag_ids2 = wp_client.get_or_create_tags(tags2) if tags2 else []

        # Create Post
        res = wp_client.create_post(
            title=p2_data["title"], 
            content=p2_data["content"], 
            status="draft", 
            slug=slug2,
            featured_media_id=fid2, 
            categories=[2], # Policy Solutions
            tags=tag_ids2,
            meta_input={
                "rank_math_focus_keyword": p2_data["rank_math_focus_keyword"], 
                "rank_math_description": p2_data["rank_math_description"]
            }
        )
        
        if res:
            print(f"✅ Post 2 Created! Link: {res}")
        else:
            print("❌ Post 2 Creation Failed.")

if __name__ == "__main__":
    run_policy_post2()
