import time
import requests
import re
from src.config.settings import Config
from src.core.generator import ContentGenerator
from src.core.image_processor import ImageProcessor
from src.core.wp_client import WordPressClient
from src.utils.logger import get_logger

# 1. 로거 설정 (Logger Setup)
logger = get_logger("ChainNewStart")

# 2. 설정 로드 (Configuration)
Config.validate()
BASE_URL = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2/posts"
AUTH = (Config.WP_USERNAME, Config.WP_PASSWORD)

def process_images_for_post(post_data, wp_client, image_processor):
    """
    포스트의 이미지를 생성하고 워드프레스에 업로드합니다.
    """
    images_data = post_data.get("images", [])
    
    # 이미지 데이터가 없으면 프롬프트만 있는 경우를 대비 (구버전 호환)
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
    
    logger.info(f"🎨 이미지 생성 시작: 총 {len(images_data)}장 ('{post_data['title']}')")
    
    slug = post_data.get("slug", "post")
    
    for idx, img_meta in enumerate(images_data):
        prompt_raw = img_meta.get("prompt", "")
        # 프롬프트에서 불필요한 접두어 제거
        prompt_clean = re.sub(r"^(썸네일용|본문이미지\d+):\s*", "", prompt_raw)
        
        file_suffix = "thumb" if idx == 0 else f"body_{idx}"
        file_name = f"{slug}_{file_suffix}.webp"
        
        # 이미지 생성 (Image Processor)
        image_path = image_processor.generate_image(prompt_clean, file_name)
        
        if image_path:
            # 워드프레스 업로드
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
                    logger.info(f"✅ 썸네일 업로드 완료 (ID: {featured_media_id})")
                else:
                    # 본문용 이미지 HTML 코드 생성
                    img_html = (
                        f'\n<figure class="wp-block-image size-large">'
                        f'<img src="{upload_result["source_url"]}" alt="{img_meta.get("alt", "")}" class="wp-image-body-{idx}"/>'
                        f'<figcaption>{img_meta.get("caption", "")}</figcaption>'
                        f'</figure>\n'
                    )
                    body_image_htmls.append(img_html)
                    logger.info(f"✅ 본문 이미지 {idx} 업로드 완료")
        else:
            logger.error(f"❌ 이미지 생성 실패: {prompt_clean[:20]}...")

    return featured_media_id, body_image_htmls

def insert_body_images(content, body_image_htmls):
    """
    본문 이미지들을 H2 태그 뒤에 순차적으로 삽입합니다.
    """
    if not body_image_htmls: return content
    
    # 기존 플레이스홀더 제거 (혹시 있다면)
    cleanup_patterns = [r"\[이미지 설명.*?\]", r"그림 \d+.*?\n", r"\*\*이미지 설명:\*\*.*?\n"]
    for pattern in cleanup_patterns:
        content = re.sub(pattern, "", content, flags=re.IGNORECASE)

    # H2 태그를 기준으로 본문 분리
    h2_split = re.split(r'(</h2>)', content)
    new_content = ""
    img_idx = 0
    
    for part in h2_split:
        new_content += part
        # H2 태그가 닫힐 때마다 이미지 하나씩 삽입
        if part == "</h2>" and img_idx < len(body_image_htmls):
            new_content += body_image_htmls[img_idx]
            img_idx += 1
            
    return new_content

def run_new_chain_start():
    """
    새로운 체인 포스트 시리즈의 첫 번째 글(Post 1)을 생성합니다.
    """
    # 3. 도구 초기화 (Tool Initialization)
    wp_client = WordPressClient()
    generator = ContentGenerator()
    image_processor = ImageProcessor()

    # 4. 주제 선정 (Topic Selection)
    # TODO: 사용자 입력 또는 자동화된 리스트에서 가져오기
    topic = "AI 마케팅 자동화 및 수익화 2026"  # 기본값
    print(f"\n🚀 새로운 체인 시리즈 시작: Post 1 생성 중...")
    print(f"📌 주제: {topic}")

    # 5. 콘텐츠 생성 (Content Generation)
    # Post 1은 내부 링크의 '목적지'가 될 것이므로, 지금은 내부 링크를 비워두거나 
    # 기존의 다른 인기 글(Anchor Post)을 하나 넣어줄 수 있습니다.
    anchor_post = {
        "title": "AI 스마트워크로 1인 기업 수익화 시작하는 법: 2026년 필승 가이드",
        "link": "https://smart-work-solution.com/?p=745" # ID 745 (이전 체인 Post 1)
    }
    
    post_data = generator.generate_post(topic, internal_links=[anchor_post])
    
    if post_data:
        # 6. 이미지 처리 (Image Processing)
        fid, body_imgs = process_images_for_post(post_data, wp_client, image_processor)
        
        # 7. 본문 이미지 삽입
        post_data["content"] = insert_body_images(post_data["content"], body_imgs)
        
        # 8. 슬러그 길이 조정 (안전장치)
        slug = post_data.get("slug", "ai-marketing-2026")
        if len(slug) > 75: slug = slug[:75]
        
        # 9. 태그 처리
        tags = post_data.get("tags", [])
        tag_ids = wp_client.get_or_create_tags(tags) if tags else []

        # 10. 워드프레스 포스트 생성 (Draft)
        res = wp_client.create_post(
            title=post_data["title"],
            content=post_data["content"],
            status="draft", # 안전을 위해 Draft로 저장
            slug=slug,
            featured_media_id=fid,
            categories=[86], # 카테고리 ID 86: AI 스마트워크 & 수익화
            tags=tag_ids,
            meta_input={
                "rank_math_focus_keyword": post_data["rank_math_focus_keyword"],
                "rank_math_description": post_data["rank_math_description"]
            }
        )
        
        if res:
            post_id = res.split("p=")[-1] if "p=" in res else "Unknown"
            print(f"✅ Post 1 생성 완료! (ID: {post_id})")
            print(f"🔗 링크: {res}")
            # 제목은 post_data에서 가져옴 (res가 문자열이라서)
            print(f"📝 제목: {post_data['title']}")
            
            # 로그 파일 업데이트 (PROGRESS.md)는 별도 유틸리티 또는 수동으로 수행
            # 여기서는 콘솔 출력으로 갈음
        else:
            print("❌ Post 1 생성 실패.")
    else:
        print("❌ 콘텐츠 생성 실패.")

if __name__ == "__main__":
    run_new_chain_start()
