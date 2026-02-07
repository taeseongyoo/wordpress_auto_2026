import sys
import argparse
import re
from src.core.wp_client import WordPressClient
from src.core.generator import ContentGenerator
from src.core.image_processor import ImageProcessor
from src.utils.logger import get_logger

logger = get_logger("Main")

def main():
    parser = argparse.ArgumentParser(description="WordPress Automation System v1.0")
    parser.add_argument("topic", type=str, nargs='?', help="블로그 포스트 주제")
    args = parser.parse_args()

    topic = args.topic
    if not topic:
        topic = input("게시할 블로그 주제를 입력하세요: ")

    if not topic:
        logger.error("주제가 입력되지 않았습니다. 종료합니다.")
        return

    logger.info("========================================")
    logger.info(f"작업 시작: '{topic}'")
    logger.info("========================================")

    # 1. 모듈 초기화
    try:
        wp_client = WordPressClient()
        generator = ContentGenerator()
        image_processor = ImageProcessor()
    except Exception as e:
        logger.critical(f"초기화 실패 (환경 변수를 확인해주세요): {e}")
        return

    # 2. 콘텐츠 생성
    logger.info("1단계: AI 콘텐츠 생성 중... (Rank Math 100점 전략)")
    
    # 내부 링크용 최신 글 조회
    internal_links = wp_client.get_recent_posts(count=5)
    logger.info(f"내부 링크 타겟 조회 완료: {len(internal_links)}개")
    
    post_data = generator.generate_post(topic, internal_links=internal_links)
    if not post_data:
        logger.error("콘텐츠 생성 실패. 종료합니다.")
        return

    title = post_data.get("title", f"자동 생성된 포스트: {topic}")
    content = post_data.get("content", "")
    tags = post_data.get("tags", [])
    slug = post_data.get("slug", "")
    focus_keyword = post_data.get("rank_math_focus_keyword", topic)

    logger.info(f"생성된 제목: {title}")
    logger.info(f"핵심 키워드: {focus_keyword}")

    # 3. 카테고리 자동 매핑
    # 2: 정책 & 지원금, 86: AI 수익화 & 스마트워크
    category_ids = [86] # 기본값: AI 수익화
    if any(keyword in focus_keyword or keyword in topic for keyword in ["지원금", "정책", "보조금", "수당", "복지"]):
        category_ids = [2]
    logger.info(f"카테고리 매핑: {category_ids}")

    # 4. 이미지 처리 (멀티 이미지 전략)
    # 4. 이미지 처리 (멀티 이미지 전략 V2 - Smart Metadata)
    images_data = post_data.get("images", [])
    
    # 하위 호환성: images가 없고 image_prompts만 있는 경우 변환
    if not images_data:
        raw_prompts = post_data.get("image_prompts", [])
        if not raw_prompts:
            raw_prompts = [f"썸네일용: {topic}, {title}"]
            
        for idx, p in enumerate(raw_prompts):
            images_data.append({
                "type": "featured" if idx == 0 else "body",
                "prompt": p,
                "alt": f"{focus_keyword} image {idx}",
                "caption": f"{focus_keyword} 관련 이미지 {idx}"
            })

    featured_media_id = None
    body_image_urls = []

    logger.info(f"2단계: 이미지 {len(images_data)}장 생성 및 업로드 중...")
    
    for idx, img_meta in enumerate(images_data):
        prompt_raw = img_meta.get("prompt", "")
        # 프롬프트 전처리 (접두어 제거)
        prompt_clean = re.sub(r"^(썸네일용|본문이미지\d+):\s*", "", prompt_raw)
        
        # 파일명 생성 (슬러그 활용 + 인덱스 + WebP)
        file_suffix = "thumb" if idx == 0 else f"body_{idx}"
        file_name = f"{slug}_{file_suffix}.webp"
        
        logger.info(f"[{idx+1}/{len(images_data)}] 이미지 생성: {prompt_clean[:30]}...")
        image_path = image_processor.generate_image(prompt_clean, file_name)
        
        if image_path:
            # 메타데이터 설정 (Smart Metadata 사용)
            # 썸네일은 제목을, 본문 이미지는 Alt 텍스트 기반으로 제목 설정
            img_title = title if idx == 0 else f"{focus_keyword}_{idx}"
            img_alt = img_meta.get("alt", f"{focus_keyword} image")
            img_caption = img_meta.get("caption", title)
            img_desc = post_data.get("rank_math_description", "") if idx == 0 else ""

            upload_result = wp_client.upload_image(
                image_path, 
                title=img_title,
                caption=img_caption, 
                alt_text=img_alt,
                description=img_desc
            )

            if upload_result:
                if idx == 0:
                    featured_media_id = upload_result['id']
                    logger.info(f"썸네일 등록 완료 (ID: {featured_media_id})")
                else:
                    body_image_urls.append({
                        "url": upload_result['source_url'],
                        "alt": img_alt,
                        "caption": img_caption
                    })
                    logger.info(f"본문 이미지 {idx} 업로드 완료")
            else:
                logger.error(f"이미지 {idx} 업로드 실패")
        else:
            logger.error(f"이미지 {idx} 생성 실패")

    # 5. 본문 이미지 삽입 (H2 태그 후)
    if body_image_urls:
        logger.info("3단계: 본문에 이미지 삽입 중...")
        
        # 불필요한 이미지 설명 텍스트 제거 (이중 안전장치)
        cleanup_patterns = [
            r"\[이미지 설명.*?\]",
            r"그림 \d+.*?\n",
            r"Figure \d+.*?\n",
            r"\*\*이미지 설명:\*\*.*?\n",
            r"AI 수익화 로드맵 관련 상세 이미지 \d+",  # 사용자가 제보한 특정 패턴
        ]
        for pattern in cleanup_patterns:
            content = re.sub(pattern, "", content, flags=re.IGNORECASE)

        # H2 태그 찾기
        h2_split = re.split(r'(</h2>)', content)
        
        new_content = ""
        img_idx = 0
        
        for part in h2_split:
            new_content += part
            if part == "</h2>" and img_idx < len(body_image_urls):
                # 이미지 태그 생성 (Rank Math가 좋아하는 figure 태그 사용 권장하지만 간단히 img로 처리)
                img_info = body_image_urls[img_idx]
                img_html = (
                    f'\n<figure class="wp-block-image size-large">'
                    f'<img src="{img_info["url"]}" alt="{img_info["alt"]}" class="wp-image-body-{img_idx+1}"/>'
                    f'<figcaption>{img_info["caption"]}</figcaption>'
                    f'</figure>\n'
                )
                new_content += img_html
                img_idx += 1
        
        content = new_content

    # 6. 포스트 발행
    logger.info("4단계: 워드프레스 포스팅 및 SEO 적용 중...")
    
    # 태그 ID 변환
    tag_ids = []
    if tags:
        logger.info(f"태그 ID 변환 중: {tags}")
        tag_ids = wp_client.get_or_create_tags(tags)
    
    meta_input = {}
    if "rank_math_focus_keyword" in post_data:
        meta_input["rank_math_focus_keyword"] = post_data["rank_math_focus_keyword"]
    if "rank_math_description" in post_data:
        meta_input["rank_math_description"] = post_data["rank_math_description"]

    post_link = wp_client.create_post(
        title=title,
        content=content,
        status="draft", 
        categories=category_ids,
        tags=tag_ids,
        featured_media_id=featured_media_id,
        meta_input=meta_input
    )

    if post_link:
        logger.info("========================================")
        logger.info("🎉 작업 완료! 🎉")
        logger.info(f"포스트가 '임시저장(Draft)' 상태로 생성되었습니다.")
        logger.info(f"확인 링크: {post_link}")
        logger.info(f"카테고리: {category_ids}")
        logger.info(f"태그: {tags} (IDs: {tag_ids})")
        logger.info(f"이미지: 썸네일 + {len(body_image_urls)}장 삽입됨")
        logger.info("========================================")
    else:
        logger.error("포스트 발행 실패.")

if __name__ == "__main__":
    main()
