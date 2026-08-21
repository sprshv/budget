import re
from typing import Optional

# Known merchant name mappings: raw pattern (lowercase) → clean name
MERCHANT_MAP = {
    "amazon": "Amazon",
    "amzn": "Amazon",
    "amzn mktp": "Amazon",
    "amazon.com": "Amazon",
    "apple": "Apple",
    "apple.com": "Apple",
    "itunes": "Apple",
    "app store": "Apple App Store",
    "netflix": "Netflix",
    "spotify": "Spotify",
    "hulu": "Hulu",
    "disney+": "Disney+",
    "disneyplus": "Disney+",
    "youtube": "YouTube",
    "google": "Google",
    "google*": "Google",
    "uber": "Uber",
    "uber eats": "Uber Eats",
    "ubereats": "Uber Eats",
    "lyft": "Lyft",
    "doordash": "DoorDash",
    "grubhub": "Grubhub",
    "instacart": "Instacart",
    "walmart": "Walmart",
    "target": "Target",
    "costco": "Costco",
    "whole foods": "Whole Foods",
    "trader joe": "Trader Joe's",
    "kroger": "Kroger",
    "safeway": "Safeway",
    "cvs": "CVS Pharmacy",
    "cvs pharmacy": "CVS Pharmacy",
    "walgreens": "Walgreens",
    "starbucks": "Starbucks",
    "mcdonald": "McDonald's",
    "mcdonalds": "McDonald's",
    "chipotle": "Chipotle",
    "chick-fil-a": "Chick-fil-A",
    "chickfila": "Chick-fil-A",
    "subway": "Subway",
    "dunkin": "Dunkin'",
    "dunkin donuts": "Dunkin'",
    "venmo": "Venmo",
    "paypal": "PayPal",
    "zelle": "Zelle",
    "chase": "Chase",
    "bank of america": "Bank of America",
    "wells fargo": "Wells Fargo",
    "american express": "American Express",
    "amex": "American Express",
    "planet fitness": "Planet Fitness",
    "24 hour fitness": "24 Hour Fitness",
    "la fitness": "LA Fitness",
    "comcast": "Comcast",
    "at&t": "AT&T",
    "verizon": "Verizon",
    "t-mobile": "T-Mobile",
    "tmobile": "T-Mobile",
    "github": "GitHub",
    "openai": "OpenAI",
    "chatgpt": "OpenAI",
    "adobe": "Adobe",
    "microsoft": "Microsoft",
    "dropbox": "Dropbox",
    "slack": "Slack",
    "zoom": "Zoom",
    "airbnb": "Airbnb",
    "expedia": "Expedia",
    "delta": "Delta Air Lines",
    "united airlines": "United Airlines",
    "southwest": "Southwest Airlines",
    "american airlines": "American Airlines",
}

# Regex patterns to strip noise from raw bank descriptions
_STRIP_PATTERNS = [
    r"\*+\d+",           # trailing asterisk + digits (SQ *12345)
    r"#\d+",             # store numbers (#4892)
    r"\bUS\b",           # country suffix
    r"\bUSA\b",
    r"\bINC\.?\b",       # corporate suffixes
    r"\bLLC\.?\b",
    r"\bLTD\.?\b",
    r"\bCORP\.?\b",
    r"\bCO\.?\b",
    r"\d{4,}",           # long numeric sequences (transaction refs)
    r"[A-Z0-9]{8,}",     # long uppercase alphanumeric refs
    r"\s{2,}",           # multiple spaces → single space
]

_STRIP_RE = re.compile("|".join(_STRIP_PATTERNS), re.IGNORECASE)
_SQUARE_RE = re.compile(r"^SQ\s*\*\s*", re.IGNORECASE)
_PAYPAL_RE = re.compile(r"^PAYPAL\s*\*\s*", re.IGNORECASE)
_CHECKCARD_RE = re.compile(r"^(CHECK\s*CARD|DEBIT|PURCHASE|POS|ACH)\s*[-\s]*", re.IGNORECASE)


def normalize_merchant(raw_description: str, plaid_merchant_name: Optional[str] = None) -> str:
    """
    Return a clean, human-readable merchant name.

    Priority:
    1. Plaid's merchant_name if present and not generic
    2. Known merchant dict lookup on cleaned raw description
    3. Regex-cleaned title-cased raw description
    """
    # Priority 1: Plaid's own merchant_name
    if plaid_merchant_name and len(plaid_merchant_name.strip()) > 1:
        cleaned = plaid_merchant_name.strip()
        # Still check our map in case Plaid gives us an abbreviation
        lookup = _lookup_merchant(cleaned)
        return lookup if lookup else cleaned

    if not raw_description:
        return "Unknown"

    # Strip common prefixes
    name = _SQUARE_RE.sub("", raw_description)
    name = _PAYPAL_RE.sub("PayPal — ", name)
    name = _CHECKCARD_RE.sub("", name)

    # Look up in known merchants after basic cleaning
    lookup = _lookup_merchant(name)
    if lookup:
        return lookup

    # Apply strip patterns
    name = _STRIP_RE.sub(" ", name).strip()

    # Look up again after stripping
    lookup = _lookup_merchant(name)
    if lookup:
        return lookup

    # Fall back to title-cased cleaned string
    result = " ".join(word.capitalize() for word in name.split() if word)
    return result if result else "Unknown"


def _lookup_merchant(name: str) -> Optional[str]:
    """Check MERCHANT_MAP using normalized lowercase key."""
    key = name.lower().strip()
    # Exact match
    if key in MERCHANT_MAP:
        return MERCHANT_MAP[key]
    # Prefix match (e.g. "amazon prime" → "Amazon")
    for pattern, clean_name in MERCHANT_MAP.items():
        if key.startswith(pattern) and len(pattern) >= 4:
            return clean_name
    return None
