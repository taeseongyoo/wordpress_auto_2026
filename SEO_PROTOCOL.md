# WordPress SEO Automation Protocol (Verified 2026-02-10)

> [!IMPORTANT]
> **PROTOCOL LOCKED**: This configuration achieved a **Rank Math Score of 87** (Excellent).
> Do not modify the core logic below without explicit approval.

## 📌 Core Principles

This document outlines the verified strategy for generating high-quality, SEO-optimized blog posts using the `wordpress_auto_2026` system.

### 1. Keyword Strategy

- **Main Keyword**: 1 Focus Keyword (Rank Math Meta Field).
- **Related Keywords**: 8 LSI Keywords generated and naturally woven into the content.
- **Protocol**:
  - Focus Keyword Field: **ONLY** the Main Keyword.
  - Content: Must naturally include related keywords.

### 2. Content Quality & Quantity

- **Length**: Minimum **2,000 characters** (Actual results: ~9,000-10,000 chars).
- **Structure**: 6~8 H2 Sections + Intro + Conclusion + FAQ.
- **Readability**: Short paragraphs (2-3 sentences), Bullet points, Bold highlights.

### 3. Visual Strategy

- **Quantity**: Minimum **4 Images** (1 Thumbnail + 3 Body Images).
- **Placement**:
  - Thumbnail: Before Title.
  - Body Images: After H2 headers (distributed evenly).
- **Metadata**: All images must have Alt Text and Captions containing the Focus Keyword.

### 4. Linking Strategy

- **Internal Links**: Fetch 5 recent posts and distribute them throughout the content and in a "Related Posts" section at the bottom.
- **External Links**: 1-3 high-authority links (Gov, Big Tech, Statistics) per post.

## ✅ Verified Code Logic

The following logic has been "memorized" in `src/main.py` and `src/core/generator.py`:

```python
# [Verified] Rank Math Focus Keyword
rank_math_focus_keyword = focus_keyword # Single Keyword Only

# [Verified] Image Generation
images needed >= 4

# [Verified] Content Validation
content length >= 2000 chars
```

### 5. AI Smart Work Strategy (New 2026.02.12)

- **Category**: `AI 스마트워크 & 수익화` (ID: **86**)
- **Tags**: 8 Fixed Tags (Refer to PROGRESS.md).
- **Image Protocol**:
  - **Style**: Futuristic, Isometric 3D, No Text.
  - **Alt Text**: Must include Focus Keyword + Description (No HTML).
- **Link Protocol (Walled Garden)**:
  - **External**: Minimum **5** High-Authority Links (Google, AWS, Gov, etc.).
  - **Internal**: Minimum **5** Contextual Links (Chain Strategy).

## 🏆 Success Benchmarks

- **Post 1 (Blog Monetization)**: Success
- **Post 2 (YouTube Monetization)**: Success (Score 87)
- **Post 3 (AI Smart Work)**: Success (Post ID 745)

## 📜 Version History & Roadmap

### v1.2 (Updated - 2026.02.12)

- **AI Smart Work**: Added dedicated category and tag protocol.
- **Image Alt Text**: Strict rule to strip HTML tags and include Focus Keyword.

### v1.1 (Stable - 2026.02.10)

- **Rank Math Score**: **87** (Achieved without manual English slug optimization).
- **Tags**: 8 Auto-generated tags per post.
- **Links**:
  - External: 5+ High-authority links (Gov, Tech Giants).
  - Internal: 3+ Contextual links + Related Posts section.
- **Components**:
  - Clickable FAQ (HTML `<details>`).
  - DALL-E 3 Image Generation (1024x1024, WebP).

### 🚀 Future Roadmap (Tier 2 Upgrade)

- **Image Generation**: Switch to **Midjourney** (via NanoBanana Pro API) for higher artistic quality.
- **SEO**:
  - Automated English Slug Translation.
  - JSON-LD Schema Auto-injection.
