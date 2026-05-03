from dotenv import load_dotenv
import os
import asyncio
import json
import random
import re
import sys
import requests
from html import escape
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import PeerChannel

load_dotenv()


def parse_source_channels(raw_value):
    channels = []

    for item in (raw_value or "").split(","):
        value = item.strip()
        if not value:
            continue
        if re.fullmatch(r"-?\d+", value):
            channels.append(int(value))
        else:
            channels.append(value)

    return channels


API_ID = os.getenv("TG_API_ID")
API_HASH = os.getenv("TG_API_HASH")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
SOURCE_CHANNELS = parse_source_channels(SOURCE_CHANNEL)
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")
REVIEW_CHANNEL_ID = os.getenv("REVIEW_CHANNEL_ID", "").strip()
if REVIEW_CHANNEL_ID.startswith("100"):
    REVIEW_CHANNEL_ID = f"-{REVIEW_CHANNEL_ID}"
MODERATION_ENABLED = os.getenv("MODERATION_ENABLED", "false").strip().lower() == "true"
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("TG_SESSION_STRING", "").strip()
AI_ENABLED = os.getenv("AI_ENABLED", "false").strip().lower() == "true"
AI_API_KEY = (os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
AI_MODEL = os.getenv("AI_MODEL", "gpt-4.1-mini").strip()
AI_STYLE_PROMPT = os.getenv(
    "AI_STYLE_PROMPT",
    "Rewrite the Telegram post in natural Portuguese. Keep facts, odds, teams, scores, promo meaning, and useful details. For sports news keep it short, factual, and clean. For promo posts make it persuasive, neat, and readable. Do not invent facts or numbers.",
).strip()
AI_TARGET_LANG = (os.getenv("AI_TARGET_LANG", "").strip() or "portuguese").lower()
PROMOCODE_TEXT = os.getenv("PROMOCODE_TEXT", "Codigo promocional: NILE").strip() or "Codigo promocional: NILE"
APK_URL = os.getenv("APK_URL", "https://lckypr.com/wW5nH61").strip() or "https://lckypr.com/wW5nH61"

BUTTON1_TEXT = os.getenv("BUTTON1_TEXT", "Cadastre-se LUCKYPARI💛").strip()
BUTTON1_URL = os.getenv("BUTTON1_URL", "https://lckypr.com/G4DtDxQ").strip()
BUTTON2_TEXT = os.getenv("BUTTON2_TEXT", "Cadastre-se WINWIN🚀").strip()
BUTTON2_URL = os.getenv("BUTTON2_URL", "https://winwin-624339.top/ru/registration?tag=d_5343420m_94904c_").strip()
BUTTON3_TEXT = os.getenv("BUTTON3_TEXT", "Cadastre-se ULTRAPARI🔥").strip()
BUTTON3_URL = os.getenv("BUTTON3_URL", "https://ultrapari.com/ru/registration?tag=d_5299306m_118408c_").strip()
BUTTON4_TEXT = os.getenv("BUTTON4_TEXT", "Cadastre-se LINEBET👑").strip()
BUTTON4_URL = os.getenv("BUTTON4_URL", "https://lb-aff.com/L?tag=d_5445297m_22611c_site&site=5445297&ad=22611&r=registration").strip()

LUCKYPARI_APK_URL = os.getenv("LUCKYPARI_APK_URL", "https://lckypr.com/wW5nH61").strip()
ULTRAPARI_APK_URL = os.getenv("ULTRAPARI_APK_URL", "https://refpa42156.com/L?tag=d_5299306m_118431c_&site=5299306&ad=118431").strip()
WINWIN_APK_URL = os.getenv("WINWIN_APK_URL", "https://refpa712080.pro/L?tag=d_5343420m_68383c_&site=5343420&ad=68383").strip()
LINEBET_APK_URL = os.getenv("LINEBET_APK_URL", "https://lb-aff.com/L?tag=d_5445297m_66803c_apk1&site=5445297&ad=66803").strip()
ALBUM_CHANNEL_URL = os.getenv("ALBUM_CHANNEL_URL", "https://lckypr.com/wW5nH61").strip() or "https://lckypr.com/wW5nH61"
BONUS_BUTTON_MESSAGE = os.getenv("BONUS_BUTTON_MESSAGE", "Escolha sua casa favorita").strip() or "Escolha sua casa favorita"
REVIEW_MODE = MODERATION_ENABLED and bool(REVIEW_CHANNEL_ID)

TEXT_LINK_TOKENS = [
    ("[[APK1]]", "LuckyPari APK", LUCKYPARI_APK_URL),
    ("[[APK2]]", "WinWin APK", WINWIN_APK_URL),
    ("[[APK3]]", "UltraPari APK", ULTRAPARI_APK_URL),
    ("[[APK4]]", "Linebet APK", LINEBET_APK_URL),
]

ALBUM_LINK_TOKEN = "[[ALBUM_APK]]"
ALBUM_LINK_LABEL = "🎮APK ANDROID"

BOOKMAKER_LINK_LINES = [
    ("luckypa", "LuckyPari", BUTTON1_URL or "https://lckypr.com/G4DtDxQ"),
    ("winwin", "WinWin", BUTTON2_URL or "https://winwin-624339.top/ru/registration?tag=d_5343420m_94904c_"),
    ("ultrapari", "UltraPari", BUTTON3_URL or "https://ultrapari.com/ru/registration?tag=d_5299306m_118408c_"),
    ("linebet", "Linebet", BUTTON4_URL or "https://lb-aff.com/L?tag=d_5445297m_22611c_site&site=5445297&ad=22611&r=registration"),
]

FALLBACK_BOOKMAKER_NAME = "LuckyPari"
FALLBACK_BOOKMAKER_URL = BUTTON1_URL or "https://lckypr.com/G4DtDxQ"
PRIMARY_BUTTON_LINK = (BUTTON1_TEXT, BUTTON1_URL)

BUTTON_LINKS = [PRIMARY_BUTTON_LINK]

PARTNER_LINE_TOKENS = [
    ("[[PARTNER1]]", BUTTON1_TEXT, BUTTON1_URL),
]

TOKEN_ONLY_LINES = {token for token, _, _ in TEXT_LINK_TOKENS}
TOKEN_ONLY_LINES.update({token for token, _, _ in PARTNER_LINE_TOKENS})
TOKEN_ONLY_LINES.add(ALBUM_LINK_TOKEN)
URL_PATTERN = re.compile(r"(?:https?://|www\.|t\.me/|telegram\.me/)\S+", re.IGNORECASE)
HANDLE_PATTERN = re.compile(r"(?<!\w)@[\w\d_]{3,}")
STANDALONE_CODE_PATTERN = re.compile(r"^[A-Z0-9]{5,8}$")
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}

CYRILLIC_TITLES = [
    "ÐœÐ¾Ñ ÑÑ‚Ð°Ð²ÐºÐ° ÑÐµÐ³Ð¾Ð´Ð½Ñ:",
    "Ð¢Ð¾Ð¿ ÑÑ‚Ð°Ð²ÐºÐ° Ð´Ð½Ñ:",
    "Ð¡ÐµÐ³Ð¾Ð´Ð½Ñ Ð±ÐµÑ€Ñƒ Ð²Ð¾Ñ‚ ÑÑ‚Ð¾:",
    "Ð¡Ñ‚Ð°Ð²ÐºÐ° Ð½Ð° ÑÐµÐ³Ð¾Ð´Ð½Ñ:",
    "Ð—Ð°Ð±Ð¸Ñ€Ð°ÑŽ Ñ‚Ð°ÐºÐ¾Ð¹ Ð²Ð°Ñ€Ð¸Ð°Ð½Ñ‚:",
]

LATIN_TITLES = [
    "Bugungi top stavka:",
    "Bugun men shuni tanladim:",
    "Kun stavkasi:",
    "Mening bugungi tanlovim:",
    "Bugungi stavkam:",
]

STATE_FILE = "data/state.json"
PENDING_FILE = "data/pending.json"
CHECK_INTERVAL = 10


def safe_console_text(value):
    text = str(value)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


def get_source_key(entity, source_name=None):
    entity_id = getattr(entity, "id", None)
    if entity_id is not None:
        return str(entity_id)
    return str(source_name or "").strip()


def get_source_signature(entity, source_name=None):
    source_name = str(source_name or "").strip().lower()
    entity_id = getattr(entity, "id", "")
    return f"{entity_id}:{source_name}"


def get_source_state_bucket(state, source_key):
    sources = state.get("sources")
    if not isinstance(sources, dict):
        sources = {}
        state["sources"] = sources

    bucket = sources.get(source_key)
    if not isinstance(bucket, dict):
        bucket = {}
        sources[source_key] = bucket

    return bucket


def migrate_state_shape(state):
    changed = False

    if not isinstance(state.get("sources"), dict):
        state["sources"] = {}
        changed = True

    if "source_signature" in state:
        state.pop("source_signature", None)
        changed = True

    if "last_post_key" in state:
        state.pop("last_post_key", None)
        changed = True

    return changed


def build_reply_markup():
    rows = []

    for text, url in BUTTON_LINKS:
        if text and url:
            rows.append([{"text": text, "url": url}])

    if not rows:
        return None

    return {"inline_keyboard": rows}


def build_moderation_markup(post_key):
    return {
        "inline_keyboard": [
            [
                {"text": "Approve", "callback_data": f"approve:{post_key}"},
                {"text": "Reject", "callback_data": f"reject:{post_key}"},
            ]
        ]
    }


def prepare_telegram_text(text, limit=None):
    text = text if text else "[Ð±ÐµÐ· Ñ‚ÐµÐºÑÑ‚Ð°]"
    if limit:
        text = text[:limit]

    safe_text = escape(text)
    apk_link = f'<a href="{escape(APK_URL, quote=True)}">APK</a>'
    safe_text = re.sub(r"\bAPK\b", apk_link, safe_text, flags=re.IGNORECASE)
    safe_text = safe_text.replace(
        escape(ALBUM_LINK_TOKEN),
        f'<a href="{escape(ALBUM_CHANNEL_URL, quote=True)}">{escape(ALBUM_LINK_LABEL)}</a>',
    )

    for token, label, url in TEXT_LINK_TOKENS:
        safe_text = safe_text.replace(
            escape(token),
            f'<a href="{escape(url, quote=True)}">{escape(label)}</a>',
        )

    for token, label, url in PARTNER_LINE_TOKENS:
        safe_text = safe_text.replace(
            escape(token),
            f'<a href="{escape(url, quote=True)}">{escape(label)}</a>',
        )

    return safe_text


def detect_text_language(text):
    cyrillic_count = sum(1 for char in text.lower() if "Ð°" <= char <= "Ñ" or char == "Ñ‘")
    latin_count = sum(1 for char in text.lower() if "a" <= char <= "z")
    return "cyrillic" if cyrillic_count > latin_count else "latin"


def build_post_title(text):
    titles = CYRILLIC_TITLES if detect_text_language(text) == "cyrillic" else LATIN_TITLES
    return random.choice(titles)


def add_offer_footer(text):
    footer_tokens = [token for token, _, _ in TEXT_LINK_TOKENS]

    if any(token in text for token in footer_tokens):
        return text

    footer_block = "\n".join(footer_tokens)
    return f"{text}\n\n{footer_block}".strip()


def add_album_footer(text):
    body = (text or "").strip()

    if ALBUM_LINK_TOKEN in body:
        return body

    if not body:
        return ALBUM_LINK_TOKEN

    return f"{body}\n\n{ALBUM_LINK_TOKEN}".strip()


FOREIGN_BOOKMAKER_KEYWORDS = (
    "1xbet",
    "dbbet",
    "betkom",
    "melbet",
    "mostbet",
    "fonbet",
    "parimatch",
    "pari match",
    "pari-match",
    "betwinner",
    "pinup",
    "pin-up",
    "winline",
    "leon",
    "olimp",
    "marathon",
    "betboom",
    "granawin",
    "granawip",
    "grana win",
)

BOOKMAKER_KEYWORDS = FOREIGN_BOOKMAKER_KEYWORDS + (
    "luckypa",
    "luckypari",
    "ultrapari",
    "winwin",
    "linebet",
)

FOREIGN_BOOKMAKER_PATTERN = re.compile(
    r"\b(?:1xbet|dbbet|betkom|melbet|mostbet|fonbet|parimatch|pari[\s-]?match|betwinner|pin[\s-]?up|winline|leon|olimp|marathon|betboom|granawin|granawip|grana\s+win)\b",
    re.IGNORECASE,
)

PARTNER_HINT_KEYWORDS = (
    "bonus",
    "bônus",
    "promo",
    "promocode",
    "promo code",
    "promo-code",
    "promokod",
    "codigo promocional",
    "código promocional",
    "register",
    "registration",
    "sign up",
    "signup",
    "cadastre",
    "cadastro",
    "apk",
    "download",
    "baixar",
    "deposit",
    "депозит",
    "скач",
    "yuklab",
)


def strip_language_banner(text):
    lines = []

    for raw_line in (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        lowered = line.lower().rstrip(":")

        if lowered.startswith("язык результата"):
            continue
        if lowered.startswith("result language"):
            continue
        if lowered.startswith("language result"):
            continue
        if lowered == AI_TARGET_LANG:
            continue

        lines.append(raw_line)

    return "\n".join(lines)


def has_partner_hint(line):
    lowered = (line or "").lower()
    if not lowered:
        return False

    has_link = bool(URL_PATTERN.search(line) or HANDLE_PATTERN.search(line))
    has_brand = any(keyword in lowered for keyword in BOOKMAKER_KEYWORDS)
    has_hint = any(keyword in lowered for keyword in PARTNER_HINT_KEYWORDS)
    return has_brand or (has_link and has_hint)


def replace_foreign_bookmaker_mentions(text):
    return FOREIGN_BOOKMAKER_PATTERN.sub(FALLBACK_BOOKMAKER_NAME, text or "")


def sanitize_partner_line(line):
    cleaned_line = replace_foreign_bookmaker_mentions(line)
    cleaned_line = URL_PATTERN.sub("", cleaned_line)
    cleaned_line = HANDLE_PATTERN.sub("", cleaned_line)
    cleaned_line = re.sub(r"[ \t]{2,}", " ", cleaned_line)
    cleaned_line = cleaned_line.strip(" -–—|•·")

    if not cleaned_line:
        return ""
    if STANDALONE_CODE_PATTERN.fullmatch(cleaned_line):
        return ""

    return cleaned_line


def collapse_blank_lines(lines):
    collapsed = []

    for line in lines:
        if line:
            collapsed.append(line)
            continue

        if collapsed and collapsed[-1] != "":
            collapsed.append("")

    while collapsed and collapsed[0] == "":
        collapsed.pop(0)
    while collapsed and collapsed[-1] == "":
        collapsed.pop()

    return "\n".join(collapsed).strip()


def remove_foreign_links_and_contacts(text):
    cleaned_lines = []

    for raw_line in strip_language_banner(text).splitlines():
        line = (raw_line or "").strip()

        if not line:
            cleaned_lines.append("")
            continue

        if line in TOKEN_ONLY_LINES:
            cleaned_lines.append(line)
            continue

        if STANDALONE_CODE_PATTERN.fullmatch(line):
            continue

        if has_partner_hint(line):
            partner_line = sanitize_partner_line(line)
            if partner_line:
                cleaned_lines.append(partner_line)
            continue

        had_link_or_handle = bool(URL_PATTERN.search(line) or HANDLE_PATTERN.search(line))
        line = URL_PATTERN.sub("", line)
        line = HANDLE_PATTERN.sub("", line)
        line = re.sub(r"[ \t]{2,}", " ", line)
        line = line.strip(" -–—|•·")

        if had_link_or_handle and len(line.split()) <= 2:
            continue
        if line.lower() in {"source", "fonte", "canal", "channel", "telegram"}:
            continue
        if line:
            cleaned_lines.append(line)

    return collapse_blank_lines(cleaned_lines)


def normalize_post_text(text):
    body = (text or "").replace("\u200b", "").replace("\xa0", " ").strip()
    body = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", body)
    body = re.sub(r"\s*```$", "", body)
    body = remove_foreign_links_and_contacts(body)
    body = replace_foreign_bookmaker_mentions(body)
    body = re.sub(r"[ \t]{2,}", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def sanitize_source_text(text):
    return normalize_post_text(text)


def source_has_partner_context(text):
    for raw_line in (text or "").splitlines():
        line = (raw_line or "").strip()
        if not line:
            continue
        if STANDALONE_CODE_PATTERN.fullmatch(line):
            continue
        if has_partner_hint(line):
            return True
    return False


def add_partner_lines(text):
    body = (text or "").strip()
    partner_tokens = [token for token, label, url in PARTNER_LINE_TOKENS if token and label and url]

    if not partner_tokens:
        return body

    if any(token in body for token in partner_tokens):
        return body

    if FALLBACK_BOOKMAKER_NAME.lower() in body.lower():
        return body

    partner_block = "\n".join(partner_tokens)
    if not body:
        return partner_block

    return f"{body}\n\n{partner_block}".strip()


def should_attach_buttons(include_partner_lines):
    return bool(build_reply_markup()) and not include_partner_lines


def build_final_post_text(post_data, use_ai=True):
    source_text = post_data.get("text", "") or ""
    rewritten_text = process_text_with_ai(source_text) if use_ai else normalize_post_text(source_text)
    include_partner_lines = source_has_partner_context(source_text)
    media_paths = post_data.get("photo_paths") or []
    is_album = post_data.get("media_count", len(media_paths)) > 1
    final_text = finalize_post_text(
        rewritten_text,
        is_album=is_album,
        include_partner_lines=include_partner_lines,
    )
    final_text = add_thematic_emojis(final_text)
    return final_text, should_attach_buttons(include_partner_lines)


def apply_promocode_rule(text, force=False):
    text = (text or "").strip()
    promo_line_pattern = re.compile(
        r"(?im)^.*(?:promo\s*code|promocode|promokod|promo-code|c[oó]digo(?:\s+promocional)?)\s*[:ï¼š\-â€“â€”]?\s*.*$"
    )

    if promo_line_pattern.search(text):
        return promo_line_pattern.sub(PROMOCODE_TEXT, text).strip()

    if not text:
        return PROMOCODE_TEXT if force else ""

    if force:
        return f"{text}\n\n{PROMOCODE_TEXT}".strip()

    return text


def finalize_post_text(text, is_album=False, include_partner_lines=False):
    body = normalize_post_text(text)

    body = apply_promocode_rule(body, force=include_partner_lines)
    if is_album:
        body = add_album_footer(body)
    if include_partner_lines:
        body = add_partner_lines(body)
    return body


def choose_line_emoji(line):
    lowered = (line or "").lower()

    if "apk" in lowered:
        return "📲"
    if "bonus" in lowered or "bônus" in lowered or "promo" in lowered or "promocode" in lowered or "promokod" in lowered or "código promocional" in lowered or "codigo promocional" in lowered:
        return "🎁"
    if "cadastre" in lowered or "cadastro" in lowered or "register" in lowered:
        return "🚀"
    if "1xbet" in lowered or "linebet" in lowered or "dbbet" in lowered or "betkom" in lowered:
        return "🔥"
    if "stavka" in lowered or "ставк" in lowered or "express" in lowered or "экспресс" in lowered:
        return "🎯"
    if "futbol" in lowered or "football" in lowered or "futebol" in lowered or "футбол" in lowered:
        return "⚽"
    if "tennis" in lowered or "теннис" in lowered:
        return "🎾"
    if "basket" in lowered or "баскет" in lowered:
        return "🏀"
    if "yuklab" in lowered or "скач" in lowered or "download" in lowered or "baixar" in lowered:
        return "⬇️"
    if "koeff" in lowered or "коэфф" in lowered or "kf" in lowered:
        return "💎"
    return "✨"


def add_thematic_emojis(text):
    lines = [(line or "").strip() for line in (text or "").splitlines()]
    styled_lines = []

    for line in lines:
        if not line:
            continue
        if line in TOKEN_ONLY_LINES:
            styled_lines.append(line)
            continue
        if re.match(r"^[\W_]*[\U0001F300-\U0001FAFF]", line):
            styled_lines.append(line)
            continue
        styled_lines.append(f"{choose_line_emoji(line)} {line}")

    return "\n".join(styled_lines).strip()


def process_text_with_ai(text):
    if not text:
        return text

    text = sanitize_source_text(text)

    if not AI_ENABLED:
        return normalize_post_text(text)

    if not AI_API_KEY:
        print("AI Ð²Ñ‹ÐºÐ»ÑŽÑ‡ÐµÐ½: Ð½Ðµ Ð½Ð°Ð¹Ð´ÐµÐ½ AI_API_KEY, Ð¾Ñ‚Ð¿Ñ€Ð°Ð²Ð»ÑÑŽ Ð¸ÑÑ…Ð¾Ð´Ð½Ñ‹Ð¹ Ñ‚ÐµÐºÑÑ‚")
        return normalize_post_text(text)

    user_prompt = text

    system_prompt = (
        f"{AI_STYLE_PROMPT}\n\n"
        f"Write the final result only in {AI_TARGET_LANG}. "
        "Never print headings like 'Язык результата' or 'Result language'. "
        "Keep bright normal unicode emojis in the text. "
        "Replace premium or custom emojis with bright normal unicode emojis that match the meaning. "
        "Use emojis in every meaningful line when it looks natural. "
        "APK lines should look vivid with phone, android, download emojis. "
        "Bonus or promocode lines should look vivid with gift, ticket, fire, money emojis. "
        "Sports lines should use fitting sports emojis. "
        "Keep facts, teams, odds, promo meaning, and useful details. "
        "Remove filler words and make the text cleaner and nicer. "
        "Preserve readable spacing and blank lines between logical blocks. "
        "Delete чужие ссылки, чужие Telegram контакты, и чужие call-to-action lines. "
        "Do not add footer links or bonus buttons text. "
        "Return only the main rewritten body."
    )

    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90,
        )
        data = response.json()

        if response.status_code != 200:
            print("AI Ð¾ÑˆÐ¸Ð±ÐºÐ°:", response.status_code, data)
            return normalize_post_text(text)

        ai_text = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not ai_text:
            print("AI Ð²ÐµÑ€Ð½ÑƒÐ» Ð¿ÑƒÑÑ‚Ð¾Ð¹ Ñ‚ÐµÐºÑÑ‚, Ð¾Ñ‚Ð¿Ñ€Ð°Ð²Ð»ÑÑŽ Ð¸ÑÑ…Ð¾Ð´Ð½Ñ‹Ð¹")
            return normalize_post_text(text)

        print("AI Ñ‚ÐµÐºÑÑ‚ Ð¿Ð¾Ð´Ð³Ð¾Ñ‚Ð¾Ð²Ð»ÐµÐ½")
        return normalize_post_text(ai_text)

    except Exception as e:
        print("AI Ð¾ÑˆÐ¸Ð±ÐºÐ°:", str(e))
        return normalize_post_text(text)



def send_text(text, with_buttons=False, chat_id=None, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    normalized_text = text

    if text in {"ðŸ‘‡ Ð‘Ð¾Ð½ÑƒÑÐ½Ñ‹Ðµ ÑÑÑ‹Ð»ÐºÐ¸", "Ã°Å¸â€˜â€¡ Ãâ€˜ÃÂ¾ÃÂ½Ã‘Æ’Ã‘ÂÃÂ½Ã‘â€¹ÃÂµ Ã‘ÂÃ‘ÂÃ‘â€¹ÃÂ»ÃÂºÃÂ¸"}:
        normalized_text = BONUS_BUTTON_MESSAGE

    payload = {
        "chat_id": chat_id or TARGET_CHANNEL,
        "text": prepare_telegram_text(normalized_text),
        "disable_web_page_preview": True,
        "parse_mode": "HTML",
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup
    elif with_buttons:
        button_markup = build_reply_markup()
        if button_markup:
            payload["reply_markup"] = button_markup

    return requests.post(url, json=payload, timeout=60)



def send_one_photo(photo_path, caption, with_buttons=False, chat_id=None, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    data = {
        "chat_id": chat_id or TARGET_CHANNEL,
        "caption": prepare_telegram_text(caption, limit=1024),
        "parse_mode": "HTML",
    }

    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    elif with_buttons:
        button_markup = build_reply_markup()
        if button_markup:
            data["reply_markup"] = json.dumps(button_markup, ensure_ascii=False)

    with open(photo_path, "rb") as photo_file:
        files = {"photo": photo_file}
        return requests.post(url, data=data, files=files, timeout=120)


def send_one_video(video_path, caption, with_buttons=False, chat_id=None, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo"

    data = {
        "chat_id": chat_id or TARGET_CHANNEL,
        "caption": prepare_telegram_text(caption, limit=1024),
        "parse_mode": "HTML",
        "supports_streaming": True,
    }

    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup, ensure_ascii=False)
    elif with_buttons:
        button_markup = build_reply_markup()
        if button_markup:
            data["reply_markup"] = json.dumps(button_markup, ensure_ascii=False)

    with open(video_path, "rb") as video_file:
        files = {"video": video_file}
        return requests.post(url, data=data, files=files, timeout=240)


def is_video_path(file_path):
    extension = os.path.splitext((file_path or "").lower())[1]
    return extension in VIDEO_EXTENSIONS



def send_media_group(photo_paths, caption, chat_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMediaGroup"

    media = []
    opened_files = {}

    try:
        for i, photo_path in enumerate(photo_paths):
            file_key = f"media{i}"
            opened_files[file_key] = open(photo_path, "rb")

            item = {
                "type": "video" if is_video_path(photo_path) else "photo",
                "media": f"attach://{file_key}",
            }

            if i == 0 and caption:
                item["caption"] = prepare_telegram_text(caption, limit=1024)
                item["parse_mode"] = "HTML"

            media.append(item)

        data = {
            "chat_id": chat_id or TARGET_CHANNEL,
            "media": json.dumps(media, ensure_ascii=False),
        }

        return requests.post(url, data=data, files=opened_files, timeout=180)

    finally:
        for f in opened_files.values():
            f.close()


def send_poll(question, options, chat_id=None, is_anonymous=False, allows_multiple_answers=False):
    payload = {
        "chat_id": chat_id or TARGET_CHANNEL,
        "question": question[:300],
        "options": options[:10],
        "is_anonymous": is_anonymous,
        "allows_multiple_answers": allows_multiple_answers,
    }
    return bot_api("sendPoll", payload)



def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}



def save_state(state):
    os.makedirs("data", exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def load_pending():
    if not os.path.exists(PENDING_FILE):
        return {}

    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_pending(pending):
    os.makedirs("data", exist_ok=True)
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)


def bot_api(method, payload):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    return requests.post(url, json=payload, timeout=60)



def get_post_key(message, source_key=None):
    if message.grouped_id:
        base_key = f"group_{message.grouped_id}"
    else:
        base_key = f"msg_{message.id}"

    if source_key:
        return f"{source_key}:{base_key}"

    return base_key


def utf16_offset_to_index(text, offset):
    if offset <= 0:
        return 0

    units_seen = 0
    for index, char in enumerate(text):
        char_units = 2 if ord(char) > 0xFFFF else 1
        if units_seen + char_units > offset:
            return index
        units_seen += char_units
        if units_seen == offset:
            return index + 1

    return len(text)


def choose_custom_emoji_replacement(text, index):
    line_start = text.rfind("\n", 0, index) + 1
    line_end = text.find("\n", index)
    if line_end == -1:
        line_end = len(text)

    line = text[line_start:line_end].lower()

    if "express" in line or "ekspress" in line or "ÑÐºÑÐ¿Ñ€ÐµÑÑ" in line:
        return "🔥"
    if "vip" in line:
        return "👑"
    if "1xbet" in line or "1x" in line:
        return "💙"
    if "dbbet" in line or "db bet" in line:
        return "🖤"
    if "betkom" in line:
        return "🟢"
    if "promo" in line or "promokod" in line or "kod:" in line or "ÐºÐ¾Ð´" in line:
        return "🎟️"
    if "bonus" in line or "aksiya" in line or "akciya" in line or "Ð°ÐºÑ†Ð¸Ñ" in line:
        return "🎁"
    if "apk" in line:
        return "📲"
    if "football" in line or "futbol" in line or "Ñ„ÑƒÑ‚Ð±Ð¾Ð»" in line:
        return "⚽"
    if "basket" in line or "Ð±Ð°ÑÐºÐµÑ‚" in line:
        return "🏀"
    if "tennis" in line or "Ñ‚ÐµÐ½Ð½Ð¸Ñ" in line:
        return "🎾"

    return ""


def replace_custom_emojis(text, entities):
    if not text or not entities:
        return text

    replacements = []
    for entity in entities:
        if entity.__class__.__name__ != "MessageEntityCustomEmoji":
            continue

        start = utf16_offset_to_index(text, entity.offset)
        end = utf16_offset_to_index(text, entity.offset + entity.length)
        replacement = choose_custom_emoji_replacement(text, start)
        replacements.append((start, end, replacement))

    if not replacements:
        return text

    for start, end, replacement in sorted(replacements, reverse=True):
        before = text[:start]
        after = text[end:]
        prefix = "" if not before or before.endswith((" ", "\n")) else " "
        suffix = "" if not after or after.startswith((" ", "\n", ".", ",", ":", ";", "!", "?")) else " "
        text = before + prefix + replacement + suffix + after

    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    print("Custom emoji replaced:", len(replacements))
    return text


def get_message_text(message):
    text = message.raw_text or ""
    return replace_custom_emojis(text, getattr(message, "entities", None))


def is_service_message(message):
    return getattr(message, "action", None) is not None


def get_poll_data(message):
    media = getattr(message, "media", None)
    poll_wrapper = getattr(media, "poll", None)
    poll = getattr(poll_wrapper, "poll", None)

    if not poll:
        return None

    answers = []
    for answer in getattr(poll, "answers", []) or []:
        answer_text = getattr(answer, "text", "")
        if answer_text:
            answers.append(answer_text)

    if len(answers) < 2:
        return None

    question = getattr(poll, "question", "") or ""
    return {
        "question": question,
        "options": answers,
        "multiple_choice": bool(getattr(poll, "multiple_choice", False)),
        "is_quiz": bool(getattr(poll, "quiz", False)),
    }


def has_video_media(message):
    if getattr(message, "video", None):
        return True

    media = getattr(message, "media", None)
    document = getattr(media, "document", None)
    mime_type = getattr(document, "mime_type", "") if document else ""
    return mime_type.startswith("video/")


def has_downloadable_image(message):
    if getattr(message, "photo", None):
        return True

    media = getattr(message, "media", None)
    document = getattr(media, "document", None)
    mime_type = getattr(document, "mime_type", "") if document else ""
    return mime_type.startswith("image/")


def has_file_media(message):
    media = getattr(message, "media", None)
    document = getattr(media, "document", None)
    if not document:
        return False

    mime_type = getattr(document, "mime_type", "") or ""
    if mime_type.startswith("image/") or mime_type.startswith("video/"):
        return False
    return True


def has_supported_media(message):
    return has_downloadable_image(message) or has_video_media(message)


def should_skip_post(messages):
    post_messages = messages or []
    if not post_messages:
        return True

    if any(is_service_message(message) for message in post_messages):
        print("Skip reason: service message")
        return True

    if any(get_poll_data(message) for message in post_messages):
        print("Skip reason: poll")
        return True

    if any(has_file_media(message) for message in post_messages):
        print("Skip reason: file")
        return True

    if count_supported_media(post_messages) == 0 and not any(get_message_text(message).strip() for message in post_messages):
        print("Skip reason: empty post")
        return True

    return False


def cleanup_photo_paths(photo_paths):
    for photo_path in set(photo_paths or []):
        if not photo_path:
            continue
        try:
            if os.path.exists(photo_path):
                os.remove(photo_path)
        except Exception as e:
            print("Cleanup warning:", str(e))


def cleanup_temp_media_dir():
    os.makedirs("data", exist_ok=True)
    temp_prefixes = ("photo_", "document_")
    temp_suffixes = {".jpg", ".jpeg", ".png", ".webp", ".gif", *VIDEO_EXTENSIONS}

    for file_name in os.listdir("data"):
        if not file_name.startswith(temp_prefixes):
            continue
        if os.path.splitext(file_name.lower())[1] not in temp_suffixes:
            continue

        file_path = os.path.join("data", file_name)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print("Startup cleanup warning:", str(e))


async def get_latest_post_key(client, entity, source_key=None):
    messages = await client.get_messages(entity, limit=1)
    if not messages:
        return None
    return get_post_key(messages[0], source_key=source_key)


async def ensure_client_connected(client):
    if client.is_connected():
        return True

    print("Telethon disconnected, trying to reconnect...")

    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("Reconnect failed: session is not authorized")
            return False

        print("Telethon reconnected")
        return True
    except Exception as e:
        print("Reconnect error:", str(e))
        return False


async def resolve_source_entity(client, source_ref):
    candidates = [source_ref]
    raw_value = str(source_ref).strip()

    if re.fullmatch(r"-?\d+", raw_value):
        if raw_value.startswith("-100"):
            channel_id = int(raw_value[4:])
        else:
            channel_id = abs(int(raw_value))
        candidates.extend([raw_value, PeerChannel(channel_id)])

    last_error = None

    for candidate in candidates:
        try:
            return await client.get_entity(candidate)
        except Exception as exc:
            last_error = exc

    try:
        await client.get_dialogs(limit=None)
    except Exception:
        pass

    for candidate in candidates:
        try:
            return await client.get_entity(candidate)
        except Exception as exc:
            last_error = exc

    raise last_error


async def rebuild_post_media(client, entity, post_data):
    photo_paths = post_data.get("photo_paths") or []
    if photo_paths and all(os.path.exists(path) for path in photo_paths):
        return post_data

    message_id = post_data.get("source_message_id")
    if not message_id:
        return post_data

    source_message = await client.get_messages(entity, ids=message_id)
    if not source_message:
        return post_data

    post_messages = [source_message]
    if source_message.grouped_id:
        nearby_ids = list(range(max(1, message_id - 10), message_id + 11))
        nearby_messages = await client.get_messages(entity, ids=nearby_ids)
        album_messages = [
            message
            for message in nearby_messages
            if message and message.grouped_id == source_message.grouped_id
        ]
        if album_messages:
            album_messages.sort(key=lambda message: message.id)
            post_messages = album_messages

    rebuilt_paths = []
    for message in post_messages:
        if has_supported_media(message):
            photo_path = await client.download_media(message, file="data/")
            if photo_path:
                rebuilt_paths.append(photo_path)

    rebuilt_post = dict(post_data)
    rebuilt_post["photo_paths"] = rebuilt_paths
    return rebuilt_post


def count_supported_media(messages):
    return sum(1 for message in messages if has_supported_media(message))



async def get_post_data(client, entity, source_key=None, source_ref=None):
    messages = await client.get_messages(entity, limit=1)

    if not messages:
        return None

    last_msg = messages[0]
    post_messages = [last_msg]
    text = get_message_text(last_msg)

    if last_msg.grouped_id:
        recent_messages = await client.get_messages(entity, limit=20)
        album_messages = [m for m in recent_messages if m.grouped_id == last_msg.grouped_id]
        album_messages.sort(key=lambda m: m.id)

        if album_messages:
            post_messages = album_messages
            for m in album_messages:
                if m.raw_text:
                    text = get_message_text(m)
                    break

    if should_skip_post(post_messages):
        return None

    effective_source_key = source_key or get_source_key(entity, source_ref)

    return {
        "key": get_post_key(last_msg, source_key=effective_source_key),
        "text": text,
        "photo_paths": [],
        "media_count": count_supported_media(post_messages),
        "source_message_id": last_msg.id,
        "source_key": effective_source_key,
        "source_ref": str(source_ref if source_ref is not None else effective_source_key),
        "source_title": getattr(entity, "title", "") or "",
    }


async def build_post_data_from_messages(client, messages, source_key=None, source_ref=None, source_title=""):
    if not messages:
        return None

    post_messages = sorted(messages, key=lambda m: m.id)
    last_msg = post_messages[-1]
    text = ""

    if should_skip_post(post_messages):
        return None

    for message in post_messages:
        if message.raw_text:
            text = get_message_text(message)
            break

    if not text:
        text = get_message_text(last_msg)

    return {
        "key": get_post_key(last_msg, source_key=source_key),
        "text": text,
        "photo_paths": [],
        "media_count": count_supported_media(post_messages),
        "source_message_id": last_msg.id,
        "source_key": source_key,
        "source_ref": str(source_ref if source_ref is not None else source_key or ""),
        "source_title": source_title or "",
    }


async def get_new_posts_data(client, entity, last_post_key=None, limit=50, source_key=None, source_ref=None):
    messages = await client.get_messages(entity, limit=limit)

    if not messages:
        return []

    effective_source_key = source_key or get_source_key(entity, source_ref)
    source_title = getattr(entity, "title", "") or ""
    grouped_messages = {}
    ordered_keys = []

    for message in messages:
        post_key = get_post_key(message, source_key=effective_source_key)
        if post_key not in grouped_messages:
            grouped_messages[post_key] = []
            ordered_keys.append(post_key)
        grouped_messages[post_key].append(message)

    new_keys = []
    for post_key in ordered_keys:
        if last_post_key and post_key == last_post_key:
            break
        new_keys.append(post_key)

    new_keys.reverse()

    posts = []
    for post_key in new_keys:
        post_data = await build_post_data_from_messages(
            client,
            grouped_messages[post_key],
            source_key=effective_source_key,
            source_ref=source_ref,
            source_title=source_title,
        )
        if post_data:
            posts.append(post_data)

    posts.sort(key=lambda post: post.get("source_message_id", 0))
    return posts

def response_ok(response):
    try:
        data = response.json()
        return response.status_code == 200 and data.get("ok") is True
    except Exception:
        return response.status_code == 200

def publish_post(post_data, use_ai=True):
    text = post_data.get("processed_text")
    with_buttons = post_data.get("with_buttons")
    if text is None or with_buttons is None:
        text, with_buttons = build_final_post_text(post_data, use_ai=use_ai)

    photo_paths = post_data.get("photo_paths", [])

    if len(photo_paths) == 0:
        response = send_text(text, with_buttons=with_buttons)
        print("ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÐµÐ½ Ñ‚ÐµÐºÑÑ‚:", response.status_code)
        print(response.text)
        return response_ok(response)

    if len(photo_paths) == 1:
        media_path = photo_paths[0]
        if is_video_path(media_path):
            response = send_one_video(media_path, text, with_buttons=with_buttons)
            print("ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¾ 1 Ð²Ð¸Ð´ÐµÐ¾:", response.status_code)
        else:
            response = send_one_photo(media_path, text, with_buttons=with_buttons)
            print("ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÐµÐ½Ð¾ 1 Ñ„Ð¾Ñ‚Ð¾:", response.status_code)
        print(response.text)
        return response_ok(response)

    response = send_media_group(photo_paths, text)
    print(f"ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÐµÐ½ Ð°Ð»ÑŒÐ±Ð¾Ð¼ ({len(photo_paths)} media):", response.status_code)
    print(response.text)

    if not response_ok(response):
        return False

    if not with_buttons:
        return True

    buttons_response = send_text(BONUS_BUTTON_MESSAGE, with_buttons=True)
    print("ÐžÑ‚Ð¿Ñ€Ð°Ð²Ð»ÐµÐ½Ñ‹ ÐºÐ½Ð¾Ð¿ÐºÐ¸:", buttons_response.status_code)
    print(buttons_response.text)
    return response_ok(buttons_response)


def send_post_to_review(post_data):
    if not REVIEW_MODE:
        return False

    text = post_data.get("processed_text", post_data.get("text", ""))
    photo_paths = post_data["photo_paths"]
    moderation_markup = build_moderation_markup(post_data["key"])

    if len(photo_paths) == 0:
        response = send_text(
            text,
            chat_id=REVIEW_CHANNEL_ID,
            reply_markup=moderation_markup,
        )
        print("Review text sent:", response.status_code)
        print(response.text)
        return response_ok(response)

    if len(photo_paths) == 1:
        media_path = photo_paths[0]
        if is_video_path(media_path):
            response = send_one_video(
                media_path,
                text,
                chat_id=REVIEW_CHANNEL_ID,
                reply_markup=moderation_markup,
            )
            print("Review video sent:", response.status_code)
        else:
            response = send_one_photo(
                media_path,
                text,
                chat_id=REVIEW_CHANNEL_ID,
                reply_markup=moderation_markup,
            )
            print("Review photo sent:", response.status_code)
        print(response.text)
        return response_ok(response)

    response = send_media_group(photo_paths, text, chat_id=REVIEW_CHANNEL_ID)
    print("Review album sent:", response.status_code)
    print(response.text)

    if not response_ok(response):
        return False

    buttons_response = send_text(
        f"Moderation for {post_data['key']}",
        chat_id=REVIEW_CHANNEL_ID,
        reply_markup=moderation_markup,
    )
    print("Review buttons sent:", buttons_response.status_code)
    print(buttons_response.text)
    return response_ok(buttons_response)


def queue_post_for_review(post_data):
    pending = load_pending()
    prepared_post = dict(post_data)
    prepared_post["processed_text"], prepared_post["with_buttons"] = build_final_post_text(
        post_data,
        use_ai=True,
    )
    prepared_post["status"] = "pending"

    success = send_post_to_review(prepared_post)
    cleanup_photo_paths(prepared_post.get("photo_paths"))
    if not success:
        return False

    prepared_post["photo_paths"] = []
    pending[prepared_post["key"]] = prepared_post
    save_pending(pending)
    return True


def answer_callback(callback_query_id, text):
    bot_api("answerCallbackQuery", {
        "callback_query_id": callback_query_id,
        "text": text,
    })


async def handle_moderation_updates(client, source_entities, state):
    if not REVIEW_MODE:
        return

    payload = {
        "timeout": 1,
        "allowed_updates": ["callback_query"],
    }

    if state.get("bot_update_offset"):
        payload["offset"] = state["bot_update_offset"]

    response = bot_api("getUpdates", payload)
    if not response_ok(response):
        print("getUpdates error:", response.status_code, response.text)
        return

    updates = response.json().get("result", [])
    if not updates:
        return

    pending = load_pending()

    for update in updates:
        state["bot_update_offset"] = update["update_id"] + 1
        callback = update.get("callback_query")
        if not callback:
            continue

        action_data = callback.get("data", "")
        if ":" not in action_data:
            continue

        action, post_key = action_data.split(":", 1)
        post_data = pending.get(post_key)

        if not post_data:
            answer_callback(callback["id"], "Post not found")
            continue

        if post_data.get("status") != "pending":
            answer_callback(callback["id"], f"Already {post_data.get('status')}")
            continue

        if action == "approve":
            source_key = str(post_data.get("source_key", "")).strip()
            source_entity = source_entities.get(source_key)
            if not source_entity:
                answer_callback(callback["id"], "Source not found")
                continue

            prepared_post = await rebuild_post_media(client, source_entity, post_data)
            success = publish_post(prepared_post, use_ai=False)
            cleanup_photo_paths(prepared_post.get("photo_paths"))
            if success:
                post_data["status"] = "approved"
                post_data["photo_paths"] = []
                pending[post_key] = post_data
                save_pending(pending)
                answer_callback(callback["id"], "Approved and published")
            else:
                answer_callback(callback["id"], "Publish error")

        elif action == "reject":
            post_data["status"] = "rejected"
            cleanup_photo_paths(post_data.get("photo_paths"))
            post_data["photo_paths"] = []
            pending[post_key] = post_data
            save_pending(pending)
            answer_callback(callback["id"], "Rejected")

    save_state(state)



async def main():
    if not API_ID:
        print("Error: TG_API_ID is missing")
        return

    if not API_HASH:
        print("Error: TG_API_HASH is missing")
        return

    if not SOURCE_CHANNELS:
        print("Error: SOURCE_CHANNEL is missing")
        return

    if not TARGET_CHANNEL:
        print("Error: TARGET_CHANNEL is missing")
        return

    if not BOT_TOKEN:
        print("Error: BOT_TOKEN is missing")
        return

    if SESSION_STRING:
        client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
    else:
        client = TelegramClient("data/session_name", int(API_ID), API_HASH)

    await client.start()
    cleanup_temp_media_dir()
    print("Telethon connected")
    print("Auto mode started")
    print("Review mode:", "ON" if REVIEW_MODE else "OFF")
    if REVIEW_MODE:
        print("Review channel:", safe_console_text(REVIEW_CHANNEL_ID))

    state = load_state()
    state_changed = migrate_state_shape(state)
    source_descriptors = []
    source_entities = {}

    try:
        for source_ref in SOURCE_CHANNELS:
            entity = await resolve_source_entity(client, source_ref)
            source_key = get_source_key(entity, source_ref)
            source_signature = get_source_signature(entity, source_ref)
            source_title = getattr(entity, "title", "no title")

            source_descriptors.append({
                "entity": entity,
                "source_ref": source_ref,
                "source_key": source_key,
                "source_signature": source_signature,
                "source_title": source_title,
            })
            source_entities[source_key] = entity

            print("SOURCE_CHANNEL:", safe_console_text(source_ref))
            print("Source found:", safe_console_text(source_title))

        if not source_descriptors:
            print("Error: no valid source channels found")
            await client.disconnect()
            return

        pending_reset_needed = False

        for source_info in source_descriptors:
            first_post_key = await get_latest_post_key(
                client,
                source_info["entity"],
                source_key=source_info["source_key"],
            )
            source_state = get_source_state_bucket(state, source_info["source_key"])

            if not first_post_key:
                print("No messages in source channel:", safe_console_text(source_info["source_ref"]))
                continue

            if source_state.get("source_signature") != source_info["source_signature"]:
                source_state["source_signature"] = source_info["source_signature"]
                source_state["last_post_key"] = first_post_key
                state_changed = True
                pending_reset_needed = True
                print("Source changed: current last post saved, waiting for new posts")
                continue

            if not source_state.get("last_post_key"):
                source_state["last_post_key"] = first_post_key
                source_state["source_signature"] = source_info["source_signature"]
                state_changed = True
                print("First start: current last post saved, waiting for new posts")

        if pending_reset_needed:
            save_pending({})

        if state_changed:
            save_state(state)

        while True:
            try:
                if not await ensure_client_connected(client):
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue

                await handle_moderation_updates(client, source_entities, state)
                found_new_posts = False

                for source_info in source_descriptors:
                    source_state = get_source_state_bucket(state, source_info["source_key"])
                    last_post_key = source_state.get("last_post_key")
                    new_posts = await get_new_posts_data(
                        client,
                        source_info["entity"],
                        last_post_key,
                        source_key=source_info["source_key"],
                        source_ref=source_info["source_ref"],
                    )

                    print(
                        f"New posts found for {safe_console_text(source_info['source_ref'])}:",
                        len(new_posts),
                    )
                    print("State key:", safe_console_text(last_post_key))

                    if not new_posts:
                        continue

                    found_new_posts = True

                    for post_data in new_posts:
                        print(
                            f"Processing post from {safe_console_text(source_info['source_ref'])}:",
                            post_data["key"],
                        )
                        if REVIEW_MODE:
                            print("Route: review channel")
                            prepared_post = await rebuild_post_media(client, source_info["entity"], post_data)
                            success = queue_post_for_review(prepared_post)
                        else:
                            prepared_post = await rebuild_post_media(client, source_info["entity"], post_data)
                            success = publish_post(prepared_post)
                            cleanup_photo_paths(prepared_post.get("photo_paths"))

                        if success:
                            source_state["last_post_key"] = post_data["key"]
                            source_state["source_signature"] = source_info["source_signature"]
                            save_state(state)

                if not found_new_posts:
                    print("No new posts")
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue

            except Exception as e:
                print("Loop error:", str(e))
                await asyncio.sleep(CHECK_INTERVAL)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
