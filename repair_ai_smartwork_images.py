
import os
import re
from src.config.settings import Config
from src.core.image_processor import ImageProcessor
from src.core.wp_client import WordPressClient
from src.utils.logger import get_logger

# Logger
logger = get_logger("RepairImages")

def main():
    Config.validate()
    
    # Initialize Clients
    img_processor = ImageProcessor()
    wp_client = WordPressClient()
    
    POST_ID = 745
    
    # 1. Fetch Post Content
    print(f"📥 Fetching Post {POST_ID}...")
    post = wp_client.get_post(POST_ID)
    if not post:
        print("❌ Post not found!")
        return

    title = post['title']['rendered']
    content = post['content']['rendered']
    
    # Extract Sections (H2) for body image context
    # Regex to find text inside <h2>...</h2>
    # Note: Content might have attributes like <h2 class="...">
    h2_matches = re.findall(r'<h2.*?>(.*?)</h2>', content)
    
    print(f"📌 Title: {title}")
    print(f"📌 Found {len(h2_matches)} H2 sections.")
    
    # Needs: 1 Thumbnail + 3 Body Images
    # Strategy:
    # Thumb: Based on Title
    # Body 1: Based on H2 #1 (Concept/Intro)
    # Body 2: Based on H2 #3 (Strategy/Method) - mid point
    # Body 3: Based on H2 #5 or last (Future/Conclusion)
    
    # Safe fallback if not enough H2s
    h2_1 = h2_matches[0] if len(h2_matches) > 0 else "Smart Work Concept"
    h2_2 = h2_matches[len(h2_matches)//2] if len(h2_matches) > 1 else "Automation Strategy"
    h2_3 = h2_matches[-2] if len(h2_matches) > 2 else "Future of Work"
    
    # Define Image Tasks
    images_to_generate = [
        {
            "type": "featured",
            "prompt": f"Concept art for '{title}'. Futuristic, highly detailed, isometric 3D style, bright and professional colors. Representing AI automation and financial growth for one-person business.",
            "filename": "ai-smartwork-2026-thumb.webp",
            "caption": "AI 스마트워크로 만드는 1인 기업의 미래",
            "alt": f"{title} 대표 이미지"
        },
        {
            "type": "body",
            "prompt": f"Illustration for '{h2_1}'. Minimalist vector art, infographic style. Showing workflow efficiency and AI tools.",
            "filename": "ai-smartwork-2026-body-1.webp",
            "caption": "스마트워크의 핵심: 효율성과 자동화",
            "alt": f"{h2_1} 설명 이미지",
            "insert_after_h2_index": 0 # Insert after 1st H2
        },
        {
            "type": "body",
            "prompt": f"Illustration for '{h2_2}'. Data visualization style, isometric. Showing revenue growth charts and automated systems working.",
            "filename": "ai-smartwork-2026-body-2.webp",
            "caption": "수익화 자동화 시스템 구조도",
            "alt": f"{h2_2} 설명 이미지",
            "insert_after_h2_index": 2 # Insert after 3rd H2 (approx)
        },
        {
            "type": "body",
            "prompt": f"Illustration for '{h2_3}'. Visionary style, futuristic office with AI assistants. Bright and hopeful atmosphere.",
            "filename": "ai-smartwork-2026-body-3.webp",
            "caption": "2026년 1인 기업의 진화된 업무 환경",
            "alt": f"{h2_3} 설명 이미지",
            "insert_after_h2_index": 5 # Insert after 6th H2 (approx)
        }
    ]
    
    generated_media_ids = {} # { type_index: media_id }
    
    # 2. Generate & Upload Images
    print("\n🎨 Generating and Uploading Images...")
    
    for idx, img_task in enumerate(images_to_generate):
        print(f"   [{idx+1}/4] Processing: {img_task['type']} - {img_task['filename']}")
        
        # A. Generate
        local_path = img_processor.generate_image(img_task['prompt'], img_task['filename'])
        if not local_path:
            print("   ❌ Generation Failed. Skipping.")
            continue
            
        # B. Upload
        media_info = wp_client.upload_image(
            image_path=local_path,
            caption=img_task['caption'],
            title=img_task['alt'], # Title same as alt for convenience
            alt_text=img_task['alt'],
            description=img_task['prompt']
        )
        
        if media_info:
            print(f"   ✅ Uploaded ID: {media_info['id']}")
            img_task['media_id'] = media_info['id']
            img_task['source_url'] = media_info['source_url']
        else:
            print("   ❌ Upload Failed.")

    # 3. Update Post Content
    print("\n📝 Updating Post Content...")
    
    # A. Featured Image
    featured_img = next((img for img in images_to_generate if img['type'] == 'featured'), None)
    if featured_img and 'media_id' in featured_img:
        # Update featured media
        wp_client.update_post(POST_ID, {"featured_media": featured_img['media_id']})
        print(f"   ✅ Featured Image Set (ID: {featured_img['media_id']})")
        
    # B. Insert Body Images
    # Split content by H2 headers to insert images safely
    # This is a bit tricky with Regex split, so we'll do a simple find/replace strategy or split reconstruction
    
    # Reconstruction Strategy:
    # 1. Split by </h2> because it's the end of a header
    # 2. Re-assemble and inject images at targeted indices
    
    parts = re.split(r'(</h2>)', content)
    # parts will look like: ['...text...<h2...>', '</h2>', '...text...', '</h2>'...]
    
    new_content = ""
    h2_counter = 0
    
    body_images = [img for img in images_to_generate if img['type'] == 'body' and 'media_id' in img]
    body_imgs_map = {img['insert_after_h2_index']: img for img in body_images}
    
    for i in range(0, len(parts)):
        part = parts[i]
        new_content += part
        
        if part == "</h2>":
            # We just closed an H2, check if we need to insert an image here
            current_h2_idx = h2_counter
            
            # Check if an image is scheduled for this index
            # Logic: We mapped 'insert_after_h2_index' to specific H2 counts
            # But we should be flexible. If exact index match, insert.
            
            if current_h2_idx in body_imgs_map:
                img = body_imgs_map[current_h2_idx]
                
                # Gutenberg Image Block HTML
                block_html = (
                    f'\n\n<!-- wp:image {{"id":{img["media_id"]},"sizeSlug":"large","linkDestination":"none"}} -->\n'
                    f'<figure class="wp-block-image size-large">'
                    f'<img src="{img["source_url"]}" alt="{img["alt"]}" class="wp-image-{img["media_id"]}"/>'
                    f'<figcaption>{img["caption"]}</figcaption>'
                    f'</figure>\n'
                    f'<!-- /wp:image -->\n\n'
                )
                new_content += block_html
                print(f"   -> Inserted Body Image after H2 #{current_h2_idx+1}")
            
            h2_counter += 1

    # If new_content is same (no insertions happened?), warning
    if new_content == content and len(body_images) > 0:
        print("⚠️ Warning: No body images were inserted (regex split mismatch?). Appending to bottom for safety.")
        for img in body_images:
             block_html = (
                    f'\n\n<!-- wp:image {{"id":{img["media_id"]},"sizeSlug":"large","linkDestination":"none"}} -->\n'
                    f'<figure class="wp-block-image size-large">'
                    f'<img src="{img["source_url"]}" alt="{img["alt"]}" class="wp-image-{img["media_id"]}"/>'
                    f'<figcaption>{img["caption"]}</figcaption>'
                    f'</figure>\n'
                    f'<!-- /wp:image -->\n\n'
                )
             new_content += block_html

    # Final Update
    res = wp_client.update_post(POST_ID, {"content": new_content})
    if res:
        print("✨ Post Content Updated Successfully!")
    else:
        print("❌ Failed to update post content.")

if __name__ == "__main__":
    main()
