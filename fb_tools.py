import re
import urllib.request
import urllib.parse

def check_fb_uid_live(uid):
    """
    Checks if a Facebook UID has an active, accessible profile.
    Returns (is_live: bool, details: str).
    """
    if not uid or not str(uid).isdigit():
        return False, "Invalid numeric UID"
        
    url = f"https://graph.facebook.com/{uid}/picture?type=normal"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=5) as res:
            final_url = res.geturl()
            if "static" in final_url or "fbcdn" in final_url or "facebook" in final_url:
                return True, "🟢 Live & Active Profile"
            return True, "🟢 Live"
    except urllib.error.HTTPError as e:
        if e.code in [404, 400]:
            return False, "🔴 Dead / Checkpoint (Human Khaiche)"
        return False, f"⚠️ Check failed (HTTP {e.code})"
    except Exception as e:
        return None, f"⚠️ Ping error: {str(e)}"


def extract_fb_lite_uid(raw_text):
    """
    Extracts numeric UID from FB Lite profile links, share links, or long URL strings.
    Handles:
    - https://www.facebook.com/profile.php?id=100084729104821&mibextid=ZbWKwL
    - https://m.facebook.com/profile.php?id=61552391029381&_rdr&paipv=...
    - https://lite.facebook.com/profile.php?id=...
    - fb://profile/100084729104821
    - facebook.com/100084729104821
    - Raw text with long URLs inside
    """
    if not raw_text:
        return None
    text = raw_text.strip()
    
    # 1. Match ?id=1000... or &id=1000...
    m_id = re.search(r'[?&]id=(\d{4,})', text)
    if m_id:
        return m_id.group(1)
        
    # 2. Match profile/1000... or /user/1000...
    m_prof = re.search(r'(?:profile|user)/(\d{4,})', text)
    if m_prof:
        return m_prof.group(1)
        
    # 3. Match facebook.com/100084729104821
    m_num = re.search(r'facebook\.com/(\d{4,})', text)
    if m_num:
        return m_num.group(1)
        
    # 4. Direct numeric digits
    clean_digits = re.sub(r'\D', '', text)
    if text.isdigit() and len(text) >= 4:
        return text

    # 5. Handle share links (e.g. facebook.com/share/...)
    if "facebook.com/share/" in text:
        m_share_num = re.search(r'facebook\.com/share/[^/]+/(\d{4,})', text)
        if m_share_num:
            return m_share_num.group(1)
            
        # Extract full URL and resolve redirect
        m_url = re.search(r'https?://[^\s]+', text)
        target_url = m_url.group(0) if m_url else text
        try:
            req = urllib.request.Request(
                target_url,
                headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"}
            )
            with urllib.request.urlopen(req, timeout=4) as res:
                final = res.geturl()
                m_sub = re.search(r'[?&]id=(\d{4,})', final)
                if m_sub:
                    return m_sub.group(1)
        except Exception:
            pass

    # 6. Vanity username (facebook.com/username?mibextid=...)
    m_user = re.search(r'facebook\.com/([^/?#\s]+)', text)
    if m_user:
        uname = m_user.group(1).strip()
        if uname.lower() not in ["profile.php", "share", "watch", "photo", "groups", "story"]:
            if uname.isdigit() and len(uname) >= 4:
                return uname
            # Resolve via Graph
            try:
                g_url = f"https://graph.facebook.com/{uname}/picture?type=normal"
                req = urllib.request.Request(g_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=4) as res:
                    final = res.geturl()
                    m_found = re.search(r'/(\d{8,})[._]', final)
                    if m_found:
                        return m_found.group(1)
            except Exception:
                pass
                
    return None
