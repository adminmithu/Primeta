import re
import urllib.parse
from PIL import Image
import io

try:
    import zxingcpp
except ImportError:
    zxingcpp = None

def extract_secret_from_text(raw_text):
    """Extracts base32 secret key from otpauth URL or raw string."""
    if not raw_text:
        return None
    raw_text = raw_text.strip()
    
    # Check if otpauth:// URL
    if raw_text.startswith("otpauth://"):
        try:
            parsed = urllib.parse.urlparse(raw_text)
            query = urllib.parse.parse_qs(parsed.query)
            if "secret" in query:
                return query["secret"][0]
        except Exception:
            pass
        # Fallback regex
        match = re.search(r'[?&]secret=([A-Za-z0-9]+)', raw_text)
        if match:
            return match.group(1)
            
    # Plain secret key
    clean = re.sub(r'[\s\-:_]+', '', raw_text)
    if re.match(r'^[A-Za-z2-7=]{8,}$', clean):
        return clean
        
    return raw_text


def scan_qr_from_bytes(image_bytes):
    """
    Decodes QR code from image bytes.
    Returns (secret_key, full_decoded_text, error_message).
    """
    if zxingcpp is None:
        return None, None, "QR code scanning is currently unavailable: zxing-cpp library is not installed."
        
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        res = zxingcpp.read_barcode(image)
        if not res or not res.text:
            return None, None, "No QR code could be found in the image."
            
        decoded_text = res.text
        secret = extract_secret_from_text(decoded_text)
        return secret, decoded_text, None
    except Exception as e:
        return None, None, f"Error processing image: {str(e)}"


def scan_qr_from_file(file_path):
    """Decodes QR code from image file path."""
    with open(file_path, "rb") as f:
        return scan_qr_from_bytes(f.read())
