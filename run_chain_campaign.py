
import time
import requests
from src.config.settings import Config
from src.core.generator import ContentGenerator
from src.utils.logger import get_logger

# Logger setup
logger = get_logger("ChainCampaign")

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

    # WordPress Payload
    payload = {
        "title": post_data["title"],
        "content": post_data["content"],
        "status": "draft",  # Safety first!
        "slug": post_data["slug"],
        "meta": {
            "rank_math_focus_keyword": post_data["rank_math_focus_keyword"],
            "rank_math_description": post_data["rank_math_description"]
        }
    }
    
    # Upload Feature Image if available (Skipping for now to focus on text logic, or reuse existing)
    # in a real scenario, we would generate and upload images here.

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

def run_chain():
    # 0. Anchor Post (Existing)
    # [ID: 528] 1인 사업자 정부지원금 2026: 최대 7천만원 받는 7가지 방법 완벽 가이드
    ANCHOR_POST = {
        "id": 528,
        "title": "1인 사업자 정부지원금 2026: 최대 7천만원 받는 7가지 방법 완벽 가이드",
        "link": "https://smart-work-solution.com/2026-government-funding-for-small-business/" 
        # Note: Actual link might differ, usually we fetch it, but for now assuming/fetching by ID is safer.
    }
    
    # Verify Anchor Link (Optional but recommended)
    try:
        r = requests.get(f"{BASE_URL}/528", auth=AUTH)
        if r.status_code == 200:
            ANCHOR_POST['link'] = r.json()['link']
            print(f"⚓ Anchor Post Verified: {ANCHOR_POST['link']}")
        else:
            print("⚠️ Anchor Post ID 528 not found? Using default logic.")
    except:
        pass

    # Chain Execution Order (Reverse: 1 -> 2 -> 3? No, we need Link of 1 to put in 2)
    # So order is: Generate 1 (get link) -> Generate 2 (put link of 1) -> Generate 3 (put link of 2)
    
    # 1. Post 1 (The Hub) -> Links to Anchor
    print("\n--- [Step 1] Generating Post 1 (Hub) ---")
    post1 = create_post_draft(
        title="2026년 정부지원금 종류 및 신청 기간 총정리",
        topic="2026년 정부지원금 종류 및 신청 기간 총정리",
        internal_links=[ANCHOR_POST]
    )
    if not post1: return

    time.sleep(2) # Safety pause

    # 2. Post 2 (The How-to) -> Links to Post 1
    print("\n--- [Step 2] Generating Post 2 (How-to) ---")
    post2 = create_post_draft(
        title="정부지원금 합격을 위한 사업계획서 작성 필수 꿀팁",
        topic="정부지원금 합격을 위한 사업계획서 작성 필수 꿀팁",
        internal_links=[post1]
    )
    if not post2: return
    
    time.sleep(2)

    # 3. Post 3 (The Trend) -> Links to Post 2
    print("\n--- [Step 3] Generating Post 3 (Trend) ---")
    post3 = create_post_draft(
        title="2026년 바뀌는 정부 지원 정책: 놓치면 손해 보는 3가지",
        topic="2026년 바뀌는 정부 지원 정책: 놓치면 손해 보는 3가지",
        internal_links=[post2]
    )
    
    print("\n✨ All Chained Posts Generated Successfully!")
    print(f"1. {post1['title']} (Linked to Anchor)")
    print(f"2. {post2['title']} (Linked to Post 1)")
    print(f"3. {post3['title']} (Linked to Post 2)")

if __name__ == "__main__":
    run_chain()
