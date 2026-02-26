from __future__ import annotations
import re
import requests
import yaml
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from .utils import debug_log

@dataclass
class RegulationInfo:
    update_or_filed_date: str
    country: str  # 추가: 규제 대상 국가
    # case_title: 법안/규제명 또는 관련 기관/국가
    case_title: str
    # article_title: RSS/기사 원문 제목
    article_title: str
    case_number: str
    reason: str
    article_urls: List[str]
    matched_keywords: str = ""


def fetch_page_text(url: str, timeout: int = 15) -> tuple[str, str]:
    """기사 페이지 텍스트를 가져오고 (텍스트, 최종URL)을 반환한다."""
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
        r.raise_for_status()
        final_url = (r.url or url).strip()
        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text[:20000], final_url
    except Exception as e:
        debug_log(f"fetch_page_text failed: {url}, error: {e}")
        return "", url

def load_known_cases(path: str = "data/known_cases.yml") -> List[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or []
    except FileNotFoundError:
        return []

def enrich_from_known(text: str, title: str, known: List[Dict[str, Any]]) -> Dict[str, str]:
    hay = (title + "\n" + text).lower()
    for entry in known:
        any_terms = [t.lower() for t in entry.get("match", {}).get("any", [])]
        if any_terms and any(term in hay for term in any_terms):
            return entry.get("enrich", {}) or {}
    return {}

def extract_country(text: str, title: str) -> str:
    """본문 또는 제목에서 국가 정보를 추정한다."""
    text_to_search = (title + " " + text).lower()
    
    mapping = {
        "Ascension and Tristan da Cunha": ["Ascension and Tristan da Cunha", "saint helena"],
        "EU": ["eu ", "european union", "유럽연합", "브뤼셀", "유럽"],
        "가나": ["ghana", "가나"],
        "가봉": ["gabon", "가봉"],
        "가이아나": ["guyana", "가이아나"],
        "감비아": ["gambia", "감비아"],
        "건지": ["guernsey", "건지"],
        "과들루프": ["guadeloupe", "과들루프"],
        "과테말라": ["guatemala", "과테말라"],
        "괌": ["guam", "괌"],
        "그레나다": ["grenada", "그레나다"],
        "그리스": ["greece", "그리스"],
        "그린란드": ["greenland", "그린란드"],
        "글로벌": ["global", "international", "글로벌", "국제"],
        "기니": ["guinea", "기니"],
        "기니비사우": ["guinea-bissau", "기니비사우"],
        "나미비아": ["namibia", "나미비아"],
        "나우루": ["nauru", "나우루"],
        "나이지리아": ["nigeria", "나이지리아"],
        "남수단": ["south sudan", "남수단"],
        "남아프리카 공화국": ["south africa", "남아프리카 공화국"],
        "네덜란드": ["netherlands", "네덜란드"],
        "네팔": ["nepal", "네팔"],
        "노르웨이": ["norway", "노르웨이"],
        "노퍽 섬": ["norfolk island", "노퍽 섬"],
        "누벨칼레도니": ["new caledonia", "누벨칼레도니"],
        "뉴질랜드": ["new zealand", "뉴질랜드"],
        "니우에": ["niue", "니우에"],
        "니제르": ["niger", "니제르"],
        "니카라과": ["nicaragua", "니카라과"],
        "대만": ["taiwan", "대만"],
        "대한민국": ["korea", "republic of korea", "south korea", "대한민국", "한국"],
        "덴마크": ["denmark", "덴마크"],
        "도미니카": ["dominica", "도미니카"],
        "도미니카 공화국": ["dominican republic", "도미니카 공화국"],
        "독일": ["germany", "독일", "베를린"],
        "동티모르": ["timor-leste", "동티모르"],
        "라오스": ["laos", "라오스"],
        "라이베리아": ["liberia", "라이베리아"],
        "라트비아": ["latvia", "라트비아"],
        "러시아": ["russia", "러시아"],
        "레바논": ["lebanon", "레바논"],
        "레소토": ["lesotho", "레소토"],
        "레위니옹": ["réunion", "레위니옹"],
        "루마니아": ["romania", "루마니아"],
        "룩셈부르크": ["luxembourg", "룩셈부르크"],
        "르완다": ["rwanda", "르완다"],
        "리비아": ["libya", "리비아"],
        "리투아니아": ["lithuania", "리투아니아"],
        "리히텐슈타인": ["liechtenstein", "리히텐슈타인"],
        "마다가스카르": ["madagascar", "마다가스카르"],
        "마르티니크": ["martinique", "마르티니크"],
        "마셜 제도": ["marshall islands", "마셜 제도"],
        "마요트": ["mayotte", "마요트"],
        "마카오": ["macau", "마카오"],
        "말라위": ["malawi", "말라위"],
        "말레이시아": ["malaysia", "말레이시아"],
        "말리": ["mali", "말리"],
        "맨 섬": ["isle of man", "맨 섬"],
        "멕시코": ["mexico", "멕시코"],
        "모나코": ["monaco", "모나코"],
        "모로코": ["morocco", "모로코"],
        "모리셔스": ["mauritius", "모리셔스"],
        "모리타니": ["mauritania", "모리타니"],
        "모잠비크": ["mozambique", "모잠비크"],
        "몬테네그로": ["montenegro", "몬테네그로"],
        "몬트세랫": ["montserrat", "몬트세랫"],
        "몰도바": ["moldova", "몰도바"],
        "몰디브": ["maldives", "몰디브"],
        "몰타": ["malta", "몰타"],
        "몽골": ["mongolia", "몽골"],
        "미국": ["u.s.", "u.s.a", "united states", "usa", "미 연방", "미국"],
        "미얀마": ["myanmar (burma)", "미얀마"],
        "미크로네시아": ["micronesia", "미크로네시아"],
        "바누아투": ["vanuatu", "바누아투"],
        "바레인": ["bahrain", "바레인"],
        "바베이도스": ["barbados", "바베이도스"],
        "바티칸 시국": ["vatican city (holy see)", "바티칸 시국"],
        "바하마": ["bahamas", "바하마"],
        "방글라데시": ["bangladesh", "방글라데시"],
        "버뮤다": ["bermuda", "버뮤다"],
        "베냉": ["benin", "베냉"],
        "베네수엘라": ["venezuela", "베네수엘라"],
        "베트남": ["vietnam", "베트남"],
        "벨기에": ["belgium", "벨기에"],
        "벨라루스": ["belarus", "벨라루스"],
        "벨리즈": ["belize", "벨리즈"],
        "보네르": ["bonaire", "보네르"],
        "보스니아 헤르체고비나": ["bosnia and herzegovina", "보스니아 헤르체고비나"],
        "보츠와나": ["botswana", "보츠와나"],
        "볼리비아": ["bolivia", "볼리비아"],
        "부룬디": ["burundi", "부룬디"],
        "부르키나파소": ["burkina faso", "부르키나파소"],
        "부베 섬": ["bouvet island", "부베 섬"],
        "부탄": ["bhutan", "부탄"],
        "북마케도니아": ["north macedonia", "북마케도니아"],
        "북한": ["north korea", "북한"],
        "불가리아": ["bulgaria", "불가리아"],
        "브라질": ["brazil", "브라질"],
        "브루나이": ["brunei darussalam", "브루나이"],
        "사모아": ["samoa", "사모아"],
        "사우디아라비아": ["saudi arabia", "사우디아라비아"],
        "산마리노": ["san marino", "산마리노"],
        "상투메 프린시페": ["sao tome and principe", "상투메 프린시페"],
        "생마르탱": ["saint martin (french part)", "생마르탱"],
        "생바르텔레미": ["saint barthélemy", "생바르텔레미"],
        "생피에르 미클롱": ["saint pierre and miquelon", "생피에르 미클롱"],
        "서사하라": ["western sahara", "서사하라"],
        "세네갈": ["senegal", "세네갈"],
        "세르비아": ["serbia", "세르비아"],
        "세이셸": ["seychelles", "세이셸"],
        "세인트루시아": ["saint lucia", "세인트루시아"],
        "세인트빈센트 그레나딘": ["saint vincent and the grenadines", "세인트빈센트 그레나딘"],
        "세인트키츠 네비스": ["saint kitts and nevis", "세인트키츠 네비스"],
        "소말리아": ["somalia", "소말리아"],
        "솔로몬 제도": ["solomon islands", "솔로몬 제도"],
        "수단": ["sudan", "수단"],
        "수리남": ["suriname", "수리남"],
        "스리랑카": ["sri lanka", "스리랑카"],
        "스웨덴": ["sweden", "스웨덴"],
        "스위스": ["switzerland", "스위스"],
        "스페인": ["spain", "스페인"],
        "슬로바키아": ["slovakia", "슬로바키아"],
        "슬로베니아": ["slovenia", "슬로베니아"],
        "시리아": ["syria", "시리아"],
        "시에라리온": ["sierra leone", "시에라리온"],
        "신트마르턴": ["sint maarten (dutch part)", "신트마르턴"],
        "싱가포르": ["singapore", "싱가포르"],
        "아랍에미리트": ["united arab emirates", "아랍에미리트"],
        "아루바": ["aruba", "아루바"],
        "아르메니아": ["armenia", "아르메니아"],
        "아르헨티나": ["argentina", "아르헨티나"],
        "아메리칸사모아": ["american samoa", "아메리칸사모아"],
        "아이슬란드": ["iceland", "아이슬란드"],
        "아이티": ["haiti", "아이티"],
        "아일랜드": ["ireland", "아일랜드"],
        "아제르바이잔": ["azerbaijan", "아제르바이잔"],
        "아프가니스탄": ["afghanistan", "아프가니스탄"],
        "안도라": ["andorra", "안도라"],
        "알바니아": ["albania", "알바니아"],
        "알제리": ["algeria", "알제리"],
        "앙골라": ["angola", "앙골라"],
        "앤티가 바부다": ["antigua and barbuda", "앤티가 바부다"],
        "앵귈라": ["anguilla", "앵귈라"],
        "어센션 섬": ["ascension island", "어센션 섬"],
        "에리트레아": ["eritrea", "에리트레아"],
        "에스와티니": ["eswatini", "에스와티니"],
        "에스토니아": ["estonia", "에스토니아"],
        "에콰도르": ["ecuador", "에콰도르"],
        "에티오피아": ["ethiopia", "에티오피아"],
        "엘살바도르": ["el salvador", "엘살바도르"],
        "영국": ["uk ", "united kingdom", "런던", "영국"],
        "영국령 버진아일랜드": ["british virgin islands", "영국령 버진아일랜드"],
        "영국령 인도양 식민지": ["british indian ocean territory", "영국령 인도양 식민지"],
        "예멘": ["yemen", "예멘"],
        "오만": ["oman", "오만"],
        "오스트레일리아": ["australia", "오스트레일리아"],
        "오스트리아": ["austria", "오스트리아"],
        "온두라스": ["honduras", "온두라스"],
        "올란드 제도": ["åland islands", "올란드 제도"],
        "왈리스 푸투나": ["wallis and futuna", "왈리스 푸투나"],
        "요르단": ["jordan", "요르단"],
        "우간다": ["uganda", "우간다"],
        "우루과이": ["uruguay", "우루과이"],
        "우즈베키스탄": ["uzbekistan", "우즈베키스탄"],
        "우크라이나": ["ukraine", "우크라이나"],
        "이라크": ["iraq", "이라크"],
        "이란": ["iran", "이란"],
        "이스라엘": ["israel", "이스라엘"],
        "이집트": ["egypt", "이집트"],
        "이탈리아": ["italy", "이탈리아"],
        "인도": ["india", "인도"],
        "인도네시아": ["indonesia", "인도네시아"],
        "일본": ["japan", "도쿄", "일본"],
        "자메이카": ["jamaica", "자메이카"],
        "잠비아": ["zambia", "잠비아"],
        "저지": ["jersey", "저지"],
        "적도 기니": ["equatorial guinea", "적도 기니"],
        "조지아": ["georgia", "조지아"],
        "중국": ["china", "베이징", "중국"],
        "중앙아프리카 공화국": ["central african republic", "중앙아프리카 공화국"],
        "지부티": ["djibouti", "지부티"],
        "지브롤터": ["gibraltar", "지브롤터"],
        "짐바브웨": ["zimbabwe", "짐바브웨"],
        "차드": ["chad", "차드"],
        "체코": ["czech republic", "체코"],
        "칠레": ["chile", "칠레"],
        "카메룬": ["cameroon", "카메룬"],
        "카보베르데": ["cape verde", "카보베르데"],
        "카자흐스탄": ["kazakhstan", "카자흐스탄"],
        "카타르": ["qatar", "카타르"],
        "캄보디아": ["cambodia", "캄보디아"],
        "캐나다": ["canada", "캐나다"],
        "케냐": ["kenya", "케냐"],
        "케이맨제도": ["cayman islands", "케이맨제도"],
        "코모로": ["comoros", "코모로"],
        "코스타리카": ["costa rica", "코스타리카"],
        "코코스 제도": ["cocos (keeling) islands", "코코스 제도"],
        "코트디부아르": ["ivory coast (côte d'ivoire)", "코트디부아르"],
        "콜롬비아": ["colombia", "콜롬비아"],
        "콩고 공화국": ["congo (republic)", "콩고 공화국"],
        "콩고 민주 공화국": ["congo (democratic republic of)", "콩고 민주 공화국"],
        "쿠바": ["cuba", "쿠바"],
        "쿠웨이트": ["kuwait", "쿠웨이트"],
        "쿡 제도": ["cook islands", "쿡 제도"],
        "퀴라소": ["curaçao", "퀴라소"],
        "크로아티아": ["croatia", "크로아티아"],
        "크리스마스 섬": ["christmas island", "크리스마스 섬"],
        "키르기스스탄": ["kyrgyzstan", "키르기스스탄"],
        "키리바시": ["kiribati", "키리바시"],
        "키프로스": ["cyprus", "키프로스"],
        "타지키스탄": ["tajikistan", "타지키스탄"],
        "탄자니아": ["tanzania", "탄자니아"],
        "태국": ["thailand", "태국"],
        "터크스 케이커스 제도": ["turks and caicos islands", "터크스 케이커스 제도"],
        "토고": ["togo", "토고"],
        "토켈라우": ["tokelau", "토켈라우"],
        "통가": ["tonga", "통가"],
        "투르크메니스탄": ["turkmenistan", "투르크메니스탄"],
        "투발루": ["tuvalu", "투발루"],
        "튀니지": ["tunisia", "튀니지"],
        "튀르키예": ["turkey", "튀르키예"],
        "트리니다드 토바고": ["trinidad and tobago", "트리니다드 토바고"],
        "파나마": ["panama", "파나마"],
        "파라과이": ["paraguay", "파라과이"],
        "파키스탄": ["pakistan", "파키스탄"],
        "파푸아뉴기니": ["papua new guinea", "파푸아뉴기니"],
        "팔라우": ["palau", "팔라우"],
        "팔레스타인": ["palestine", "팔레스타인"],
        "페로 제도": ["faroe islands", "페로 제도"],
        "페루": ["peru", "페루"],
        "포르투갈": ["portugal", "포르투갈"],
        "포클랜드 제도": ["falkland islands", "포클랜드 제도"],
        "폴란드": ["poland", "폴란드"],
        "푸에르토리코": ["puerto rico", "푸에르토리코"],
        "프랑스": ["france", "파리", "프랑스"],
        "프랑스령 기아나": ["french guiana", "프랑스령 기아나"],
        "프랑스령 폴리네시아": ["french polynesia", "프랑스령 폴리네시아"],
        "피지": ["fiji", "피지"],
        "핀란드": ["finland", "핀란드"],
        "필리핀": ["philippines", "필리핀"],
        "핏케언 제도": ["pitcairn islands", "핏케언 제도"],
        "헝가리": ["hungary", "헝가리"],
        "홍콩": ["hong kong", "홍콩"]
    }

    
    for country, keywords in mapping.items():
        if any(k in text_to_search for k in keywords):
            return country
            
    return "기타"

def extract_regulation_subject(text: str, title: str) -> str:
    """본문 또는 제목에서 규제 대상(국가, 법안명 등)을 추정한다."""
    text_to_search = (title + " " + text).lower()
    
    if "eu ai act" in text_to_search or "유럽연합" in text_to_search or "european union" in text_to_search:
        return "EU AI Act"
    if "기본법" in text_to_search or "대한민국" in text_to_search or "korea" in text_to_search:
        return "AI 기본법 (KR)"
    if "copyright" in text_to_search or "저작권" in text_to_search:
        return "AI 저작권 가이드라인"
    if "california" in text_to_search or "sb 1047" in text_to_search:
        return "California AI Safety Bill"
    
    return "국내외 규제 동향"

def reason_heuristic(hay: str) -> str:
    h = hay.lower()
    if "copyright" in h or "저작권" in h:
        return "AI 학습 데이터에 대한 저작권 가이드라인 또는 지식재산권 보호 조치 관련 정보."
    if "governance" in h or "policy" in h or "거버넌스" in h or "정책" in h:
        return "AI 윤리 준수 및 거버넌스 체계 구축을 위한 정책 가이드라인 또는 규제 프레임워크."
    if "ai act" in h or "eu" in h:
        return "EU AI Act 또는 이에 준하는 고강도 AI 규제 법안의 진척 및 대응 필요 사항."
    return "국내외 AI 규제 법제화, 가이드라인 배포 및 정책 동향 관련 최신 정보."

def build_regulations_from_news(news_items, known_cases, lookback_days: int = 3) -> List[RegulationInfo]:
    results: List[RegulationInfo] = []
    debug_log(f"build_regulations_from_news items={len(news_items)} lookback={lookback_days}")
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    for item in news_items:
        if item.published_at and item.published_at < cutoff:
            continue
        text, final_url = fetch_page_text(item.url)
        if not text:
            continue

        hay = (item.title + " " + text)
        lower = hay.lower()
        keywords = [
            "regulation", "governance", "act", "policy", "bill", "copyright", "dispute", "legal", 
            "intellectual property", "framework", "safety summit", "guideline", "ethics",
            "규제", "거버넌스", "기본법", "정책", "가이드라인", "저작권", "책임법", "윤리", "지식재산권"
        ]
        found = [k for k in keywords if k.lower() in lower]
        if not found:
            debug_log(f"Skipped non-relevant news: {item.title[:60]}...")
            continue
        matched_str = ", ".join(found)

        enrich = enrich_from_known(text, item.title, known_cases)

        # 규제명/대상 추출
        article_title = item.title
        country = enrich.get("country") or extract_country(text, article_title)
        case_title = enrich.get("case_title") or extract_regulation_subject(text, article_title)
        case_number = enrich.get("case_number") or "N/A"

        published = item.published_at or datetime.now(timezone.utc)
        update_date = published.date().isoformat()

        results.append(
            RegulationInfo(
                update_or_filed_date=update_date,
                country=country,
                case_title=case_title,
                article_title=article_title,
                case_number=case_number,
                reason=enrich.get("reason", reason_heuristic(hay)),
                article_urls=sorted(list({final_url, item.url})),
                matched_keywords=matched_str
            )
        )

    # 병합
    merged: Dict[tuple[str, str, str, str], RegulationInfo] = {}
    for r in results:
        key = (r.case_number, r.country, r.case_title, r.article_title)
        if key not in merged:
            merged[key] = r
        else:
            merged[key].article_urls = sorted(list(set(merged[key].article_urls + r.article_urls)))
            if r.update_or_filed_date > merged[key].update_or_filed_date:
                merged[key].update_or_filed_date = r.update_or_filed_date
            # 키워드 병합
            k1 = [x.strip() for x in merged[key].matched_keywords.split(",") if x.strip()]
            k2 = [x.strip() for x in r.matched_keywords.split(",") if x.strip()]
            merged[key].matched_keywords = ", ".join(sorted(list(set(k1 + k2))))

    return list(merged.values())