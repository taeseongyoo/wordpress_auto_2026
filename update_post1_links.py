import os
import sys
from src.core.wp_client import WordPressClient
from src.utils.logger import get_logger

logger = get_logger("UpdatePost1")

# Target Post: ID 778 (Post 1)
POST_ID = 778
LINKS_TO_ADD = [
    {"title": "청년도약계좌 신청 가이드", "link": "https://smart-work-solution.com/youth-future-savings-2026-application/"},
    {"title": "청년미래적금 혜택 비교", "link": "https://smart-work-solution.com/youth-future-savings-vs-leap-account-2026/"},
    {"title": "AI 수익화 전략", "link": "https://smart-work-solution.com/ai-ebook-monetization-2026/"},
    {"title": "AI 유튜브 채널 만들기", "link": "https://smart-work-solution.com/ai-youtube-monetization-2026/"},
    {"title": "정부지원금 통합 조회(홈)", "link": "https://smart-work-solution.com/"} 
]

def update_post_links():
    client = WordPressClient()
    
    # 1. Get current content
    post = client.get_post(POST_ID)
    if not post:
        logger.error(f"Post {POST_ID} not found.")
        return

    content = post['content']['rendered']
    logger.info(f"Original Content Length: {len(content)}")

    # 2. Creating the Link Section HTML
    link_html = """
    <div class="internal-links" style="margin: 30px 0; padding: 20px; background-color: #f0f7fb; border-left: 5px solid #0073aa; border-radius: 4px;">
        <h3 style="margin-top: 0; font-size: 1.2em;">💡 함께 보면 좋은 정부지원 정책</h3>
        <ul style="margin-bottom: 0;">
    """
    for link in LINKS_TO_ADD:
        link_html += f"        <li style='margin-bottom: 8px;'><a href='{link['link']}' target='_blank' rel='dofollow' style='text-decoration: none; color: #0073aa; font-weight: bold;'>{link['title']}</a></li>\n"
    link_html += "    </ul></div>"

    # 3. Append to content (before FAQ or at end)
    # If standard generator format, it often ends with FAQ. We can put it before that or just at the very end.
    # Let's put it before the conclusion or FAQ if possible, otherwise append.
    
    if "<h2>자주 묻는 질문" in content:
        parts = content.split("<h2>자주 묻는 질문")
        new_content = parts[0] + link_html + "\n\n<h2>자주 묻는 질문" + parts[1]
    else:
        new_content = content + "\n\n" + link_html

    # 4. Update Post
    res = client.update_post(POST_ID, {"content": new_content})
    if res:
        logger.info(f"✅ Post {POST_ID} updated with {len(LINKS_TO_ADD)} internal links.")
    else:
        logger.error(f"❌ Failed to update Post {POST_ID}")

if __name__ == "__main__":
    update_post_links()
