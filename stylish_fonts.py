# Unicode offset constants
def _map_chars(text, upper_start, lower_start, digit_start=None, exceptions=None):
    if exceptions is None:
        exceptions = {}
    result = []
    for ch in text:
        if ch in exceptions:
            result.append(exceptions[ch])
        elif 'A' <= ch <= 'Z' and upper_start:
            result.append(chr(upper_start + ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z' and lower_start:
            result.append(chr(lower_start + ord(ch) - ord('a')))
        elif '0' <= ch <= '9' and digit_start:
            result.append(chr(digit_start + ord(ch) - ord('0')))
        else:
            result.append(ch)
    return "".join(result)

def to_sans_bold(text):
    return _map_chars(text, 0x1D5D4, 0x1D5EE, 0x1D7EC)

def to_serif_bold(text):
    return _map_chars(text, 0x1D400, 0x1D41A, 0x1D7CE)

def to_sans_italic(text):
    return _map_chars(text, 0x1D608, 0x1D622)

def to_bold_italic(text):
    return _map_chars(text, 0x1D63C, 0x1D656)

def to_monospace(text):
    return _map_chars(text, 0x1D670, 0x1D68A, 0x1D7F6)

def to_script(text):
    # Mathematical Script has some holes in BMP, using reliable Fraktur or Cursive
    script_upper = 0x1D49C
    script_lower = 0x1D4B6
    # Handling specific standard unicode script exceptions
    exc = {
        'B': 'ℬ', 'E': 'ℰ', 'F': 'ℱ', 'H': 'ℋ', 'I': 'ℐ', 'L': 'ℒ', 'M': 'ℳ', 'R': 'ℛ',
        'e': 'ℯ', 'g': 'ℊ', 'o': 'ℴ'
    }
    return _map_chars(text, script_upper, script_lower, exceptions=exc)

def to_gothic(text):
    exc = {'C': 'ℭ', 'H': 'ℌ', 'I': 'ℑ', 'R': 'ℜ', 'Z': 'ℨ'}
    return _map_chars(text, 0x1D504, 0x1D51E, exceptions=exc)

def to_bubble(text):
    res = []
    for ch in text:
        if 'A' <= ch <= 'Z':
            res.append(chr(0x24B6 + ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z':
            res.append(chr(0x24D0 + ord(ch) - ord('a')))
        elif '1' <= ch <= '9':
            res.append(chr(0x2460 + ord(ch) - ord('1')))
        elif ch == '0':
            res.append('⓪')
        else:
            res.append(ch)
    return "".join(res)

def to_squared(text):
    res = []
    for ch in text:
        if 'A' <= ch <= 'Z':
            res.append(chr(0x1F130 + ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z':
            res.append(chr(0x1F130 + ord(ch.upper()) - ord('A')))
        else:
            res.append(ch)
    return "".join(res)

def to_small_caps(text):
    sc_map = {
        'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ', 'h': 'ʜ',
        'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ',
        'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
        'y': 'ʏ', 'z': 'ᴢ',
        'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ꜰ', 'G': 'ɢ', 'H': 'ʜ',
        'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ', 'O': 'ᴏ', 'P': 'ᴘ',
        'Q': 'ǫ', 'R': 'ʀ', 'S': 'ꜱ', 'T': 'ᴛ', 'U': 'ᴜ', 'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x',
        'Y': 'ʏ', 'Z': 'ᴢ'
    }
    return "".join(sc_map.get(ch, ch) for ch in text)

def to_strikethrough(text):
    return "".join(ch + '\u0336' if ch != ' ' else ' ' for ch in text)

def to_underline(text):
    return "".join(ch + '\u0332' if ch != ' ' else ' ' for ch in text)

def generate_all_styles(text):
    """Returns a list of dicts with all stylish versions."""
    clean = text.strip()
    return [
        {"name": "Sans Bold", "font": to_sans_bold(clean)},
        {"name": "Serif Bold", "font": to_serif_bold(clean)},
        {"name": "Bold Italic", "font": to_bold_italic(clean)},
        {"name": "Sans Italic", "font": to_sans_italic(clean)},
        {"name": "Monospace", "font": to_monospace(clean)},
        {"name": "Cursive Script", "font": to_script(clean)},
        {"name": "Gothic / Fraktur", "font": to_gothic(clean)},
        {"name": "Circled / Bubble", "font": to_bubble(clean)},
        {"name": "Squared Box", "font": to_squared(clean)},
        {"name": "Small Caps", "font": to_small_caps(clean)},
        {"name": "Underline", "font": to_underline(clean)},
        {"name": "Strikethrough", "font": to_strikethrough(clean)},
    ]
