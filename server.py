import http.server
import socketserver
import urllib.request
import urllib.parse
import re
import html
import json
import time
import os
import io
import unicodedata

try:
    import docx
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

PORT = 5000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

def resolve_full_title(raw_title):
    clean_q = raw_title.replace('\u2026', '').replace('...', '').rstrip('. ').strip()
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={urllib.parse.quote(clean_q)}&rows=2"
        req = urllib.request.Request(url, headers={'User-Agent': 'ScholarPulse/1.0 (mailto:scholar@research.org)'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            cr = json.loads(resp.read().decode('utf-8'))
        items = cr.get('message', {}).get('items', [])
        for it in items:
            t = it.get('title', [''])[0]
            if t:
                clean_t = html.unescape(re.sub(r'<[^>]+>', '', t).strip())
                if clean_q.lower()[:30] in clean_t.lower():
                    return clean_t
    except Exception:
        pass
    return clean_q

def scrape_scholar(user_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    author_info = None
    all_papers = []
    cstart = 0
    pagesize = 100
    
    while True:
        url = f"https://scholar.google.com/citations?user={user_id}&hl=en&cstart={cstart}&pagesize={pagesize}"
        print(f"[Scholar Scraper] Fetching: cstart={cstart}...")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print("[Scholar Scraper] Network error:", e)
            break
            
        if not author_info:
            name_m = re.search(r'id="gsc_prf_in"[^>]*>([^<]+)<', content)
            affil_m = re.search(r'class="gsc_prf_il"[^>]*>([^<]+)<', content)
            email_m = re.search(r'id="gsc_prf_ivh"[^>]*>([^<]+)<', content)
            interests = re.findall(r'class="gsc_prf_inta"[^>]*>([^<]+)<', content)
            avatar_m = re.search(r'<img[^>]+id="gsc_prf_pup-img"[^>]+src="([^"]+)"', content, re.I)
            avatar_url = html.unescape(avatar_m.group(1).strip()) if avatar_m else ""
            if avatar_url.startswith('/'):
                avatar_url = "https://scholar.google.com" + avatar_url
            
            author_info = {
                "name": html.unescape(name_m.group(1).strip()) if name_m else "Scholar Author",
                "affiliation": html.unescape(affil_m.group(1).strip()) if affil_m else "",
                "email": html.unescape(email_m.group(1).strip()) if email_m else "",
                "interests": [html.unescape(i.strip()) for i in interests],
                "avatar": avatar_url or None,
                "scholarLink": f"https://scholar.google.com/citations?user={user_id}"
            }

        rows = re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', content, re.DOTALL)
        if not rows:
            break
            
        page_papers = 0
        for r in rows:
            a_tag = re.search(r'<a\s+[^>]*class="[^"]*gsc_a_at[^"]*"[^>]*>(.*?)</a>', r, re.DOTALL)
            if not a_tag:
                continue
            
            raw_title = html.unescape(re.sub(r'<[^>]+>', '', a_tag.group(1)).strip())
            if '\u2026' in raw_title or raw_title.endswith('...') or '...' in raw_title:
                raw_title = resolve_full_title(raw_title)
            
            href_m = re.search(r'href="([^"]+)"', a_tag.group(0))
            link = ""
            if href_m:
                link = html.unescape(href_m.group(1))
                if link.startswith('/'):
                    link = "https://scholar.google.com" + link
            
            gray_divs = re.findall(r'<div class="gs_gray">(.*?)</div>', r, re.DOTALL)
            raw_authors = html.unescape(re.sub(r'<[^>]+>', '', gray_divs[0]).strip()) if gray_divs else ""
            authors = clean_authors(raw_authors)
            raw_venue = html.unescape(re.sub(r'<[^>]+>', '', gray_divs[1]).strip()) if len(gray_divs) > 1 else ""
            venue = clean_venue(raw_venue)
            
            cite_m = re.search(r'<a\s+[^>]*class="[^"]*gsc_a_ac[^"]*"[^>]*>([0-9]+)</a>', r)
            citations = int(cite_m.group(1)) if cite_m else 0
            
            year_m = re.search(r'<span\s+[^>]*class="[^"]*gsc_a_h[^"]*"[^>]*>([0-9]{4})</span>', r)
            year = int(year_m.group(1)) if year_m else None
            
            all_papers.append({
                "id": f"paper_{len(all_papers)+1}",
                "title": raw_title,
                "authors": authors,
                "venue": venue,
                "year": year,
                "citations": citations,
                "link": link
            })
            page_papers += 1
            
        print(f"[Scholar Scraper] Loaded {page_papers} papers (Total: {len(all_papers)})")
        if page_papers < pagesize:
            break
        cstart += page_papers
        time.sleep(0.3)
        
    return {
        "author": author_info or {"name": f"Author ({user_id})", "affiliation": "", "email": "", "interests": []},
        "papers": all_papers
    }


def clean_venue(v):
    if not v:
        return ""
    v = re.sub(r'[\.\s\u2026]{2,}$', '', v).strip()
    if re.match(r'^\(?(?:19|20)\d{2}\)?$', v):
        return ""
    return re.sub(r'(?:,\s*|\s+)\(?(?:19|20)\d{2}\)?\s*$', '', v).strip()


def clean_authors(a):
    if not a:
        return "Unknown Authors"
    return re.sub(r'[\s,]+(?:\.{2,}|\u2026)\s*$', '', a).strip()


def clean_title(t):
    if not t:
        return "Untitled"
    return re.sub(r'[\.\s\u2026]+$', '', t).strip()


def generate_docx(payload):
    if not HAS_DOCX:
        raise RuntimeError("python-docx is not installed.")
        
    author = payload.get('author', {})
    papers = payload.get('papers', [])
    style_name = payload.get('style', 'APA').upper()
    citations = payload.get('citations', [])

    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    p_title = doc.add_paragraph()
    r_name = p_title.add_run(author.get('name', 'Scholar Author'))
    r_name.font.name = 'Calibri'
    r_name.font.size = Pt(22)
    r_name.font.bold = True
    r_name.font.color.rgb = RGBColor(29, 78, 216)
    p_title.paragraph_format.space_after = Pt(2)

    if author.get('affiliation'):
        p_affil = doc.add_paragraph()
        r_aff = p_affil.add_run(author.get('affiliation', ''))
        r_aff.font.name = 'Calibri'
        r_aff.font.size = Pt(11)
        r_aff.font.italic = True
        r_aff.font.color.rgb = RGBColor(100, 116, 139)
        p_affil.paragraph_format.space_after = Pt(2)

    if author.get('email'):
        p_email = doc.add_paragraph()
        r_em = p_email.add_run(author.get('email', ''))
        r_em.font.name = 'Calibri'
        r_em.font.size = Pt(10)
        r_em.font.color.rgb = RGBColor(148, 163, 184)
        p_email.paragraph_format.space_after = Pt(12)

    p_head = doc.add_heading(level=1)
    r_head = p_head.add_run(f"List of Publications ({style_name} Style — {len(papers)} Papers)")
    r_head.font.name = 'Calibri'
    r_head.font.size = Pt(14)
    r_head.font.bold = True
    r_head.font.color.rgb = RGBColor(15, 23, 42)
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(10)

    for idx, p_obj in enumerate(papers):
        p_elem = doc.add_paragraph()
        p_elem.paragraph_format.left_indent = Inches(0.5)
        p_elem.paragraph_format.first_line_indent = Inches(-0.5)
        p_elem.paragraph_format.space_before = Pt(0)
        p_elem.paragraph_format.space_after = Pt(0)
        p_elem.paragraph_format.line_spacing = 1.0
        
        if idx < len(citations) and citations[idx]:
            c_text = citations[idx]
        else:
            venue = clean_venue(p_obj.get('venue', ''))
            authors = clean_authors(p_obj.get('authors', ''))
            title = clean_title(p_obj.get('title', ''))
            if venue:
                c_text = f"{idx+1}. {authors} ({p_obj.get('year', 'n.d.')}). {title}. {venue}."
            else:
                c_text = f"{idx+1}. {authors} ({p_obj.get('year', 'n.d.')}). {title}."

        c_text = re.sub(r'\s*\.{2,}', '.', c_text)
        c_text = re.sub(r'\.\s+\.', '.', c_text)
        c_text = re.sub(r'\s*\.$', '.', c_text)

        r_body = p_elem.add_run(c_text)
        r_body.font.name = 'Calibri'
        r_body.font.size = Pt(11)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def levenshtein_dist(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_dist(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def normalize_search_text(value):
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    return re.sub(r'[\W_]+', ' ', text, flags=re.UNICODE).strip()


def search_tokens(value):
    return [token for token in normalize_search_text(value).split() if len(token) > 1]


def token_similarity(query_token, target_token):
    if not query_token or not target_token:
        return 0.0
    if query_token == target_token:
        return 1.0
    if query_token in target_token or target_token in query_token:
        return 0.86 + (min(len(query_token), len(target_token)) / max(len(query_token), len(target_token))) * 0.08
    distance = levenshtein_dist(query_token, target_token)
    max_distance = 1 if len(query_token) <= 4 else 2 if len(query_token) <= 7 else 3
    if distance > max_distance:
        return 0.0
    return max(0.0, 1 - (distance / max(len(query_token), len(target_token))))


def best_token_similarity(query_token, target_tokens):
    return max((token_similarity(query_token, target) for target in target_tokens), default=0.0)


def author_match_score(query, name, affiliation=''):
    normalized_query = normalize_search_text(query)
    normalized_name = normalize_search_text(name)
    normalized_affiliation = normalize_search_text(affiliation)
    if not normalized_query or not normalized_name:
        return 0.0
    if normalized_name == normalized_query:
        return 1.0
    if normalized_query in normalized_name:
        return 0.98
    if normalized_query in normalized_affiliation:
        return 0.82

    query_tokens = search_tokens(query)
    name_tokens = search_tokens(name)
    affiliation_tokens = search_tokens(affiliation)
    if not query_tokens:
        return 0.0

    name_scores = [best_token_similarity(token, name_tokens) for token in query_tokens]
    affiliation_scores = [best_token_similarity(token, affiliation_tokens) for token in query_tokens]
    combined_scores = [max(name_score, affiliation_score * 0.88) for name_score, affiliation_score in zip(name_scores, affiliation_scores)]
    minimum_score = 0.58 if len(query_tokens) == 1 else 0.52
    if any(score < minimum_score for score in combined_scores):
        return 0.0

    average_score = sum(combined_scores) / len(combined_scores)
    name_coverage = sum(name_scores) / len(name_scores)
    return min(0.96, (average_score * 0.68) + (name_coverage * 0.32))


def fuzzy_match_author(query, target):
    return author_match_score(query, target) >= 0.58


SEARCH_SPELLING_VARIANTS = {
    'nasser': ['naser'],
    'naser': ['nasser'],
    'hossein': ['hosein', 'hussein'],
    'hosein': ['hossein', 'hussein'],
    'hussein': ['hossein', 'hosein'],
    'hassan': ['hasan'],
    'hasan': ['hassan'],
    'mohammed': ['mohammad', 'mohamed', 'mohamad'],
    'mohammad': ['mohammed', 'mohamed', 'mohamad'],
    'mohamed': ['mohammad', 'mohammed', 'mohamad'],
    'mohamad': ['mohammad', 'mohammed', 'mohamed'],
    'mehdi': ['mahdi'],
    'mahdi': ['mehdi'],
    'rodabeh': ['roudabeh'],
    'roudabeh': ['rodabeh'],
    'samiee': ['samie', 'samii'],
    'samie': ['samiee', 'samii'],
}


def get_search_variants(q):
    variants = [q.strip()]
    words = q.strip().split()
    priority_variants = []
    for index, word in enumerate(words):
        for candidate in SEARCH_SPELLING_VARIANTS.get(word.lower(), []):
            variant_words = list(words)
            variant_words[index] = candidate
            priority_variants.append(' '.join(variant_words))
    
    for i, w in enumerate(words):
        w_low = w.lower()
        word_cands = set()

        for candidate in SEARCH_SPELLING_VARIANTS.get(w_low, []):
            word_cands.add(candidate)
        
        # Vowels & Transliterations
        if 'ou' in w_low:
            word_cands.add(re.sub('ou', 'o', w, flags=re.I))
            word_cands.add(re.sub('ou', 'u', w, flags=re.I))
        elif 'o' in w_low:
            word_cands.add(re.sub('o', 'ou', w, flags=re.I))
            word_cands.add(re.sub('o', 'oo', w, flags=re.I))
            
        if 'oo' in w_low:
            word_cands.add(re.sub('oo', 'ou', w, flags=re.I))
            word_cands.add(re.sub('oo', 'u', w, flags=re.I))
            
        if 'ee' in w_low:
            word_cands.add(re.sub('ee', 'i', w, flags=re.I))
        elif 'i' in w_low:
            word_cands.add(re.sub('i', 'ee', w, flags=re.I))
            word_cands.add(re.sub('i', 'y', w, flags=re.I))
            
        if 'ei' in w_low:
            word_cands.add(re.sub('ei', 'ee', w, flags=re.I))
            word_cands.add(re.sub('ei', 'ey', w, flags=re.I))
            
        if 'zadeh' in w_low:
            word_cands.add(re.sub('zadeh', 'zade', w, flags=re.I))
        elif 'zade' in w_low:
            word_cands.add(re.sub('zade', 'zadeh', w, flags=re.I))
            
        if 'pour' in w_low:
            word_cands.add(re.sub('pour', 'poor', w, flags=re.I))
            word_cands.add(re.sub('pour', 'por', w, flags=re.I))
        elif 'por' in w_low:
            word_cands.add(re.sub('por', 'pour', w, flags=re.I))
            
        # Individual consonant doubling & reduction: l, s, m, d, t, r, n, p, b, f, z
        for idx, char in enumerate(w):
            c_low = char.lower()
            if c_low in 'lsmdtrnpbfz':
                # If followed by another same char, candidate with single
                if idx + 1 < len(w) and w[idx+1].lower() == c_low:
                    reduced = w[:idx] + w[idx+1:]
                    word_cands.add(reduced)
                # If not preceded or followed by same char, candidate with doubled
                elif (idx == 0 or w[idx-1].lower() != c_low) and (idx + 1 == len(w) or w[idx+1].lower() != c_low):
                    doubled = w[:idx+1] + char.lower() + w[idx+1:]
                    word_cands.add(doubled)
                    
        for cand in word_cands:
            v_words = list(words)
            v_words[i] = cand
            v_str = ' '.join(v_words)
            if v_str not in variants:
                variants.append(v_str)
                
    return list(dict.fromkeys(variants[:1] + priority_variants + variants[1:]))[:24]


class ScholarHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Access-Control-Expose-Headers', 'Content-Disposition')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/api/export-docx':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                payload = json.loads(body)
                author_name = payload.get('author', {}).get('name', 'Scholar_Author').replace(' ', '_')
                style = payload.get('style', 'APA')
                filename = f"{author_name}_Publications_{style}.docx"
                
                docx_bytes = generate_docx(payload)
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', str(len(docx_bytes)))
                self.end_headers()
                self.wfile.write(docx_bytes)
                return
            except Exception as e:
                print("Docx export error:", e)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                return

        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # Download docx via direct GET
        if parsed.path == '/api/download-docx':
            query = urllib.parse.parse_qs(parsed.query)
            user_id = query.get('user', ['8EUCPOUAAAAJ'])[0].strip()
            style = query.get('style', ['APA'])[0].strip()
            
            cache_file = os.path.join(DIRECTORY, f"scholar_{user_id}.json")
            if not os.path.exists(cache_file):
                cache_file = os.path.join(DIRECTORY, "scholar_8EUCPOUAAAAJ.json")
                
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                payload = {
                    "author": data.get('author', {}),
                    "papers": data.get('papers', []),
                    "style": style
                }
                docx_bytes = generate_docx(payload)
                author_name = data.get('author', {}).get('name', 'Scholar_Author').replace(' ', '_')
                filename = f"{author_name}_Publications_{style}.docx"
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.send_header('Content-Length', str(len(docx_bytes)))
                self.end_headers()
                self.wfile.write(docx_bytes)
                return

        if parsed.path == '/api/scrape':
            query = urllib.parse.parse_qs(parsed.query)
            user_id = query.get('user', [''])[0].strip()
            
            match = re.search(r'[?&]user=([a-zA-Z0-9_-]+)', user_id)
            if match:
                user_id = match.group(1)
                
            if not user_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing or invalid user parameter"}).encode('utf-8'))
                return

            print(f"[API] Scraping user: {user_id}")
            result = scrape_scholar(user_id)
            
            try:
                cache_file = os.path.join(DIRECTORY, f"scholar_{user_id}.json")
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print("Cache write notice:", e)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            return

        if parsed.path == '/api/search-author':
            query = urllib.parse.parse_qs(parsed.query)
            q = query.get('q', [''])[0].strip()
            if not q:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing query parameter q"}).encode('utf-8'))
                return

            print(f"[API] Searching authors for: {q}")
            results = []
            q_lower = q.lower()
            
            presets = [
                {
                    "id": "8EUCPOUAAAAJ",
                    "name": "Prof. Nasser Mehrdadi",
                    "affiliation": "Professor of Environmental Engineering, Faculty of Environment, University of Tehran",
                    "works_count": 353,
                    "citations": 5393,
                    "h_index": 37,
                    "avatar": "https://scholar.googleusercontent.com/citations?view_op=view_photo&user=8EUCPOUAAAAJ&citpid=2",
                    "source": "scholar"
                },
                {
                    "id": "A5052955513",
                    "name": "Dr. Roudabeh Samiee-Zafarghandi",
                    "affiliation": "Department of Environmental Engineering, University of Tehran",
                    "works_count": 6,
                    "citations": 180,
                    "h_index": 4,
                    "avatar": "https://api.dicebear.com/7.x/notionists/svg?seed=RoudabehSamiee&backgroundColor=ffd5dc,ffdfbf",
                    "source": "openalex"
                },
                {
                    "id": "A5060424364",
                    "name": "Prof. Ali Torabian",
                    "affiliation": "Faculty of Environment, University of Tehran",
                    "works_count": 83,
                    "citations": 2379,
                    "h_index": 28,
                    "avatar": "https://api.dicebear.com/7.x/notionists/svg?seed=AliTorabian&backgroundColor=b6e3f4,c0aede",
                    "source": "openalex"
                },
                {
                    "id": "u1PBvywAAAAJ",
                    "name": "Prof. Yoshua Bengio",
                    "affiliation": "Professor of Computer Science, Université de Montréal, Mila",
                    "works_count": 920,
                    "citations": 832000,
                    "h_index": 230,
                    "avatar": "https://scholar.googleusercontent.com/citations?view_op=view_photo&user=u1PBvywAAAAJ&citpid=2",
                    "source": "scholar"
                },
                {
                    "id": "JicYPdAAAAAJ",
                    "name": "Prof. Geoffrey Hinton",
                    "affiliation": "Professor Emeritus of Computer Science, University of Toronto",
                    "works_count": 340,
                    "citations": 680000,
                    "h_index": 175,
                    "avatar": "https://scholar.googleusercontent.com/citations?view_op=view_photo&user=JicYPdAAAAAJ&citpid=2",
                    "source": "scholar"
                },
                {
                    "id": "WLN3QrAAAAAJ",
                    "name": "Prof. Yann LeCun",
                    "affiliation": "Professor of Computer Science, NYU & Chief AI Scientist, Meta",
                    "works_count": 480,
                    "citations": 410000,
                    "h_index": 158,
                    "avatar": "https://scholar.googleusercontent.com/citations?view_op=view_photo&user=WLN3QrAAAAAJ&citpid=2",
                    "source": "scholar"
                }
            ]
            
            for p in presets:
                if fuzzy_match_author(q, p["name"]) or fuzzy_match_author(q, p["affiliation"]) or q_lower in p["id"].lower():
                    results.append(p)
            
            try:
                alex_url = f"https://api.openalex.org/authors?search={urllib.parse.quote(q)}"
                req = urllib.request.Request(alex_url, headers={'User-Agent': 'ScholarPulse/1.0 (mailto:scholarpulse@research.org)'})
                with urllib.request.urlopen(req, timeout=6) as res:
                    alex_data = json.loads(res.read().decode('utf-8'))
                
                for a in alex_data.get('results', [])[:8]:
                    name = a.get('display_name', '')
                    inst = a.get('last_known_institutions', [{}])[0].get('display_name', '') if a.get('last_known_institutions') else ''
                    works_cnt = a.get('works_count', 0)
                    cites_cnt = a.get('cited_by_count', 0)
                    h_idx = a.get('summary_stats', {}).get('h_index', 0)
                    aid = a.get('id', '').split('/')[-1]
                    
                    if not any(r['name'].lower() == name.lower() for r in results):
                        avatar_url = a.get('image_url') or a.get('image_thumbnail_url') or f"https://api.dicebear.com/7.x/notionists/svg?seed={urllib.parse.quote(name)}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf"
                        results.append({
                            "id": aid,
                            "name": name,
                            "affiliation": inst,
                            "works_count": works_cnt,
                            "citations": cites_cnt,
                            "h_index": h_idx,
                            "avatar": avatar_url,
                            "image_url": a.get('image_url') or "",
                            "image_thumbnail_url": a.get('image_thumbnail_url') or "",
                            "source": "openalex"
                        })
            except Exception as e:
                print("[API] OpenAlex search notice:", e)

            # If the first query did not produce a close match, try a few spelling
            # variants even when the API returned unrelated popular authors.
            has_close_result = any(
                author_match_score(q, item.get('name', ''), item.get('affiliation', '')) >= 0.58
                for item in results
            )
            if len(results) < 3 or not has_close_result:
                variants = get_search_variants(q)
                for var in variants[1:5]:
                    if len(results) >= 8:
                        break
                    for p in presets:
                        if (fuzzy_match_author(var, p["name"]) or fuzzy_match_author(var, p["affiliation"])) and not any(r['id'] == p['id'] for r in results):
                            results.append(p)
                    try:
                        alex_url = f"https://api.openalex.org/authors?search={urllib.parse.quote(var)}"
                        req = urllib.request.Request(alex_url, headers={'User-Agent': 'ScholarPulse/1.0 (mailto:scholarpulse@research.org)'})
                        with urllib.request.urlopen(req, timeout=3) as res:
                            alex_data = json.loads(res.read().decode('utf-8'))
                        for a in alex_data.get('results', [])[:4]:
                            name = a.get('display_name', '')
                            inst = a.get('last_known_institutions', [{}])[0].get('display_name', '') if a.get('last_known_institutions') else ''
                            works_cnt = a.get('works_count', 0)
                            cites_cnt = a.get('cited_by_count', 0)
                            h_idx = a.get('summary_stats', {}).get('h_index', 0)
                            aid = a.get('id', '').split('/')[-1]
                            if (
                                author_match_score(q, name, inst) >= 0.46
                                or author_match_score(var, name, inst) >= 0.58
                            ) and not any(r['name'].lower() == name.lower() or r['id'] == aid for r in results):
                                avatar_url = a.get('image_url') or a.get('image_thumbnail_url') or f"https://api.dicebear.com/7.x/notionists/svg?seed={urllib.parse.quote(name)}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf"
                                results.append({
                                    "id": aid,
                                    "name": name,
                                    "affiliation": inst,
                                    "works_count": works_cnt,
                                    "citations": cites_cnt,
                                    "h_index": h_idx,
                                    "avatar": avatar_url,
                                    "image_url": a.get('image_url') or "",
                                    "image_thumbnail_url": a.get('image_thumbnail_url') or "",
                                    "source": "openalex"
                                })
                    except Exception:
                        pass

            search_variants = get_search_variants(q)[:8]
            results.sort(
                key=lambda item: (
                    max(
                        author_match_score(
                            variant,
                            item.get('name', ''),
                            item.get('affiliation', ''),
                        )
                        for variant in search_variants
                    ),
                    item.get('citations', 0),
                ),
                reverse=True,
            )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"results": results}, ensure_ascii=False).encode('utf-8'))
            return

        if parsed.path == '/api/author-works':
            query = urllib.parse.parse_qs(parsed.query)
            author_id = query.get('author_id', [''])[0].strip()
            
            if author_id in ['8EUCPOUAAAAJ', '']:
                cache_file = os.path.join(DIRECTORY, "scholar_8EUCPOUAAAAJ.json")
                if os.path.exists(cache_file):
                    with open(cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
                    return

            if author_id.startswith('A') or author_id.isdigit():
                try:
                    a_url = f"https://api.openalex.org/authors/{author_id}"
                    req = urllib.request.Request(a_url, headers={'User-Agent': 'ScholarPulse/1.0'})
                    with urllib.request.urlopen(req, timeout=6) as res:
                        a_meta = json.loads(res.read().decode('utf-8'))
                    
                    author_name = a_meta.get('display_name', f'Scholar ({author_id})')
                    affil = a_meta.get('last_known_institutions', [{}])[0].get('display_name', '') if a_meta.get('last_known_institutions') else ''
                    
                    w_url = f"https://api.openalex.org/works?filter=author.id:{author_id}&per-page=100"
                    req = urllib.request.Request(w_url, headers={'User-Agent': 'ScholarPulse/1.0'})
                    with urllib.request.urlopen(req, timeout=8) as res:
                        w_data = json.loads(res.read().decode('utf-8'))
                        
                    alex_papers = []
                    for idx, w in enumerate(w_data.get('results', [])):
                        t = w.get('title') or 'Untitled'
                        auths = ', '.join([auth.get('author', {}).get('display_name', '') for auth in w.get('authorships', [])])
                        loc = w.get('primary_location', {}) or {}
                        src = loc.get('source', {}) or {}
                        ven = src.get('display_name', '')
                        yr = w.get('publication_year')
                        cites = w.get('cited_by_count', 0)
                        doi = (w.get('doi') or '').replace('https://doi.org/', '')
                        link = w.get('doi') or loc.get('landing_page_url') or ''
                        
                        alex_papers.append({
                            "id": f"paper_{idx+1}",
                            "title": clean_title(t),
                            "authors": clean_authors(auths),
                            "venue": clean_venue(ven),
                            "year": yr,
                            "citations": cites,
                            "doi": doi,
                            "link": link
                        })
                    
                    out_payload = {
                        "author": {
                            "name": author_name,
                            "affiliation": affil,
                            "email": "",
                            "avatar": f"https://api.dicebear.com/7.x/notionists/svg?seed={urllib.parse.quote(author_name)}&backgroundColor=b6e3f4,c0aede,d1d4f9,ffd5dc,ffdfbf",
                            "interests": [t.get('display_name', '') for t in a_meta.get('x_concepts', [])[:5]],
                            "stats": {
                                "citations": a_meta.get('cited_by_count', 0),
                                "h_index": a_meta.get('summary_stats', {}).get('h_index', 0),
                                "i10_index": a_meta.get('summary_stats', {}).get('i10_index', 0)
                            }
                        },
                        "papers": alex_papers
                    }
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(json.dumps(out_payload, ensure_ascii=False).encode('utf-8'))
                    return
                except Exception as e:
                    print("OpenAlex works error:", e)
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
                    return

        return super().do_GET()


def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ScholarHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 60)
        print(f" ScholarPulse Local Server running at: {url}")
        print(" Direct scraping + Word (.docx) export active")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == '__main__':
    main()
