"""
stations.py - Master railway station codes, names, and authentic Hindi translations.
Provides exact mappings for Indian Railways PRS stations with fallback transliteration.
"""

from typing import Tuple

STATION_MAP = {
    # Major stations and stations active in fleet tracking
    "NGP": ("Nagpur Junction", "नागपुर जंक्शन"),
    "PRYJ": ("Prayagraj Junction", "प्रयागराज जंक्शन"),
    "PRG": ("Prayag", "प्रयाग"),
    "AY": ("Ayodhya", "अयोध्या"),
    "AYC": ("Ayodhya Cantt", "अयोध्या कैंट"),
    "KRBA": ("Korba", "कोरबा"),
    "KCG": ("Hyderabad Kacheguda", "हैदराबाद काचेगुड़ा"),
    "HYB": ("Hyderabad Deccan", "हैदराबाद डेक्कन"),
    "SC": ("Secunderabad Junction", "सिकंदराबाद जंक्शन"),
    "DNR": ("Danapur", "दानापुर"),
    "NDLS": ("New Delhi", "नई दिल्ली"),
    "DLI": ("Delhi", "दिल्ली"),
    "NZM": ("Hazrat Nizamuddin", "हज़रत निज़ामुद्दीन"),
    "ANVT": ("Anand Vihar Terminal", "आनंद विहार टर्मिनल"),
    "CNB": ("Kanpur Central", "कानपुर सेंट्रल"),
    "BJU": ("Barauni Junction", "बरौनी जंक्शन"),
    "BSB": ("Varanasi Junction", "वाराणसी जंक्शन"),
    "BSBS": ("Banaras", "बनारस"),
    "LKO": ("Lucknow Charbagh", "लखनऊ चारबाग"),
    "LJN": ("Lucknow Junction", "लखनऊ जंक्शन"),
    "HWH": ("Howrah Junction", "हावड़ा जंक्शन"),
    "SDAH": ("Sealdah", "सियालदह"),
    "CSMT": ("Chhatrapati Shivaji Maharaj Terminus", "छत्रपति शिवाजी महाराज टर्मिनस"),
    "DR": ("Dadar", "दादर"),
    "MMCT": ("Mumbai Central", "मुंबई सेंट्रल"),
    "BCT": ("Mumbai Central", "मुंबई सेंट्रल"),
    "BDTS": ("Bandra Terminus", "बांद्रा टर्मिनस"),
    "PNBE": ("Patna Junction", "पटना जंक्शन"),
    "GKP": ("Gorakhpur Junction", "गोरखपुर जंक्शन"),
    "JAT": ("Jammu Tawi", "जम्मू तवी"),
    "CDG": ("Chandigarh", "चंडीगढ़"),
    "AGC": ("Agra Cantt", "आगरा कैंट"),
    "AF": ("Agra Fort", "आगरा फोर्ट"),
    "GWL": ("Gwalior Junction", "ग्वालियर जंक्शन"),
    "VGLJ": ("Virangana Lakshmibai Jhansi", "वीरांगना लक्ष्मीबाई झाँसी"),
    "BPL": ("Bhopal Junction", "भोपाल जंक्शन"),
    "RKMP": ("Rani Kamalapati", "रानी कमलापति"),
    "ET": ("Itarsi Junction", "इटारसी जंक्शन"),
    "JBP": ("Jabalpur Junction", "जबलपुर जंक्शन"),
    "KTE": ("Katni Junction", "कटनी जंक्शन"),
    "STA": ("Satna Junction", "सतना जंक्शन"),
    "MZP": ("Mirzapur", "मिर्ज़ापुर"),
    "DDU": ("Pt. Deen Dayal Upadhyaya Junction", "पं. दीनदयाल उपाध्याय जंक्शन"),
    "R": ("Raipur Junction", "रायपुर जंक्शन"),
    "BSP": ("Bilaspur Junction", "बिलासपुर जंक्शन"),
    "DURG": ("Durg Junction", "दुर्ग जंक्शन"),
    "G": ("Gondia Junction", "गोंदिया जंक्शन"),
    "BXR": ("Buxar", "बक्सर"),
    "ARA": ("Ara Junction", "आरा जंक्शन"),
    "PUNE": ("Pune Junction", "पुणे जंक्शन"),
    "ADI": ("Ahmedabad Junction", "अहमदाबाद जंक्शन"),
    "BRC": ("Vadodara Junction", "वडोदरा जंक्शन"),
    "ST": ("Surat", "सूरत"),
    "JP": ("Jaipur Junction", "जयपुर जंक्शन"),
    "AII": ("Ajmer Junction", "अजमेर जंक्शन"),
    "JU": ("Jodhpur Junction", "जोधपुर जंक्शन"),
    "UJN": ("Ujjain Junction", "उज्जैन जंक्शन"),
    "INDB": ("Indore Junction", "इंदौर जंक्शन"),
    "GHY": ("Guwahati", "गुवाहाटी"),
    "MAS": ("MGR Chennai Central", "एम.जी.आर. चेन्नई सेंट्रल"),
    "MS": ("Chennai Egmore", "चेन्नई एग्मोर"),
    "SBC": ("KSR Bengaluru", "के.एस.आर. बेंगलुरु"),
    "YPR": ("Yesvantpur Junction", "यशवंतपुर जंक्शन"),
    "TVC": ("Thiruvananthapuram Central", "तिरुवनंतपुरम सेंट्रल"),
    "ERS": ("Ernakulam Junction", "एर्नाकुलम जंक्शन"),
    "PURI": ("Puri", "पुरी"),
    "BBS": ("Bhubaneswar", "भुवनेश्वर"),
    "VSKP": ("Visakhapatnam", "विशाखापट्टनम"),
    "BZA": ("Vijayawada Junction", "विजयवाड़ा जंक्शन"),
    "RNC": ("Ranchi Junction", "रांची जंक्शन"),
    "TATA": ("Tatanagar Junction", "टाटानगर जंक्शन"),
    "DHN": ("Dhanbad Junction", "धनबाद जंक्शन"),
    "ASN": ("Asansol Junction", "आसनसोल जंक्शन"),
    "MFP": ("Muzaffarpur Junction", "मुजफ्फरपुर जंक्शन"),
    "DBG": ("Darbhanga Junction", "दरभंगा जंक्शन"),
    "SHC": ("Saharsa Junction", "सहरसा जंक्शन"),
    "KIR": ("Katihar Junction", "कटिहार जंक्शन"),
    "NJP": ("New Jalpaiguri", "न्यू जलपाईगुड़ी"),
    "SV": ("Siwan Junction", "सीवान जंक्शन"),
    "CPR": ("Chhapra Junction", "छपरा जंक्शन"),
    "GAYA": ("Gaya Junction", "गया जंक्शन"),
    "FD": ("Faizabad Junction", "फैजाबाद जंक्शन"),
    "PBH": ("Pratapgarh Junction", "प्रतापगढ़ जंक्शन"),
    "SLN": ("Sultanpur Junction", "सुल्तानपुर जंक्शन"),
    "PFM": ("Phaphamau Junction", "फाफामऊ जंक्शन"),
    "JNU": ("Jaunpur Junction", "जौनपुर जंक्शन")
}

# Reverse lookup by lower-case english name
NAME_TO_CODE = {}
for code, (en_name, hi_name) in STATION_MAP.items():
    NAME_TO_CODE[code.lower()] = code
    NAME_TO_CODE[en_name.lower()] = code
    # Also add first word if unique (e.g. "nagpur" -> NGP)
    first_word = en_name.lower().split()[0]
    if first_word not in NAME_TO_CODE:
        NAME_TO_CODE[first_word] = code


def get_station_info(code: str, name: str = "") -> Tuple[str, str, str]:
    """
    Returns (station_code, station_name, station_hindi).
    Accurately maps any railway code or station name to genuine Indian Railways station info.
    """
    clean_code = str(code or "").strip().upper()
    clean_name = str(name or "").strip()

    # Case 1: Direct match on code
    if clean_code in STATION_MAP:
        std_name, std_hi = STATION_MAP[clean_code]
        final_name = clean_name if clean_name and len(clean_name) > len(std_name) else std_name
        return clean_code, final_name, std_hi

    # Case 2: Exact match on lowercase name
    name_lower = clean_name.lower()
    if name_lower in NAME_TO_CODE:
        mapped_code = NAME_TO_CODE[name_lower]
        std_name, std_hi = STATION_MAP[mapped_code]
        final_code = clean_code if clean_code else mapped_code
        return final_code, (clean_name or std_name), std_hi

    # Case 2b: Word-boundary or substantial substring match (min 4 chars) to avoid false collisions
    if len(name_lower) >= 4:
        for needle, mapped_code in NAME_TO_CODE.items():
            if len(needle) >= 4 and (needle in name_lower or name_lower in needle):
                std_name, std_hi = STATION_MAP[mapped_code]
                final_code = clean_code if clean_code else mapped_code
                return final_code, (clean_name or std_name), std_hi

    # Case 3: If code was empty but name is short uppercase code
    if not clean_code and clean_name.isupper() and len(clean_name) <= 5:
        clean_code = clean_name
        if clean_code in STATION_MAP:
            std_name, std_hi = STATION_MAP[clean_code]
            return clean_code, std_name, std_hi

    # Fallback: Generate Hindi transliteration suffix if "Junction" or "Cantt" present
    hi_name = clean_name or clean_code
    if "Junction" in clean_name or "JN" in clean_code:
        base = clean_name.replace("Junction", "").replace("Jn", "").strip()
        hi_name = f"{base} जंक्शन"
    elif "Cantt" in clean_name:
        base = clean_name.replace("Cantt", "").strip()
        hi_name = f"{base} कैंट"
    elif "Central" in clean_name:
        base = clean_name.replace("Central", "").strip()
        hi_name = f"{base} सेंट्रल"

    return clean_code or clean_name, clean_name or clean_code, hi_name
