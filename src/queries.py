# src/queries.py

# AI 규제 뉴스 센싱을 위한 쿼리 (최근 3일)
# 키워드: AI copyright, AI governance, AI regulation, AI 거버넌스, AI 저작권, AI 규제, AI 기본법, EU AI Act
NEWS_QUERIES = [
    '("AI regulation" OR "AI governance" OR "AI Act" OR "AI policy") when:3d',
    '("AI copyright" OR "AI intellectual property" OR "AI copyright regulation") when:3d',
    '("AI 규제" OR "AI 거버넌스" OR "AI 기본법" OR "AI 가이드라인") when:3d',
    '("EU AI Act" OR "AI legal framework" OR "AI safety summit") when:3d',
    '("AI 저작권" OR "AI 책임법" OR "AI 윤리 가이드라인") when:3d',
]
