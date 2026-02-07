import requests
import re
from src.config.settings import Config
from src.utils.logger import get_logger

# 로거 설정
logger = get_logger("SEO_Verifier")

class SEOVerifier:
    def __init__(self):
        Config.validate()
        self.base_url = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2"
        self.auth = (Config.WP_USERNAME, Config.WP_PASSWORD)

    def get_latest_draft(self):
        """가장 최근의 임시저장(Draft) 포스트를 가져옵니다."""
        try:
            endpoint = f"{self.base_url}/posts"
            params = {
                "status": "draft",
                "per_page": 1,
                "orderby": "date",
                "order": "desc"
            }
            response = requests.get(endpoint, auth=self.auth, params=params)
            response.raise_for_status()
            posts = response.json()
            return posts[0] if posts else None
        except Exception as e:
            logger.error(f"포스트 조회 실패: {e}")
            return None

    def analyze_seo(self, post):
        """포스트의 SEO 요소를 분석합니다."""
        if not post:
            logger.warning("분석할 포스트가 없습니다.")
            return

        print("\n" + "="*40)
        print(f"🔍 SEO 진단 보고서: {post['title']['rendered']}")
        print("="*40)

        # 1. 메타데이터 (Rank Math) 확인
        meta = post.get("meta", {})
        focus_keyword = meta.get("rank_math_focus_keyword")
        seo_desc = meta.get("rank_math_description")

        self._print_result("Rank Math 키워드(Key)", focus_keyword, focus_keyword)
        self._print_result("메타 설명(Description)", seo_desc, seo_desc)

        # 2. 콘텐츠 분석
        content = post['content']['rendered']
        
        # 글자 수 (HTML 태그 제거 후 대략적 계산)
        text_content = re.sub('<[^<]+?>', '', content)
        char_count = len(text_content)
        self._print_result("글자 수 (2000자 이상 권장)", f"{char_count}자", char_count >= 2000)

        # H2 태그 개수
        h2_count = len(re.findall(r'<h2', content))
        self._print_result("H2 태그 (4개 이상 권장)", f"{h2_count}개", h2_count >= 4)

        # 키워드 밀도 (제목 불일치 시 경고)
        if focus_keyword:
            keyword_in_title = focus_keyword in post['title']['rendered']
            self._print_result("제목에 키워드 포함", "포함됨" if keyword_in_title else "미포함", keyword_in_title)
            
            keyword_count = content.count(focus_keyword)
            self._print_result(f"본문 키워드 반복 ('{focus_keyword}')", f"{keyword_count}회", keyword_count > 0)

        # 3. 이미지 분석
        featured_media_id = post.get("featured_media")
        if featured_media_id:
             # 미디어 정보 추가 조회 필요하지만 일단 ID 존재 여부만 체크
             self._print_result("썸네일 이미지", f"ID: {featured_media_id}", True)
        else:
             self._print_result("썸네일 이미지", "없음", False)
        
        print("\n[종합 의견]")
        if char_count >= 2000 and h2_count >= 4 and focus_keyword and seo_desc:
            print("✅ 훌륭합니다! Rank Math 80점 이상이 예상됩니다.")
        else:
            print("⚠️ 일부 요소가 부족합니다. 위 항목을 보완해주세요.")

    def _print_result(self, label, value, is_pass):
        mark = "✅" if is_pass else "❌"
        print(f"{mark} {label}: {value}")

def main():
    verifier = SEOVerifier()
    post = verifier.get_latest_draft()
    verifier.analyze_seo(post)

if __name__ == "__main__":
    main()
