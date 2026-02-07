import requests
import json
from src.config.settings import Config
from src.utils.logger import get_logger

# 직접 REST API 호출 테스트
base_url = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2"
auth = (Config.WP_USERNAME, Config.WP_PASSWORD)
post_id = 579

def update_post_meta(data):
    endpoint = f"{base_url}/posts/{post_id}"
    response = requests.post(endpoint, auth=auth, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    
    # 확인
    check_response = requests.get(endpoint, auth=auth)
    current_meta = check_response.json().get('meta', {})
    print(f"Current Meta: {json.dumps(current_meta, indent=2, ensure_ascii=False)}")

print("--- Test 1: Standard 'meta' key ---")
update_post_meta({
    "meta": {
        "rank_math_focus_keyword": "TEST_KEYWORD_1"
    }
})

print("\n--- Test 2: Underscore key ---")
update_post_meta({
    "meta": {
        "_rank_math_focus_keyword": "TEST_KEYWORD_2"
    }
})
