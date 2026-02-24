from src.core.generator import ContentGenerator

html_snippet = """
    <p>이것은 유효한 링크입니다: <a href="https://www.google.com" target="_blank">구글</a></p>
    <p>이것은 내부 링크입니다: <a href="https://smart-work-solution.com/abc" target="_blank">내부</a></p>
    <p>이것은 404 에러 링크입니다: <a href="https://www.google.com/this-page-does-not-exist-12345" target="_blank">없는 페이지</a></p>
"""

cg = ContentGenerator()
fixed_html = cg._validate_and_fix_external_links(html_snippet, ["https://smart-work-solution.com"])

print("--- ORIGINAL ---")
print(html_snippet)
print("--- FIXED ---")
print(fixed_html)
