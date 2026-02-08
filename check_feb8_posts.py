import requests
from datetime import datetime
from src.config.settings import Config
from src.utils.logger import get_logger
import json

logger = get_logger("CheckFeb8")

def check_posts():
    Config.validate()
    base_url = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2/posts"
    auth = (Config.WP_USERNAME, Config.WP_PASSWORD)
    
    # KST 기준 2월 8일 (UTC로 변환하여 넉넉하게 조회)
    params = {
        "after": "2026-02-07T00:00:00",
        "before": "2026-02-09T00:00:00",
        "per_page": 20,
        "status": "publish,draft,future" # 모든 상태 조회
    }
    
    print(f"🔍 Checking posts from {base_url}...")
    try:
        response = requests.get(base_url, auth=auth, params=params)
        response.raise_for_status()
        posts = response.json()
        
        if not posts:
            print("❌ 2월 8일 근처에 발행된 글이 없습니다.")
            return

        print(f"✅ 총 {len(posts)}개의 글을 찾았습니다 (2/7 ~ 2/9 범위).\n")
        
        target_date = "2026-02-08"
        
        for post in posts:
            # 포스트 날짜 (WordPress는 기본적으로 설정된 로컬 시간대 반환 or UTC. 보통 date 필드는 로컬 시간)
            post_date = post['date'].split("T")[0]
            
            if post_date == target_date:
                print(f"📌 [2월 8일 발행] ID: {post['id']}")
                print(f"   제목: {post['title']['rendered']}")
                print(f"   상태: {post['status']}")
                print(f"   작성자 ID: {post['author']}")
                
                # 메타데이터 확인 (이 프로그램의 특징인지)
                meta = post.get('meta', {})
                print(f"   Rank Math 키워드: {meta.get('rank_math_focus_keyword', '없음')}")
                
                # 내용에서 특징 찾기
                content = post['content']['rendered']
                if "gpt-4o" in content or "AI" in content: # 혹시나 흔적이 있는지
                     print("   특이사항: 본문에 AI 관련 키워드 포함")
                
                print("-" * 30)

    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    check_posts()
