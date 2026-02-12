import os
import sys
import re
from src.core.wp_client import WordPressClient
from src.utils.logger import get_logger

logger = get_logger("UpdatePost1_V2")

POST_ID = 778
LINKS_TO_ADD = [
    {"title": "청년도약계좌 신청 가이드", "link": "https://smart-work-solution.com/youth-future-savings-2026-application/"},
    {"title": "청년미래적금 혜택 비교", "link": "https://smart-work-solution.com/youth-future-savings-vs-leap-account-2026/"},
    {"title": "AI 수익화 전략", "link": "https://smart-work-solution.com/ai-ebook-monetization-2026/"},
    {"title": "AI 유튜브 채널 만들기", "link": "https://smart-work-solution.com/ai-youtube-monetization-2026/"},
    {"title": "정부지원금 통합 조회(홈)", "link": "https://smart-work-solution.com/"} 
]

def update_post_links_v2():
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
    <div class="internal-links-box" style="margin: 30px 0; padding: 25px; background-color: #f0f7fb; border-left: 5px solid #0073aa; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <h3 style="margin-top: 0; font-size: 1.2em; color: #0073aa;">💡 함께 보면 좋은 정부지원 정책</h3>
        <ul style="margin-bottom: 0; padding-left: 20px;">
    """
    for link in LINKS_TO_ADD:
        link_html += f"        <li style='margin-bottom: 8px;'><a href='{link['link']}' target='_blank' rel='dofollow' style='text-decoration: none; color: #333; font-weight: bold; border-bottom: 1px solid #ddd;'>{link['title']}</a></li>\n"
    link_html += "    </ul></div>"

    # 3. Insert Strategy: Try to insert after the first H2 (Introduction)
    # If H2 doesn't exist, failover to prepend to content.
    
    if "</h2>" in content:
        # Split by first instance of </h2>
        parts = content.split("</h2>", 1) # Split only on first occurrence
        new_content = parts[0] + "</h2>\n\n" + link_html + "\n\n" + parts[1]
        logger.info("Inserted links after the first H2 tag.")
    else:
        # Fallback: Prepend (user wants to see them!)
        new_content = link_html + "\n\n" + content
        logger.info("No H2 found. Prepended links to top.")

    # 4. Update Post
    res = client.update_post(POST_ID, {"content": new_content})
    if res:
        logger.info(f"✅ Post {POST_ID} re-updated with visible internal links.")
    else:
        logger.error(f"❌ Failed to update Post {POST_ID}")

if __name__ == "__main__":
    update_post_links_v2()
