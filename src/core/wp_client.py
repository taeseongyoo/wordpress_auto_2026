import requests
import base64
from typing import Dict, Any, Optional
from src.config.settings import Config
from src.utils.logger import get_logger

logger = get_logger("WP_Client")

class WordPressClient:
    """
    워드프레스 REST API와 통신하여 포스트 생성, 미디어 업로드 등을 수행하는 클라이언트입니다.
    """

    def __init__(self):
        Config.validate()
        self.base_url = f"{Config.WP_URL.rstrip('/')}/wp-json/wp/v2"
        self.auth = (Config.WP_USERNAME, Config.WP_PASSWORD)
        
        # 헤더 설정 (Application Password 인증 시 Basic Auth 사용)
        # requests.auth.HTTPBasicAuth를 사용하므로 직접 헤더에 넣을 필요는 없으나,
        # 디버깅 편의를 위해 자격 증명 확인 로직을 추가할 수 있습니다.

    def upload_image(self, image_path: str, caption: str = "", title: str = "", alt_text: str = "", description: str = "") -> Optional[Dict[str, Any]]:
        """
        로컬 이미지를 워드프레스 미디어 라이브러리에 업로드합니다. (메타데이터 풀 지원)
        
        Args:
            image_path (str): 업로드할 이미지의 로컬 경로
            caption (str): 이미지 캡션
            title (str): 이미지 제목 (Title)
            alt_text (str): 대체 텍스트 (Alt Text)
            description (str): 이미지 설명 (Description)
            
        Returns:
            Optional[Dict[str, Any]]: 업로드 성공 시 {'id': int, 'source_url': str}, 실패 시 None
        """
        if not image_path:
            logger.warning("이미지 경로가 제공되지 않았습니다.")
            return None

        endpoint = f"{self.base_url}/media"
        file_name = image_path.split("/")[-1]

        try:
            # 이미지 파일 열기
            with open(image_path, "rb") as img_file:
                files = {
                    "file": (file_name, img_file, "image/jpeg")
                }
                
                # 메타데이터 구성
                data = {
                    "caption": caption,
                    "title": title if title else file_name,
                    "alt_text": alt_text if alt_text else title,
                    "description": description
                }
                
                logger.info(f"이미지 업로드 시도: {file_name}")
                response = requests.post(
                    endpoint,
                    auth=self.auth,
                    files=files,
                    data=data
                )
                
                response.raise_for_status()
                result = response.json()
                media_info = {
                    "id": result.get("id"),
                    "source_url": result.get("source_url")
                }
                logger.info(f"이미지 업로드 성공! ID: {media_info['id']}")
                return media_info

        except Exception as e:
            logger.error(f"이미지 업로드 실패: {e}")
            if 'response' in locals() and response.status_code != 200:
                logger.error(f"응답 내용: {response.text}")
            return None

    def create_post(self, title: str, content: str, status: str = "draft", 
                    categories: list = None, tags: list = None, featured_media_id: int = None,
                    meta_input: dict = None, slug: str = None) -> Optional[str]:
        """
        새로운 포스트를 생성합니다. (Rank Math 메타데이터 지원)
        
        Args:
            title (str): 포스트 제목
            content (str): 포스트 HTML 내용
            status (str): 게시 상태 (draft, publish, private 등)
            categories (list): 카테고리 ID 리스트
            tags (list): 태그 ID 리스트
            featured_media_id (int): 썸네일(특성 이미지) ID
            meta_input (dict): 메타데이터 (Rank Math 필드 포함)
            slug (str): 영문 슬러그 (URL 고유명)
            
        Returns:
            Optional[str]: 생성된 포스트의 URL
        """
        endpoint = f"{self.base_url}/posts"
        
        data = {
            "title": title,
            "content": content,
            "status": status,
        }
        
        # 슬러그 명시 (한글 자동 변환 방지)
        if slug:
            data["slug"] = slug
        
        if categories:
            data["categories"] = categories
        if tags:
            data["tags"] = tags
        if featured_media_id:
            data["featured_media"] = featured_media_id
        if meta_input:
            data["meta"] = meta_input

        try:
            logger.info(f"포스트 생성 시도: {title}")
            response = requests.post(endpoint, auth=self.auth, json=data)
            response.raise_for_status()
            
            result = response.json()
            post_link = result.get("link")
            logger.info(f"포스트 생성 성공! Link: {post_link}")
            return post_link

        except Exception as e:
            logger.error(f"포스트 생성 실패: {e}")
            if 'response' in locals() and response.status_code != 200:
                logger.error(f"응답 내용: {response.text}")
            return None

    def get_user_info(self):
        """
        연결 테스트 용: 현재 사용자 정보를 가져옵니다.
        """
        endpoint = f"{self.base_url}/users/me"
        try:
            response = requests.get(endpoint, auth=self.auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"사용자 정보 조회 실패 (연결 테스트 실패): {e}")
            return None

    def get_post(self, post_id: int) -> Optional[Dict[str, Any]]:
        """
        포스트 ID로 포스트 정보를 조회합니다. (디버깅용)
        """
        endpoint = f"{self.base_url}/posts/{post_id}"
        try:
            response = requests.get(endpoint, auth=self.auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"포스트 조회 실패 ({post_id}): {e}")
            return None

    def get_recent_posts(self, count: int = 5) -> list:
        """
        최신 포스트 목록을 가져옵니다. (내부 링크용)
        
        Args:
            count (int): 가져올 포스트 개수
            
        Returns:
            list: [{'id': int, 'title': str, 'link': str}, ...]
        """
        endpoint = f"{self.base_url}/posts"
        params = {
            "per_page": count,
            "status": "publish", # 발행된 글만
            "_fields": "id,title,link" # 필요한 필드만 조회
        }
        
        try:
            response = requests.get(endpoint, auth=self.auth, params=params)
            response.raise_for_status()
            posts = response.json()
            
            result = []
            for p in posts:
                result.append({
                    "id": p['id'],
                    "title": p['title']['rendered'],
                    "link": p['link']
                })
            return result

        except Exception as e:
            logger.error(f"최신 포스트 조회 실패: {e}")
            return []

    def get_or_create_tags(self, tag_names: list) -> list:
        """
        태그 이름 리스트를 받아 ID 리스트로 반환합니다.
        없는 태그는 생성합니다.
        
        Args:
            tag_names (list): 태그 이름 문자열 리스트
            
        Returns:
            list: 태그 ID 정수 리스트
        """
        if not tag_names:
            return []
            
        tag_ids = []
        for name in tag_names:
            try:
                # 1. 태그 조회
                slug = name.strip().replace(" ", "-").lower() # 간단한 슬러그 변환
                search_endpoint = f"{self.base_url}/tags?search={name}"
                response = requests.get(search_endpoint, auth=self.auth)
                response.raise_for_status()
                existing_tags = response.json()
                
                found = False
                for tag in existing_tags:
                    if tag['name'].lower() == name.lower():
                        tag_ids.append(tag['id'])
                        found = True
                        break
                
                if found:
                    continue

                # 2. 태그 생성 (없을 경우)
                create_endpoint = f"{self.base_url}/tags"
                data = {"name": name}
                create_response = requests.post(create_endpoint, auth=self.auth, json=data)
                create_response.raise_for_status()
                new_tag = create_response.json()
                tag_ids.append(new_tag['id'])
                logger.info(f"새 태그 생성: {name} (ID: {new_tag['id']})")

            except Exception as e:
                logger.error(f"태그 처리 실패 ({name}): {e}")
                
        return tag_ids
