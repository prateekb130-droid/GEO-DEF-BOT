import feedparser, os, smtplib, re, trafilatura, time
from google import genai
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from time import mktime

FEEDS = {
    "IDRW": "https://idrw.org/feed/",
    "Diplomat": "https://thediplomat.com/feed/",
    "ORF": "https://www.orfonline.org/rss.xml",
    "Livefist": "https://www.livefistdefence.com/feed/"
}

IST_OFFSET = timedelta(hours=5, minutes=30)

def get_target_date_ist():
    now_ist = datetime.now(timezone.utc) + IST_OFFSET
    return (now_ist - timedelta(days=1)).date()

def entry_date_ist(entry):
    parsed = entry.get('published_parsed') or entry.get('updated_parsed')
    if not parsed:
        return None
    published_utc = datetime.fromtimestamp(mktime(parsed), tz=timezone.utc)
    return (published_utc + IST_OFFSET).date()

def clean_html(raw):
    text = re.sub(r'<[^>]+>', ' ', raw or '')
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:500]

def fetch_full_text(url):
    try:
        downloaded = trafilatura.fetch_url(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        if not downloaded:
            return None
        text = trafilatura.extract(downloaded)
        if text:
            return text.strip()[:2000]
    except Exception:
        pass
    return None

TIER1_DEFENCE = [
    "rafale", "tejas mk2", "tejas mk-2", "amca", "tedbf", "lca tejas", "su-30 upgrade", "mrfa",
    "s-400", "s400", "akash missile", "brahmos", "agni-", "agni v", "agni prime", "pralay", "pinaka",
    "ins vikrant", "ins vishal", "ins arighat", "ins aridhaman", "project 75", "project-75i", "scorpene",
    "arihant", "zorawar tank", "atags", "k9 vajra", "chief of defence staff", "theatre command",
    "theaterisation", "theatrisation", "agniveer", "agnipath scheme", "atmanirbhar bharat",
    "make in india defence", "positive indigenisation", "defence corridor", "no first use",
    "nuclear doctrine", "cold start doctrine", "mission shakti", "anti-satellite", "a-sat",
    "loitering munition", "marcos commando", "para sf", "garud commando",
    "lac", "loc", "galwan", "tawang", "doklam", "depsang", "demchok", "siachen",
    "surgical strike", "infiltration", "ceasefire violation"
]

TIER1_GEO = [
    "quad summit", "aukus", "indo-pacific strategy", "indian ocean region", " ior ",
    "china pakistan", "string of pearls", "cpec", "gwadar port", "hambantota",
    "maldives india", "bangladesh india", "nepal india", "sri lanka crisis"
]

TIER2_DEFENCE = [
    "exercise malabar", "yudh abhyas", "varuna exercise", "garuda exercise", "shakti exercise",
    "dustlik", "mitra shakti", "vayu shakti", "tarkash", "joint military exercise", "tri-service",
    "drdo", "isro military", "spy satellite", "cartosat", "hypersonic missile", "combat drone",
    "uav strike", "predator drone", "heron drone", "ghatak drone", "swarm drone",
    "hal ", "bel ", "ordnance factory", "defence production", "arms export india",
    "defence budget", "special forces", "amphibious assault", "andaman nicobar command"
]

TIER2_GEO = [
    "taiwan strait", "south china sea", "arunachal pradesh china", "brics expansion",
    "india us defence", "india russia defence", "india france defence", "india israel defence",
    "chabahar port", "asean india", "unsc permanent seat", "nsg membership",
    "military coup myanmar", "taliban afghanistan", "afghanistan india"
]

TIER3 = [
