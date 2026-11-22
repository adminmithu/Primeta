import random

USER_AGENTS_DB = {
    "iphone": [
        {
            "name": "iPhone 15 Pro Max (iOS 17.5.1 / Safari)",
            "device": "iPhone 15 Pro Max",
            "os": "iOS 17.5.1",
            "browser": "Mobile Safari 17.5",
            "category": "🍏 Apple iPhone",
            "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
        },
        {
            "name": "iPhone 15 Pro (iOS 17.4 / Facebook App)",
            "device": "iPhone 15 Pro",
            "os": "iOS 17.4",
            "browser": "Facebook App (FBIOS)",
            "category": "🍏 Apple iPhone",
            "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/21E219 [FBAN/FBIOS;FBAV/456.0.0.35.109;FBBV/584930129;FBDV/iPhone15,2;FBMD/iPhone;FBSN/iOS;FBSV/17.4;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5]"
        },
        {
            "name": "iPhone 14 (iOS 16.6 / Safari)",
            "device": "iPhone 14",
            "os": "iOS 16.6",
            "browser": "Mobile Safari 16.6",
            "category": "🍏 Apple iPhone",
            "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        },
        {
            "name": "iPhone 13 (iOS 17.2 / Chrome Mobile)",
            "device": "iPhone 13",
            "os": "iOS 17.2",
            "browser": "Chrome Mobile 122.0",
            "category": "🍏 Apple iPhone",
            "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/122.0.6261.89 Mobile/15E148 Safari/604.1"
        }
    ],
    "android": [
        {
            "name": "Samsung Galaxy S24 Ultra (Android 14 / Chrome)",
            "device": "Galaxy S24 Ultra (SM-S928B)",
            "os": "Android 14",
            "browser": "Chrome Mobile 128.0",
            "category": "🤖 Android Mobile",
            "ua": "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.127 Mobile Safari/537.36"
        },
        {
            "name": "Google Pixel 8 Pro (Android 14 / Facebook App)",
            "device": "Google Pixel 8 Pro",
            "os": "Android 14",
            "browser": "Facebook App (Katana)",
            "category": "🤖 Android Mobile",
            "ua": "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro Build/UD1A.231105.004; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/126.0.6478.134 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/469.0.0.50.77;]"
        },
        {
            "name": "Samsung Galaxy S23 (Android 13 / Samsung Browser)",
            "device": "Galaxy S23",
            "os": "Android 13",
            "browser": "Samsung Internet 23.0",
            "category": "🤖 Android Mobile",
            "ua": "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36"
        },
        {
            "name": "Xiaomi Redmi Note 13 (Android 13 / Chrome)",
            "device": "Redmi Note 13",
            "os": "Android 13",
            "browser": "Chrome Mobile 124.0",
            "category": "🤖 Android Mobile",
            "ua": "Mozilla/5.0 (Linux; Android 13; 2312DRA50G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.179 Mobile Safari/537.36"
        }
    ],
    "windows": [
        {
            "name": "Windows 11 PC (Google Chrome 128)",
            "device": "Windows 11 x64",
            "os": "Windows 11 / 10",
            "browser": "Google Chrome 128.0",
            "category": "💻 Windows PC",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        },
        {
            "name": "Windows 10 PC (Microsoft Edge 128)",
            "device": "Windows 10 x64",
            "os": "Windows 10",
            "browser": "Microsoft Edge 128.0",
            "category": "💻 Windows PC",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
        },
        {
            "name": "Windows 11 PC (Mozilla Firefox 129)",
            "device": "Windows 11 x64",
            "os": "Windows 11",
            "browser": "Mozilla Firefox 129.0",
            "category": "💻 Windows PC",
            "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"
        }
    ],
    "mac": [
        {
            "name": "Apple MacBook Pro M3 (macOS Sonoma / Safari)",
            "device": "MacBook Pro M3",
            "os": "macOS Sonoma (14.5)",
            "browser": "Safari 17.5",
            "category": "🍎 Apple Mac",
            "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"
        },
        {
            "name": "Apple iMac M2 (macOS / Chrome 128)",
            "device": "iMac M2",
            "os": "macOS 14.4",
            "browser": "Google Chrome 128.0",
            "category": "🍎 Apple Mac",
            "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }
    ]
}


def get_user_agent(category=None):
    """Returns a random user-agent object based on category or across all categories."""
    if category and category.lower() in USER_AGENTS_DB:
        pool = USER_AGENTS_DB[category.lower()]
    else:
        pool = [item for sublist in USER_AGENTS_DB.values() for item in sublist]
    return random.choice(pool)
