//! stations.rs - Master railway station codes, names, and authentic Hindi translations.

use std::collections::HashMap;
use std::sync::LazyLock;

pub static STATION_MAP: LazyLock<HashMap<&'static str, (&'static str, &'static str)>> = LazyLock::new(|| {
    let mut m = HashMap::new();
    m.insert("NGP", ("Nagpur Junction", "नागपुर जंक्शन"));
    m.insert("PRYJ", ("Prayagraj Junction", "प्रयागराज जंक्शन"));
    m.insert("PRG", ("Prayag", "प्रयाग"));
    m.insert("AY", ("Ayodhya", "अयोध्या"));
    m.insert("AYC", ("Ayodhya Cantt", "अयोध्या कैंट"));
    m.insert("KRBA", ("Korba", "कोरबा"));
    m.insert("KCG", ("Hyderabad Kacheguda", "हैदराबाद काचेगुड़ा"));
    m.insert("HYB", ("Hyderabad Deccan", "हैदराबाद डेक्कन"));
    m.insert("SC", ("Secunderabad Junction", "सिकंदराबाद जंक्शन"));
    m.insert("DNR", ("Danapur", "दानापुर"));
    m.insert("NDLS", ("New Delhi", "नई दिल्ली"));
    m.insert("DLI", ("Delhi", "दिल्ली"));
    m.insert("NZM", ("Hazrat Nizamuddin", "हज़रत निज़ामुद्दीन"));
    m.insert("ANVT", ("Anand Vihar Terminal", "आनंद विहार टर्मिनल"));
    m.insert("CNB", ("Kanpur Central", "कानपुर सेंट्रल"));
    m.insert("BJU", ("Barauni Junction", "बरौनी जंक्शन"));
    m.insert("BSB", ("Varanasi Junction", "वाराणसी जंक्शन"));
    m.insert("BSBS", ("Banaras", "बनारस"));
    m.insert("LKO", ("Lucknow Charbagh", "लखनऊ चारबाग"));
    m.insert("LJN", ("Lucknow Junction", "लखनऊ जंक्शन"));
    m.insert("HWH", ("Howrah Junction", "हावड़ा जंक्शन"));
    m.insert("SDAH", ("Sealdah", "सियालदह"));
    m.insert("CSMT", ("Chhatrapati Shivaji Maharaj Terminus", "छत्रपति शिवाजी महाराज टर्मिनस"));
    m.insert("DR", ("Dadar", "दादर"));
    m.insert("MMCT", ("Mumbai Central", "मुंबई सेंट्रल"));
    m.insert("BCT", ("Mumbai Central", "मुंबई सेंट्रल"));
    m.insert("BDTS", ("Bandra Terminus", "बांद्रा टर्मिनस"));
    m.insert("PNBE", ("Patna Junction", "पटना जंक्शन"));
    m.insert("GKP", ("Gorakhpur Junction", "गोरखपुर जंक्शन"));
    m.insert("JAT", ("Jammu Tawi", "जम्मू तवी"));
    m.insert("CDG", ("Chandigarh", "चंडीगढ़"));
    m.insert("AGC", ("Agra Cantt", "आगरा कैंट"));
    m.insert("AF", ("Agra Fort", "आगरा फोर्ट"));
    m.insert("GWL", ("Gwalior Junction", "ग्वालियर जंक्शन"));
    m.insert("VGLJ", ("Virangana Lakshmibai Jhansi", "वीरांगना लक्ष्मीबाई झाँसी"));
    m.insert("BPL", ("Bhopal Junction", "भोपाल जंक्शन"));
    m.insert("RKMP", ("Rani Kamalapati", "रानी कमलापति"));
    m.insert("ET", ("Itarsi Junction", "इटारसी जंक्शन"));
    m.insert("JBP", ("Jabalpur Junction", "जबलपुर जंक्शन"));
    m.insert("KTE", ("Katni Junction", "कटनी जंक्शन"));
    m.insert("STA", ("Satna Junction", "सतना जंक्शन"));
    m.insert("MZP", ("Mirzapur", "मिर्ज़ापुर"));
    m.insert("DDU", ("Pt. Deen Dayal Upadhyaya Junction", "पं. दीनदयाल उपाध्याय जंक्शन"));
    m.insert("R", ("Raipur Junction", "रायपुर जंक्शन"));
    m.insert("BSP", ("Bilaspur Junction", "बिलासपुर जंक्शन"));
    m.insert("DURG", ("Durg Junction", "दुर्ग जंक्शन"));
    m.insert("G", ("Gondia Junction", "गोंदिया जंक्शन"));
    m.insert("BXR", ("Buxar", "बक्सर"));
    m.insert("ARA", ("Ara Junction", "आरा जंक्शन"));
    m.insert("PUNE", ("Pune Junction", "पुणे जंक्शन"));
    m.insert("ADI", ("Ahmedabad Junction", "अहमदाबाद जंक्शन"));
    m.insert("BRC", ("Vadodara Junction", "वडोदरा जंक्शन"));
    m.insert("ST", ("Surat", "सूरत"));
    m.insert("JP", ("Jaipur Junction", "जयपुर जंक्शन"));
    m.insert("AII", ("Ajmer Junction", "अजमेर जंक्शन"));
    m.insert("JU", ("Jodhpur Junction", "जोधपुर जंक्शन"));
    m.insert("UJN", ("Ujjain Junction", "उज्जैन जंक्शन"));
    m.insert("INDB", ("Indore Junction", "इंदौर जंक्शन"));
    m.insert("GHY", ("Guwahati", "गुवाहाटी"));
    m.insert("MAS", ("MGR Chennai Central", "एम.जी.आर. चेन्नई सेंट्रल"));
    m.insert("MS", ("Chennai Egmore", "चेन्नई एग्मोर"));
    m.insert("SBC", ("KSR Bengaluru", "के.एस.आर. बेंगलुरु"));
    m.insert("YPR", ("Yesvantpur Junction", "यशवंतपुर जंक्शन"));
    m.insert("TVC", ("Thiruvananthapuram Central", "तिरुवनंतपुरम सेंट्रल"));
    m.insert("ERS", ("Ernakulam Junction", "एर्नाकुलम जंक्शन"));
    m.insert("PURI", ("Puri", "पुरी"));
    m.insert("BBS", ("Bhubaneswar", "भुवनेश्वर"));
    m.insert("VSKP", ("Visakhapatnam", "विशाखापट्टनम"));
    m.insert("BZA", ("Vijayawada Junction", "विजयवाड़ा जंक्शन"));
    m.insert("RNC", ("Ranchi Junction", "रांची जंक्शन"));
    m.insert("TATA", ("Tatanagar Junction", "टाटानगर जंक्शन"));
    m.insert("DHN", ("Dhanbad Junction", "धनबाद जंक्शन"));
    m.insert("ASN", ("Asansol Junction", "आसनसोल जंक्शन"));
    m.insert("MFP", ("Muzaffarpur Junction", "मुजफ्फरपुर जंक्शन"));
    m.insert("DBG", ("Darbhanga Junction", "दरभंगा जंक्शन"));
    m.insert("SHC", ("Saharsa Junction", "सहरसा जंक्शन"));
    m.insert("KIR", ("Katihar Junction", "कटिहार जंक्शन"));
    m.insert("NJP", ("New Jalpaiguri", "न्यू जलपाईगुड़ी"));
    m.insert("SV", ("Siwan Junction", "सीवान जंक्शन"));
    m.insert("CPR", ("Chhapra Junction", "छपरा जंक्शन"));
    m.insert("GAYA", ("Gaya Junction", "गया जंक्शन"));
    m.insert("FD", ("Faizabad Junction", "फैजाबाद जंक्शन"));
    m.insert("PBH", ("Pratapgarh Junction", "प्रतापगढ़ जंक्शन"));
    m.insert("SLN", ("Sultanpur Junction", "सुल्तानपुर जंक्शन"));
    m.insert("PFM", ("Phaphamau Junction", "फाफामऊ जंक्शन"));
    m.insert("JNU", ("Jaunpur Junction", "जौनपुर जंक्शन"));
    m
});

pub static NAME_TO_CODE: LazyLock<HashMap<String, &'static str>> = LazyLock::new(|| {
    let mut m = HashMap::new();
    for (&code, &(en_name, _)) in STATION_MAP.iter() {
        m.insert(code.to_lowercase(), code);
        m.insert(en_name.to_lowercase(), code);
        let first_word = en_name.to_lowercase().split_whitespace().next().unwrap_or("").to_string();
        if !first_word.is_empty() && !m.contains_key(&first_word) {
            m.insert(first_word, code);
        }
    }
    m
});

pub fn get_station_info(code: &str, name: &str) -> (String, String, String) {
    let clean_code = code.trim().to_uppercase();
    let clean_name = name.trim().to_string();

    // Case 1: Direct match on code
    if let Some(&(std_name, std_hi)) = STATION_MAP.get(clean_code.as_str()) {
        let final_name = if !clean_name.is_empty() && clean_name.len() > std_name.len() {
            clean_name
        } else {
            std_name.to_string()
        };
        return (clean_code, final_name, std_hi.to_string());
    }

    // Case 2: Exact match on lowercase name
    let name_lower = clean_name.to_lowercase();
    if let Some(&mapped_code) = NAME_TO_CODE.get(&name_lower) {
        if let Some(&(std_name, std_hi)) = STATION_MAP.get(mapped_code) {
            let final_code = if !clean_code.is_empty() { clean_code } else { mapped_code.to_string() };
            let final_name = if !clean_name.is_empty() { clean_name } else { std_name.to_string() };
            return (final_code, final_name, std_hi.to_string());
        }
    }

    // Case 2b: Word-boundary or substantial substring match (min 4 chars)
    if name_lower.len() >= 4 {
        for (needle, &mapped_code) in NAME_TO_CODE.iter() {
            if needle.len() >= 4 && (needle.contains(&name_lower) || name_lower.contains(needle)) {
                if let Some(&(std_name, std_hi)) = STATION_MAP.get(mapped_code) {
                    let final_code = if !clean_code.is_empty() { clean_code } else { mapped_code.to_string() };
                    let final_name = if !clean_name.is_empty() { clean_name } else { std_name.to_string() };
                    return (final_code, final_name, std_hi.to_string());
                }
            }
        }
    }

    // Case 3: If code was empty but name is short uppercase code
    if clean_code.is_empty() && clean_name.chars().all(|c| c.is_ascii_uppercase()) && clean_name.len() <= 5 {
        if let Some(&(std_name, std_hi)) = STATION_MAP.get(clean_name.as_str()) {
            return (clean_name.clone(), std_name.to_string(), std_hi.to_string());
        }
    }

    // Fallback: Suffix transliteration
    let mut hi_name = if !clean_name.is_empty() { clean_name.clone() } else { clean_code.clone() };
    if clean_name.contains("Junction") || clean_code.contains("JN") {
        let base = clean_name.replace("Junction", "").replace("Jn", "").trim().to_string();
        hi_name = format!("{} जंक्शन", base);
    } else if clean_name.contains("Cantt") {
        let base = clean_name.replace("Cantt", "").trim().to_string();
        hi_name = format!("{} कैंट", base);
    } else if clean_name.contains("Central") {
        let base = clean_name.replace("Central", "").trim().to_string();
        hi_name = format!("{} सेंट्रल", base);
    }

    let final_c = if !clean_code.is_empty() { clean_code } else { clean_name.clone() };
    let final_n = if !clean_name.is_empty() { clean_name } else { final_c.clone() };
    (final_c, final_n, hi_name)
}
