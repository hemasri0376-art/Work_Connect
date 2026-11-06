"""
Trade Category Visual Utilities & Normalizer.
Maps trades in English, Telugu, and Hindi to canonical category keys, visual pictures, and icons.
"""

TRADE_METADATA = {
    "mason": {
        "key": "mason",
        "name_en": "Mason / Construction",
        "name_te": "మేస్త్రీ / భవన నిర్మాణం",
        "name_hi": "राजमिस्त्री / निर्माण कार्य",
        "icon": "🧱",
        "image": "images/trades/mason.svg",
        "color": "#D9381E",
        "bg_tint": "#FFF1EE",
        "keywords": ["mason", "brick", "construction", "builder", "మేస్త్రీ", "భవన", "కట్టడం", "రాజమిస్త్రీ", "मिस्त्री", "निर्माण"]
    },
    "driver": {
        "key": "driver",
        "name_en": "Driver (Auto/Cab/Truck)",
        "name_te": "డ్రైవర్ (ఆటో/కారు/ట్రాక్టర్)",
        "name_hi": "ड्राइवर (ऑटो/गाड़ी/ट्रैक्टर)",
        "icon": "🚗",
        "image": "images/trades/driver.svg",
        "color": "#1452B8",
        "bg_tint": "#EEF5FF",
        "keywords": ["driver", "driving", "transport", "cab", "auto", "truck", "డ్రైవర్", "రవాణా", "డ్రైవింగ్", "चालक", "ड्राइवर", "गाड़ी"]
    },
    "electrician": {
        "key": "electrician",
        "name_en": "Electrician / Electrical",
        "name_te": "ఎలక్ట్రీషియన్ / కరెంట్ పని",
        "name_hi": "इलेक्ट्रीशियन / बिजली मिस्त्री",
        "icon": "⚡",
        "image": "images/trades/electrician.svg",
        "color": "#D97706",
        "bg_tint": "#FFFBEB",
        "keywords": ["electrician", "electrical", "wiring", "electric", "power", "solar", "ఎలక్ట్రీషియన్", "కరెంట్", "వైరింగ్", "बिजली", "इलेक्ट्रीशियन"]
    },
    "painter": {
        "key": "painter",
        "name_en": "Painter / Whitewashing",
        "name_te": "పెయింటర్ / రంగుల పని",
        "name_hi": "पेंटर / रंगाई का काम",
        "icon": "🎨",
        "image": "images/trades/painter.svg",
        "color": "#7C3AED",
        "bg_tint": "#F5F3FF",
        "keywords": ["painter", "painting", "paint", "whitewash", "పెయింటర్", "రంగులు", "రంగుల పని", "रंगाई", "पेंटर", "पुताई"]
    },
    "farm_worker": {
        "key": "farm_worker",
        "name_en": "Farm Worker / Agriculture",
        "name_te": "వ్యవసాయ కూలీ",
        "name_hi": "खेत मजदूर / कृषि कार्य",
        "icon": "🌾",
        "image": "images/trades/farm_worker.svg",
        "color": "#047857",
        "bg_tint": "#ECFDF5",
        "keywords": ["farm", "farming", "agriculture", "harvest", "crop", "paddy", "వ్యవసాయం", "కూలీ", "పొలం", "రైతు", "खेत", "किसान", "कृषि", "मजदूर"]
    },
    "carpenter": {
        "key": "carpenter",
        "name_en": "Carpenter / Woodwork",
        "name_te": "వడ్రంగి పని",
        "name_hi": "बढ़ई / लकड़ी का काम",
        "icon": "🪚",
        "image": "images/trades/carpenter.svg",
        "color": "#92400E",
        "bg_tint": "#FEF3C7",
        "keywords": ["carpenter", "wood", "furniture", "timber", "వడ్రంగి", "చెక్క పని", "बढ़ई", "लकड़ी"]
    },
    "plumber": {
        "key": "plumber",
        "name_en": "Plumber / Pipe Fitting",
        "name_te": "ప్లంబర్ / పైపుల పని",
        "name_hi": "प्लंबर / नलसाज",
        "icon": "🔧",
        "image": "images/trades/plumber.svg",
        "color": "#0891B2",
        "bg_tint": "#ECFEFF",
        "keywords": ["plumber", "plumbing", "pipe", "water", "leak", "టాప్", "ప్లంబర్", "పైపులు", "प्लंबर", "नल", "पाइप"]
    },
    "helper": {
        "key": "helper",
        "name_en": "General Helper / Labor",
        "name_te": "సహాయకుడు / జనరల్ కూలీ",
        "name_hi": "सहायक / सामान्य मजदूर",
        "icon": "🤝",
        "image": "images/trades/helper.svg",
        "color": "#4338CA",
        "bg_tint": "#EEF2FF",
        "keywords": ["helper", "labor", "labour", "assistant", "loading", "other", "సహాయకుడు", "కూలీ", "హెల్పర్", "सहायक", "मजदूर"]
    }
}


def get_trade_for_skill(skill_text):
    """Normalize any skill string to its trade category metadata."""
    if not skill_text:
        return TRADE_METADATA["helper"]

    text = str(skill_text).strip().lower()

    for trade_key, data in TRADE_METADATA.items():
        if trade_key == text:
            return data
        for kw in data["keywords"]:
            if kw.lower() in text or text in kw.lower():
                return data

    return TRADE_METADATA["helper"]


def get_all_trades_list(lang="en"):
    """Return all trade categories formatted for UI visual navigation."""
    result = []
    name_field = f"name_{lang}" if lang in ("en", "te", "hi") else "name_en"
    for key, data in TRADE_METADATA.items():
        result.append({
            "key": key,
            "name": data.get(name_field, data["name_en"]),
            "icon": data["icon"],
            "image": data["image"],
            "color": data["color"],
            "bg_tint": data["bg_tint"]
        })
    return result
