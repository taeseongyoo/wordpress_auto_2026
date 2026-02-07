import requests
from src.config.settings import Config

def get_categories():
    Config.validate()
    base_url = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2"
    auth = (Config.WP_USERNAME, Config.WP_PASSWORD)
    
    try:
        response = requests.get(f"{base_url}/categories", auth=auth)
        response.raise_for_status()
        categories = response.json()
        
        print("\n=== 카테고리 목록 ===")
        for cat in categories:
            print(f"ID: {cat['id']} | 이름: {cat['name']} | 슬러그: {cat['slug']}")
            
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    get_categories()
