# Post 2 이미지 수리 스크립트
# Post 2 (ID: 675)의 본문 이미지가 누락됨
# 이 스크립트는 새 이미지를 생성하고 업로드 후 본문에 삽입합니다.

import requests
import re
import time
from src.config.settings import Config
from src.core.image_processor import ImageProcessor
from src.core.wp_client import WordPressClient
from src.utils.logger import get_logger

logger = get_logger("RepairPost2")

def main():
    Config.validate()
    print("✅ 설정 검증 완료")
    
    BASE_URL = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2"
    AUTH = (Config.WP_USERNAME, Config.WP_PASSWORD)
    
    wp_client = WordPressClient()
    image_processor = ImageProcessor()
    
    # Post 2 정보
    POST_ID = 675
    SLUG = "government-funding-business-plan-2026"
    KEYWORD = "정부지원금 사업계획서"
    
    print(f"\n🔧 Post 2 (ID: {POST_ID}) 이미지 수리 시작...")
    
    # 1. Post 2 내용 가져오기
    print("📄 포스트 내용 가져오는 중...")
    r = requests.get(f"{BASE_URL}/posts/{POST_ID}", auth=AUTH)
    if r.status_code != 200:
        print(f"❌ 포스트 가져오기 실패: {r.status_code}")
        return
    
    post_data = r.json()
    original_content = post_data['content']['rendered']
    title = post_data['title']['rendered']
    print(f"✅ 포스트 제목: {title}")
    
    # 2. 이미지 생성 (3장)
    print("\n🎨 본문 이미지 3장 생성 중...")
    
    image_prompts = [
        "Modern infographic showing a business plan document with charts and graphs for government funding application, professional style, blue and white color scheme",
        "Step-by-step visual guide for writing a business proposal, including sections like executive summary, budget, and timeline, clean corporate design",
        "Success case study infographic showing approved government funding applications, with checkmarks and approval stamps, inspiring and professional"
    ]
    
    body_images = []
    
    for idx, prompt in enumerate(image_prompts, 1):
        file_name = f"{SLUG}_body_{idx}.webp"
        print(f"   🖼️ 이미지 {idx}/3 생성 중...")
        
        image_path = image_processor.generate_image(prompt, file_name)
        
        if image_path:
            # 워드프레스에 업로드
            upload_result = wp_client.upload_image(
                image_path,
                title=f"{KEYWORD} 가이드 이미지 {idx}",
                caption=f"{KEYWORD} 작성 팁 {idx}",
                alt_text=f"{KEYWORD} 관련 인포그래픽 {idx}",
                description=f"정부지원금 사업계획서 작성을 위한 시각 자료"
            )
            
            if upload_result:
                body_images.append({
                    'id': upload_result['id'],
                    'url': upload_result['source_url'],
                    'alt': f"{KEYWORD} 관련 인포그래픽 {idx}",
                    'caption': f"{KEYWORD} 작성 팁 {idx}"
                })
                print(f"   ✅ 이미지 {idx} 업로드 완료 (ID: {upload_result['id']})")
            else:
                print(f"   ❌ 이미지 {idx} 업로드 실패")
        else:
            print(f"   ❌ 이미지 {idx} 생성 실패")
    
    if len(body_images) == 0:
        print("❌ 이미지 생성/업로드 완전 실패. 중단합니다.")
        return
    
    print(f"\n✅ 총 {len(body_images)}장 이미지 준비 완료!")
    
    # 3. 본문에 이미지 삽입
    print("\n📝 본문에 이미지 삽입 중...")
    
    # 기존 이미지 관련 태그 제거 (만약 있다면)
    clean_content = re.sub(r'<figure.*?</figure>', '', original_content, flags=re.DOTALL)
    clean_content = re.sub(r'<img.*?>', '', clean_content)
    clean_content = re.sub(r'<!-- wp:image.*?-->', '', clean_content, flags=re.DOTALL)
    clean_content = re.sub(r'<!-- /wp:image -->', '', clean_content)
    clean_content = re.sub(r'\n\s*\n', '\n\n', clean_content)
    
    # H2 태그 뒤에 이미지 삽입
    parts = re.split(r'(</h2>)', clean_content)
    final_content = ""
    img_idx = 0
    
    for part in parts:
        final_content += part
        if part == "</h2>" and img_idx < len(body_images):
            m = body_images[img_idx]
            
            # Gutenberg 블록 형식으로 삽입
            block_html = (
                f'\n<!-- wp:image {{"id":{m["id"]},"sizeSlug":"large","linkDestination":"none"}} -->\n'
                f'<figure class="wp-block-image size-large">'
                f'<img src="{m["url"]}" alt="{m["alt"]}" class="wp-image-{m["id"]}"/>'
                f'<figcaption>{m["caption"]}</figcaption>'
                f'</figure>\n'
                f'<!-- /wp:image -->\n'
            )
            final_content += block_html
            print(f"   ✅ 이미지 {img_idx + 1} 삽입 완료")
            img_idx += 1
    
    # 4. 포스트 업데이트
    print("\n🔄 포스트 업데이트 중...")
    ur = requests.post(f"{BASE_URL}/posts/{POST_ID}", auth=AUTH, json={'content': final_content})
    
    if ur.status_code == 200:
        print(f"\n🎉 Post 2 (ID: {POST_ID}) 수리 완료!")
        print(f"   📸 삽입된 이미지: {len(body_images)}장")
    else:
        print(f"❌ 포스트 업데이트 실패: {ur.status_code}")
        print(ur.text[:200])

if __name__ == "__main__":
    main()
