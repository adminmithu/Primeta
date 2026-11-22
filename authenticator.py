import re
import time
from datetime import datetime
import pyotp
import base64
import hmac
import hashlib
import struct

# Allow secrets of any length in pyotp (e.g. 16-char / 80-bit Facebook & Google 2FA keys)
try:
    if hasattr(pyotp.otp.OTP, 'min_secret_length_bits'):
        pyotp.otp.OTP.min_secret_length_bits = 0
except Exception:
    pass


def generate_native_totp(secret_b32):
    """
    Standard RFC 6238 TOTP generator.
    Works for any valid Base32 key of any length (80 bits, 128 bits, 160 bits, etc.).
    """
    clean_secret = secret_b32.strip().replace(" ", "").rstrip("=").upper()
    pad = len(clean_secret) % 8
    if pad != 0:
        clean_secret += "=" * (8 - pad)
    key = base64.b32decode(clean_secret, casefold=True)
    intervals = int(time.time() // 30)
    msg = struct.pack(">Q", intervals)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    o = h[19] & 15
    code = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1000000
    return f"{code:06d}"


def get_progress_bar(remaining, total=30, length=10):
    """Draws visual countdown progress bar: ⏳ Valid: 18s [██████░░░░]"""
    filled = max(0, min(length, int((remaining / total) * length)))
    bar = "█" * filled + "░" * (length - filled)
    return f"⏳ Valid: <b>{remaining}s</b> <code>[{bar}]</code>"


def _sanitize_single(raw_key):
    """Internal helper to sanitize and test a single secret token."""
    if not raw_key:
        return None, None, 0, "Empty secret key provided."

    # 0. Check for otpauth URL or query param secret=
    if "secret=" in raw_key:
        match = re.search(r'[?&]secret=([A-Za-z0-9]+)', raw_key, flags=re.I)
        if match:
            raw_key = match.group(1)

    # 1. Strip common prefixes like '2fa', '/2fa', 'key:', 'secret:', 'totp:', 'code:'
    trimmed = re.sub(r'^(?:/?2fa|key|secret|totp|code)\s*[:=\-]?\s*', '', raw_key.strip(), flags=re.I)
    
    # Strip everything that is not alphanumeric
    clean = re.sub(r'[^A-Za-z0-9]', '', trimmed).strip().upper()
    
    # Must be at least 14 characters and NOT purely numeric (UIDs, passwords, pins are numeric)
    if not clean or len(clean) < 14 or clean.isdigit():
        return None, None, 0, "Invalid length or secret format."

    # A valid Base32 secret must contain letters
    letter_count = sum(1 for c in clean if c.isalpha())
    if letter_count < 4:
        return None, None, 0, "Secret does not contain enough Base32 characters."

    # Generate candidate variations for common OCR/typing errors
    # (0 -> O, 1 -> I or L)
    candidates = [
        clean,
        clean.replace('0', 'O').replace('1', 'I'),
        clean.replace('0', 'O').replace('1', 'L')
    ]

    for cand in candidates:
        # First try native RFC 6238 implementation
        try:
            code = generate_native_totp(cand)
            remaining = 30 - int(time.time() % 30)
            return cand, code, remaining, None
        except Exception:
            pass

        # Fallback to pyotp
        for attempt in [cand, cand + ('=' * ((8 - (len(cand) % 8)) % 8))]:
            try:
                totp = pyotp.TOTP(attempt)
                code = totp.now()
                remaining = 30 - int(time.time() % 30)
                return cand, code, remaining, None
            except Exception:
                pass

    return None, None, 0, "Invalid Base32 secret key."


def sanitize_and_generate(raw_key):
    """
    Sanitizes raw 2FA key and generates TOTP 6-digit code.
    Handles combos (e.g. 'uid|pass|2fakey'), prefixes, otpauth URLs, spaces, hyphens, and OCR errors.
    """
    if not raw_key:
        return None, None, 0, "Empty secret key provided."

    # If pipe-separated combo is passed, check each token to find the 2FA secret
    if "|" in raw_key:
        parts = [p.strip() for p in raw_key.split("|") if p.strip()]
        # Check from last token to first (combos usually place 2FA near the end)
        for p in reversed(parts):
            cand, code, remaining, err = _sanitize_single(p)
            if code:
                return cand, code, remaining, None
        for p in parts:
            cand, code, remaining, err = _sanitize_single(p)
            if code:
                return cand, code, remaining, None

    return _sanitize_single(raw_key)


def parse_and_generate_bulk(text):
    """
    Extracts potential 2FA secret keys from text (supports single line, multiple lines, combos, etc.).
    Returns list of dicts: [{'secret': ..., 'otp': ..., 'remaining': ..., 'valid': True/False, 'error': ...}]
    """
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    results = []
    
    for idx, line in enumerate(lines, 1):
        clean_line = re.sub(r'^\d+[\.\)]\s*', '', line)
        clean_line = re.sub(r'^(?:/?2fa|key|secret|totp|code)\s*[:=\-]?\s*', '', clean_line.strip(), flags=re.I)
        
        # Test line (supports combos like uid|pass|2fakey)
        secret, code, remaining, err = sanitize_and_generate(clean_line)
        if secret and code:
            results.append({
                "index": idx,
                "raw": line,
                "secret": secret,
                "otp": code,
                "remaining": remaining,
                "valid": True,
                "time": datetime.now().strftime("%I:%M %p")
            })
        else:
            results.append({
                "index": idx,
                "raw": line,
                "error": err,
                "valid": False
            })
            
    return results
