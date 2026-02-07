from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import GetPost, EditPost
from src.config.settings import Config

# XML-RPC 설정
wp_url = f"{Config.WP_URL.rstrip('/')}/xmlrpc.php"
username = Config.WP_USERNAME
password = Config.WP_PASSWORD
post_id = 579

def update_post_meta_xmlrpc():
    try:
        client = Client(wp_url, username, password)
        post = client.call(GetPost(post_id))
        
        # 커스텀 필드 설정 (Rank Math 키워드)
        post.custom_fields = [
            {'key': 'rank_math_focus_keyword', 'value': 'TEST_KEYWORD_XMLRPC'},
            {'key': 'rank_math_description', 'value': 'TEST_DESCRIPTION_XMLRPC'}
        ]
        
        result = client.call(EditPost(post_id, post))
        
        print(f"XML-RPC Update Result: {result}")
        
        # 확인을 위해 다시 조회
        updated_post = client.call(GetPost(post_id))
        print("Updated Custom Fields:")
        for field in updated_post.custom_fields:
            if 'rank_math' in field['key']:
                print(f"Key: {field['key']}, Value: {field['value']}")

    except Exception as e:
        print(f"XML-RPC Error: {e}")

if __name__ == "__main__":
    update_post_meta_xmlrpc()
