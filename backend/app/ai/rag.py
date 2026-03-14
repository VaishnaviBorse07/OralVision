"""
Advanced RAG Chatbot for OralVision
- 36-entry curated oral cancer knowledge base
- Sentence-transformer semantic search (all-MiniLM-L6-v2)
- Gemini 1.5 Flash answer synthesis when API key available (uses KB as context)
- Multi-turn conversation history support
- Keyword fallback when embeddings unavailable
"""
import logging
from functools import lru_cache
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── Comprehensive Knowledge Base (36 entries) ─────────────────────────────────
KNOWLEDGE_BASE = [
    {
        "id": "def_oral_cancer",
        "title": "What is oral cancer?",
        "content": (
            "Oral cancer refers to cancer that develops in any part of the mouth, including the lips, "
            "tongue, cheeks, floor of the mouth, hard and soft palate, sinuses, and throat (pharynx). "
            "It is a type of head and neck cancer. In India, oral cancer is one of the most common cancers, "
            "particularly among tobacco users. It accounts for over 30% of all cancer cases in India, "
            "with approximately 77,000 new cases and 52,000 deaths every year."
        ),
    },
    {
        "id": "signs_symptoms",
        "title": "Signs and symptoms of oral cancer",
        "content": (
            "Common warning signs of oral cancer include: (1) A sore or ulcer in the mouth that does not heal "
            "within 2 weeks. (2) Red patches (erythroplakia) or white patches (leukoplakia) inside the mouth. "
            "(3) A lump, thickening, or rough spot on lips, gums, or inside the mouth. "
            "(4) Difficulty chewing, swallowing, or moving the tongue or jaw. (5) Numbness or pain in the mouth or lips. "
            "(6) Loose teeth without a dental cause. (7) Ear pain. (8) Unexplained weight loss. "
            "(9) Change in voice or hoarseness. (10) Persistent bad breath. "
            "Any of these lasting more than 2 weeks requires immediate professional evaluation."
        ),
    },
    {
        "id": "risk_factors",
        "title": "Risk factors for oral cancer",
        "content": (
            "Major risk factors for oral cancer include: (1) Tobacco use — smoking cigarettes, beedis, cigars, "
            "or chewing tobacco, pan masala, gutka, or khaini significantly increases risk. "
            "(2) Alcohol consumption — heavy drinking, especially combined with tobacco (synergistic 30x risk). "
            "(3) Age — risk increases significantly after age 40, with most cases occurring in people over 60. "
            "(4) Gender — men are twice as likely as women to develop oral cancer. "
            "(5) Human Papillomavirus (HPV) infection, particularly HPV-16. "
            "(6) Sun exposure to the lips. (7) Poor diet lacking fruits and vegetables. "
            "(8) Weakened immune system. (9) Poorly fitting dentures causing chronic irritation. "
            "The combination of tobacco and alcohol is particularly dangerous — 30x higher risk."
        ),
    },
    {
        "id": "high_risk_action",
        "title": "What to do when high risk is detected",
        "content": (
            "When an AI screening shows HIGH RISK: (1) Immediately refer the patient to an oncologist, "
            "oral surgeon, or the nearest District Cancer Centre — do not delay. "
            "(2) Advise complete cessation of tobacco and alcohol immediately. "
            "(3) A biopsy is usually required within 48 hours for definitive diagnosis. "
            "(4) Document all lesion characteristics: size, color (red/white), location, duration, pain level. "
            "(5) Activate high-risk alert via the platform — this has been done automatically. "
            "(6) Tell patient about Ayushman Bharat (PM-JAY) — cancer treatment is FREE at empanelled hospitals. "
            "(7) Reassure the patient while stressing urgency. Do not delay referral. "
            "Call Tata Memorial Hospital Mumbai at 022-24177000 for specialist guidance."
        ),
    },
    {
        "id": "medium_risk_action",
        "title": "What to do when medium risk is detected",
        "content": (
            "For MEDIUM RISK patients: (1) Schedule a follow-up screening in exactly 2 weeks — mark calendar. "
            "(2) Educate the patient about warning signs to watch for: non-healing ulcers, color changes, swelling. "
            "(3) Recommend IMMEDIATE tobacco cessation and reduction of alcohol intake. "
            "(4) Monitor the lesion for changes in size, color, texture, or pain. "
            "(5) If any worsening occurs before the follow-up, refer immediately to District Hospital. "
            "(6) Document the patient's contact details for reminder scheduling. "
            "(7) Prescribe antiseptic mouthwash if inflammatory lesions present. "
            "Call tobacco quit line: 1800-11-2356 (toll-free) for cessation support."
        ),
    },
    {
        "id": "low_risk_advice",
        "title": "Advice for low risk patients",
        "content": (
            "For LOW RISK patients: (1) Reassure the patient but emphasize annual screening. "
            "(2) Educate about early warning signs — any sore not healing in 2 weeks needs evaluation. "
            "(3) Encourage tobacco and alcohol cessation even for low risk. "
            "(4) Advise good oral hygiene: brush twice daily with fluoride toothpaste, use antimicrobial "
            "mouthwash, and clean between teeth daily. (5) Recommend a diet rich in fruits, vegetables, and antioxidants. "
            "(6) Encourage routine dental check-ups every 6 months. "
            "(7) Next OralVision screening in 12 months or sooner if any symptoms develop."
        ),
    },
    {
        "id": "stages",
        "title": "Stages of oral cancer",
        "content": (
            "Oral cancer is staged from I to IV: Stage I — tumor is 2 cm or smaller, confined to the mouth. "
            "Stage II — tumor is between 2–4 cm, still localized. Stage III — tumor is over 4 cm or has spread to one lymph "
            "node on the same side of the neck. Stage IV — tumor has spread to nearby tissues, multiple "
            "lymph nodes, or distant organs (metastatic). Survival rates decrease significantly with stage: "
            "5-year survival: Stage I ~85%, Stage II ~65%, Stage III ~40%, Stage IV ~15%. "
            "Early detection in Stage I/II is critical — this is why OralVision screening matters."
        ),
    },
    {
        "id": "tobacco",
        "title": "Tobacco and oral cancer link",
        "content": (
            "Tobacco in all forms is the leading cause of oral cancer in India. This includes: "
            "Bidi smoking (3x more carcinogenic than cigarettes due to unfiltered high tar), cigarettes, cigar smoking, "
            "chewing tobacco, pan masala, gutka, khaini, and mawa. Smokeless tobacco causes "
            "leukoplakia (white patches) and submucous fibrosis, which are pre-cancerous conditions. "
            "Tobacco users have 6–10x higher risk of oral cancer. Gutka and pan masala specifically cause "
            "Oral Submucous Fibrosis (OSMF), limiting mouth opening and causing a burning sensation. "
            "Quitting tobacco reduces risk significantly within 5 years. "
            "ASHA workers should counsel every tobacco-using patient on cessation — call 1800-11-2356."
        ),
    },
    {
        "id": "prevention",
        "title": "Prevention of oral cancer",
        "content": (
            "Oral cancer prevention steps: (1) Avoid all forms of tobacco — smoking and smokeless. "
            "(2) Limit alcohol consumption to less than 1 drink/day. (3) Get vaccinated against HPV (Gardasil vaccine). "
            "(4) Eat a diet rich in fruits and vegetables — antioxidants (Vitamins A, C, E) protect cells. "
            "(5) Practice good oral hygiene — brush twice, clean between teeth, use mouthwash. "
            "(6) Get regular dental check-ups every 6 months. "
            "(7) Use lip balm with SPF 30+ when outdoors to protect lips from UV. "
            "(8) Report any mouth sore lasting more than 2 weeks to a doctor immediately. "
            "Community screening programs like OralVision are key to early rural detection."
        ),
    },
    {
        "id": "biopsy",
        "title": "What is a biopsy for oral cancer?",
        "content": (
            "A biopsy is the definitive diagnostic test for oral cancer. A small sample of tissue "
            "is removed from the suspicious lesion and examined under a microscope by a pathologist. "
            "Types include: Incisional biopsy (part of lesion removed), excisional biopsy (entire small lesion removed), "
            "and fine-needle aspiration cytology (FNAC, for lymph nodes). Results are typically available in 3–7 days. "
            "In Indian cancer centres, free biopsy is available under Ayushman Bharat Yojana (PM-JAY). "
            "Toluidine blue staining can help identify suspicious areas before biopsy. "
            "ASHA workers should help patients navigate referral for biopsy — it is free at government hospitals."
        ),
    },
    {
        "id": "treatment",
        "title": "Treatment options for oral cancer",
        "content": (
            "Treatment depends on stage, location, and patient health: "
            "Surgery — removal of tumor and surrounding tissue, may include jaw reconstruction with titanium plates. "
            "Radiation therapy — high-energy beams to kill cancer cells, used alone or after surgery (6–7 weeks). "
            "Chemotherapy — drugs to kill cancer cells, often combined with radiation (cisplatin-based regimens). "
            "Targeted therapy — drugs that target specific cancer cell proteins (e.g., Cetuximab for EGFR+ tumors). "
            "Immunotherapy — helps immune system fight cancer (pembrolizumab / nivolumab). "
            "Palliative care — for advanced cases, to manage pain and improve quality of life. "
            "Under PM-JAY/Ayushman Bharat, treatment costs up to ₹5 lakhs per family are covered at empanelled hospitals. "
            "Call 14555 for PM-JAY coverage details."
        ),
    },
    {
        "id": "asha_role",
        "title": "Role of ASHA workers in oral cancer screening",
        "content": (
            "ASHA (Accredited Social Health Activist) workers are the frontline of rural cancer detection. "
            "Key responsibilities: (1) Conduct community screenings at village level — target all adults above 30. "
            "(2) Use OralVision platform to capture oral images and submit for AI analysis. "
            "(3) Refer HIGH risk patients to PHC or CHC immediately — do not wait for symptoms. "
            "(4) Follow up with MEDIUM risk patients within 2 weeks. (5) Counsel communities on tobacco cessation. "
            "(6) Maintain patient records, document screenings with image and result. "
            "(7) Coordinate with ANMs and Block Medical Officers for confirmed cases. "
            "ASHA workers are trained under NHM and receive performance-based incentives for screenings under NPCDCS."
        ),
    },
    {
        "id": "nhm_scheme",
        "title": "Government schemes for oral cancer in India",
        "content": (
            "Key government initiatives for oral cancer in India: "
            "(1) NPCDCS — National Programme for Prevention and Control of Cancer, Diabetes, CVD and Stroke. "
            "Provides free screening at District Hospitals. Target: all adults 30+. "
            "(2) Ayushman Bharat / PM-JAY — covers cancer treatment costs up to ₹5 lakhs per family per year. "
            "Call 14555 to check eligibility. (3) RBSK — Rashtriya Bal Swasthya Karyakram — oral health screening for children 0-18. "
            "(4) NHM — National Health Mission funds rural ASHA workers and mobile health units. "
            "(5) mCessation — free tobacco quit programme by Ministry of Health. SMS QUIT to 011-22901701. "
            "Patients should be told about free cancer treatment at government empanelled hospitals."
        ),
    },
    {
        "id": "confidence_score",
        "title": "What does the AI confidence score mean?",
        "content": (
            "The OralVision AI confidence score represents the model's certainty in its prediction. "
            "It ranges from 1% to 99%. Interpretation: "
            "Above 88% confidence in High Risk: very strong CNN signal — expedite biopsy referral. "
            "72–88% High Risk: significant concern — urgent referral needed. "
            "Below 72% High Risk: concerning but less certain — close follow-up required. "
            "40–65% is the borderline Medium Risk zone. "
            "Below 40% in Low Risk: model is confident of normal/healthy tissue. "
            "The AI combines DenseNet121 image analysis with Gemini multimodal vision and clinical factors "
            "(age, tobacco type). An image upload always improves prediction accuracy significantly."
        ),
    },
    {
        "id": "oral_hygiene",
        "title": "Oral hygiene advice for rural patients",
        "content": (
            "Simple oral hygiene tips for rural patients: (1) Brush teeth twice daily — morning and night. "
            "Use a soft brush and fluoride toothpaste. If no toothpaste, neem twigs (datun) are traditional alternatives. "
            "(2) Rinse mouth thoroughly with clean water after every meal. "
            "(3) Avoid betel nut, pan, gutkha — major cancer risk even without tobacco. "
            "(4) Gargle with warm salt water (1 tsp in warm water) for mouth sores. "
            "(5) Avoid very hot food and drinks — heat damages mucosa. "
            "(6) Eat more fruits, green vegetables, and dal for nutrients. "
            "(7) Drink 8+ glasses of clean water daily. "
            "(8) Visit the PHC dentist or dental camp when available — at least once a year."
        ),
    },
    {
        "id": "leukoplakia",
        "title": "What is leukoplakia? Is it dangerous?",
        "content": (
            "Leukoplakia refers to thick, white or grey patches inside the mouth that cannot be scraped off. "
            "It is a pre-cancerous condition caused mainly by tobacco use, chronic irritation, or alcohol. "
            "About 5–17% of leukoplakia cases progress to oral cancer within 10 years. "
            "Erythroplakia (red patches) is even more dangerous — over 50% are already dysplastic or cancerous at diagnosis. "
            "Mixed erythroleukoplakia (red and white) has the highest cancer risk — refer immediately. "
            "Submucous fibrosis — caused by chewing betel nut, gutka, pan masala — causes difficulty "
            "opening the mouth (trismus), burning sensation, and has 7–13% cancer transformation rate. "
            "ALL THREE require urgent medical referral and biopsy. Cannot be diagnosed by AI alone."
        ),
    },
    {
        "id": "erythroplakia",
        "title": "What is erythroplakia?",
        "content": (
            "Erythroplakia is a red, velvety patch inside the mouth that cannot be attributed to any other cause. "
            "It is more dangerous than leukoplakia — over 50% of cases are already carcinoma in situ or invasive "
            "cancer at the time of diagnosis. It looks like a bright red, soft, smooth patch, often with irregular borders. "
            "Common locations: floor of mouth, soft palate, tongue. "
            "Any red patch persisting more than 2 weeks must be biopsied. "
            "The OralVision AI is specifically trained to detect red patch patterns. "
            "Refer immediately — do not wait for symptoms like pain (pain is a late sign)."
        ),
    },
    {
        "id": "submucous_fibrosis",
        "title": "What is Oral Submucous Fibrosis (OSMF)?",
        "content": (
            "Oral Submucous Fibrosis (OSMF) is a chronic, potentially malignant condition caused by chewing "
            "areca nut (supari), betel nut, gutka, or pan masala. Symptoms include: restricted mouth opening (trismus), "
            "burning sensation with spicy food, blanching (whitening) of oral mucosa, stiffness of cheeks and lips. "
            "OSMF has a 7–13% malignant transformation rate. The fibrous bands restrict blood supply. "
            "Management: immediate cessation of betel nut/gutka, corticosteroid injections, physiotherapy for mouth opening, "
            "regular monitoring. Common in young men in India aged 15–35. "
            "OralVision AI detects blanching patterns consistent with OSMF."
        ),
    },
    {
        "id": "cessation_programs",
        "title": "Tobacco cessation programs and resources",
        "content": (
            "Tobacco cessation resources available in India: "
            "(1) National Tobacco Quit Line: 1800-11-2356 (toll-free, Hindi and English, Mon-Sat 8am-8pm). "
            "(2) mCessation: SMS QUIT to 011-22901701 for free text-based quit programme from MoHFW. "
            "(3) iQuit — free mobile app by Ministry of Health for tracking quit progress. "
            "(4) Nicotine Replacement Therapy (NRT) — patches, gum, lozenges — available at pharmacies. "
            "(5) Bupropion and Varenicline tablets — available at CHCs and district hospitals on prescription. "
            "(6) ASHA workers can facilitate group counselling sessions in villages. "
            "Quitting tobacco reduces oral cancer risk by 50% within 5 years and 80% within 10 years."
        ),
    },
    {
        "id": "nutrition",
        "title": "Diet and nutrition for oral cancer prevention",
        "content": (
            "Diet plays a key role in oral cancer prevention and recovery: "
            "PROTECTIVE foods: Dark green vegetables (spinach, methi) — folate protects DNA. "
            "Citrus fruits (amla, lemon, orange) — Vitamin C boosts immunity. "
            "Tomatoes, papaya — lycopene and beta-carotene are antioxidants. "
            "Turmeric (haldi) — curcumin has anti-inflammatory and anti-cancer properties. "
            "Green tea — polyphenols inhibit cancer cell growth. "
            "AVOID: Very hot food and drinks — thermal injury damages mucosa. "
            "Spicy, acidic, or rough foods if lesions are present. "
            "Processed meats and red meat in excess. "
            "For patients undergoing treatment: soft, cool, nutrient-dense foods are recommended."
        ),
    },
    {
        "id": "hpv_vaccine",
        "title": "HPV vaccine and oral cancer",
        "content": (
            "Human Papillomavirus (HPV), particularly HPV-16 and HPV-18, causes oropharyngeal cancers "
            "(base of tongue, tonsil area). HPV-related oral cancers are increasing globally, especially in non-smokers. "
            "The Gardasil 9 vaccine (9-valent) protects against HPV-16, 18, and 7 other strains. "
            "Vaccination is most effective before first sexual exposure — recommended for ages 9–26 in India. "
            "Under the National Immunization Programme, girls aged 9 years receive HPV vaccine in many states. "
            "HPV testing is now available at AIIMS and major cancer centres. "
            "Even without HPV, tobacco remains the #1 risk factor in India."
        ),
    },
    {
        "id": "imaging_diagnosis",
        "title": "Imaging and diagnostic tests for oral cancer",
        "content": (
            "Diagnostic tests for oral cancer beyond visual examination: "
            "(1) Biopsy — gold standard, definitive diagnosis. "
            "(2) Toluidine blue test — dye stains suspicious cells dark blue, helps target biopsy site. "
            "(3) Brush cytology — non-invasive cell collection from lesion surface. "
            "(4) OPG (Orthopantomogram) X-ray — detects jaw bone involvement. "
            "(5) CT Scan — staging, lymph node involvement, bone invasion. "
            "(6) MRI — soft tissue extent, nerve involvement. "
            "(7) PET-CT Scan — whole body staging, metastasis detection. "
            "(8) Ultrasound — neck lymph nodes assessment. "
            "AI screening tools like OralVision provide triage-level initial risk assessment — "
            "they do NOT replace biopsy. Always confirm suspicious AI findings with biopsy."
        ),
    },
    {
        "id": "pain_management",
        "title": "Pain management in oral cancer",
        "content": (
            "Pain is common during oral cancer treatment and in advanced disease. Management options: "
            "(1) WHO Pain Ladder: mild pain → paracetamol/NSAIDs; moderate → weak opioids (tramadol, codeine); "
            "severe → strong opioids (morphine, oxycodone). Morphine is available free at government palliative care units. "
            "(2) Mouth rinses: lignocaine viscous 2% before eating reduces pain from mucositis. "
            "(3) Magic mouthwash: mixture of antifungal, antibiotic, and local anaesthetic. "
            "(4) Gabapentin for neuropathic pain (nerve damage from tumour). "
            "(5) Palliative care teams at cancer centres provide comprehensive pain management. "
            "Refer to the national palliative care helpline for guidance."
        ),
    },
    {
        "id": "ai_model_how",
        "title": "How does the OralVision AI work?",
        "content": (
            "OralVision uses a multi-engine AI prediction system: "
            "(1) DenseNet121 CNN — a deep convolutional neural network pretrained on ImageNet and fine-tuned "
            "on 1,229 oral cavity images (676 cancer, 553 normal). It extracts visual features from the oral image "
            "and outputs a probability of malignancy. "
            "(2) Gemini 1.5 Flash multimodal AI — Google's vision-language model. It analyzes the image "
            "and refines the DenseNet prediction with clinically precise natural language explanations. "
            "(3) Clinical Heuristic — if no image is uploaded, risk is estimated from age and tobacco type "
            "based on NPCDCS risk stratification guidelines. "
            "The three engines work together: DenseNet provides the score, Gemini enhances the explanation, "
            "heuristic covers the no-image case."
        ),
    },
    {
        "id": "referral_pathway",
        "title": "Referral pathway for oral cancer in India",
        "content": (
            "Standard referral pathway in India: "
            "Level 1: Village/ASHA worker → using OralVision AI screening. "
            "Level 2: PHC (Primary Health Centre) → clinical visual examination by Medical Officer. "
            "Level 3: CHC (Community Health Centre) → dental officer examination, toluidine blue test. "
            "Level 4: District Hospital → specialist examination, biopsy, OPG X-ray. "
            "Level 5: Regional Cancer Centre / Medical College → definitive treatment, radiation, surgery. "
            "High-risk OralVision cases should BYPASS levels 2–3 and go directly to District Hospital (Level 4). "
            "Under NPCDCS, the referral transport allowance covers ₹250-500 per trip for cancer suspects."
        ),
    },
    {
        "id": "post_treatment",
        "title": "Life after oral cancer treatment",
        "content": (
            "After completing oral cancer treatment, patients need ongoing follow-up: "
            "(1) Follow-up schedule: every 1–3 months for first 2 years, then every 6 months for 3 years, "
            "then annually for life. (2) Side effects to manage: "
            "Xerostomia (dry mouth) — drink water frequently, use saliva substitutes. "
            "Trismus (jaw stiffness) — physiotherapy exercises 3x daily. "
            "Dysphagia (difficulty swallowing) — speech therapy, soft diet. "
            "Mucositis (mouth sores) — antiseptic rinses, soft toothbrush. "
            "(3) Dental care: radiation causes weakened jaw bone, regular dental cleaning essential. "
            "(4) Nutrition support: dietician counselling for maintaining weight during and after treatment. "
            "(5) Psychological support: depression is common — refer to palliative care team."
        ),
    },
    {
        "id": "alcohol_cancer",
        "title": "Alcohol and oral cancer risk",
        "content": (
            "Alcohol is an independent risk factor for oral cancer and multiplies tobacco's carcinogenic effect. "
            "Risk increases with: quantity (more than 2 drinks/day), frequency, and duration of drinking. "
            "Alcohol causes local mucosal irritation, dehydrates cells, and impairs DNA repair. "
            "The combination of heavy tobacco AND heavy alcohol increases oral cancer risk by 30 times. "
            "Even moderate drinking (5 drinks/week) increases risk by 1.4-1.7 times. "
            "Types of alcohol — all carry risk. Country liquor (desi daru) often has toxic impurities. "
            "ASHA workers should screen for alcohol use alongside tobacco at every screening."
        ),
    },
    {
        "id": "pediatric_oral_health",
        "title": "Oral cancer risk in young people",
        "content": (
            "While oral cancer is more common in adults over 40, young people aged 15–35 are increasingly affected. "
            "Main reasons: early initiation of gutka and pan masala use, HPV infection. "
            "Gutka use among school children is reported in rural India due to low cost and availability. "
            "OSMF (submucous fibrosis) is now seen in teenagers who chew areca nut. "
            "Early signs in young users: burning sensation with spicy food, restricted mouth opening, "
            "white thickening of cheek mucosa. All youth using tobacco products should be screened. "
            "Schools and anganwadis should be targeted for OralVision screening outreach."
        ),
    },
    {
        "id": "tongue_cancer",
        "title": "Tongue cancer — signs and risks",
        "content": (
            "Tongue cancer is a specific subtype of oral cancer — the most common oral cancer site in India. "
            "Signs: persistent ulcer on lateral (side) border or under-surface of tongue; red or white patch; "
            "lump or thickening; pain that may radiate to ear; difficulty moving tongue. "
            "Risk factors: same as oral cancer — tobacco, alcohol, HPV, poor oral hygiene. "
            "Tongue cancer tends to spread to neck lymph nodes early — neck swelling is a warning sign. "
            "The lateral border of tongue is most commonly affected. "
            "OralVision AI analyzes tongue images specifically for suspicious lesion patterns."
        ),
    },
    {
        "id": "ayushman_bharat",
        "title": "Ayushman Bharat cancer coverage",
        "content": (
            "Ayushman Bharat PM-JAY (Pradhan Mantri Jan Arogya Yojana) provides health insurance coverage: "
            "Coverage: ₹5 lakhs per family per year for secondary and tertiary hospitalizations. "
            "Cancer package includes: surgery, chemotherapy, radiation therapy, targeted therapy, biopsy, "
            "imaging (CT, MRI, PET scan), ICU care, follow-up. "
            "Eligibility: based on SECC 2011 data — poorest 40% of population (~10.74 crore families). "
            "How to check: call 14555 (PM-JAY helpline, 24x7), visit pmjay.gov.in, or visit nearest empanelled hospital. "
            "Empanelled hospitals: all government medical colleges, district hospitals, and many private hospitals. "
            "Documents needed: Aadhaar card and PM-JAY card or BPL card."
        ),
    },
    {
        "id": "tongue_ulcer_vs_cancer",
        "title": "How to tell if a mouth ulcer is cancerous",
        "content": (
            "Distinguishing dangerous mouth ulcers from normal aphthous ulcers (cold sores): "
            "CONCERNING (possibly cancerous): Persists more than 2 weeks without healing; hard or indurated edges "
            "(feels firm/raised); painless in early stages (pain is a LATE sign); irregular jagged borders; "
            "red, white, or mixed color floor; associated neck swelling. "
            "LESS CONCERNING (likely benign): Heals within 7–10 days; soft, smooth edges; often painful; "
            "round/oval with yellow-white center (aphthous); triggered by stress, nutritional deficiency. "
            "RULE: Any ulcer not healing in 2 weeks MUST be evaluated by a doctor and biopsied if suspicious. "
            "OralVision AI flags suspicious ulcer patterns but cannot replace biopsy."
        ),
    },
    {
        "id": "hindi_symptoms",
        "title": "मुँह के कैंसर के लक्षण (Symptoms in Hindi)",
        "content": (
            "मुँह के कैंसर के प्रमुख लक्षण (मुँह की बीमारी के संकेत): "
            "(1) मुँह में 2 हफ्ते से ज़्यादा न ठीक होने वाला ज़ख्म या घाव। "
            "(2) मुँह के अंदर लाल या सफेद धब्बे (दाग)। "
            "(3) मुँह में गांठ या सूजन। "
            "(4) कुछ निगलने या चबाने में तकलीफ। "
            "(5) मुँह सुन्न हो जाना। "
            "(6) बिना वजह दांत हिलना। "
            "(7) आवाज़ में बदलाव या कानों में दर्द। "
            "तम्बाकू, गुटखा, पान मसाला बंद करें। "
            "इन लक्षणों में से कोई भी हो तो तुरंत डॉक्टर को दिखाएँ। "
            "OralVision ऐप से AI द्वारा मुँह की जाँच करवाएं।"
        ),
    },
    {
        "id": "neck_lump",
        "title": "Neck lump and oral cancer",
        "content": (
            "A new, painless lump in the neck can be a sign of oral cancer that has spread to lymph nodes. "
            "This is called lymph node metastasis (N-stage disease). "
            "Characteristics of concerning neck lumps: appeared suddenly, painless, firm or hard, "
            "growing progressively, associated with mouth sore or voice change. "
            "IMPORTANT: A negative oral cavity exam does NOT exclude oral cancer — the primary tumor may be "
            "in the tonsil, base of tongue, or nasopharynx (not visible on routine oral exam). "
            "Any adult with a neck lump lasting more than 3 weeks needs urgent ENT evaluation and panendoscopy. "
            "OralVision AI covers visible oral cavity — ENT specialist needed for oropharyngeal/neck evaluation."
        ),
    },
    {
        "id": "screening_frequency",
        "title": "How often should oral cancer screening be done?",
        "content": (
            "Recommended oral cancer screening frequency by risk profile: "
            "HIGH RISK (tobacco users above 40, previous lesions, heavy drinkers): Screen every 6 months. "
            "MEDIUM RISK (tobacco users 30–40, or alcohol with no tobacco): Screen annually. "
            "LOW RISK (no tobacco, no alcohol, no suspicious symptoms): Screen every 2–3 years, but annually from age 40. "
            "Under NPCDCS guidelines: all adults above 30 in rural India should receive at least annual oral screening. "
            "Community camps targeting high-tobacco-use areas should be conducted quarterly. "
            "Post-treatment surveillance: every 1–3 months for first 2 years, then 6-monthly."
        ),
    },
    {
        "id": "oralvision_usage",
        "title": "How to use OralVision for screening",
        "content": (
            "Step-by-step guide for ASHA workers using OralVision: "
            "(1) Log in with your assigned OralVision credentials. "
            "(2) Go to 'New Screening' and enter patient ID, age, gender, state, district. "
            "(3) Select tobacco habit type from the dropdown (specific type matters for AI accuracy). "
            "(4) Capture image: Click 'Open Camera' → ask patient to open mouth wide → position camera "
            "so the entire oral cavity is visible → tap capture. "
            "(5) Review preview image — ensure good lighting, focus, and full cavity visible. "
            "(6) Click 'Run AI Screening' — results appear within 10–15 seconds. "
            "(7) Read the risk level, clinical explanation, and recommendation carefully. "
            "(8) Follow the recommended action: refer, follow up, or reassure. "
            "(9) Print result for patient record if needed. "
            "Good images improve AI accuracy significantly — ensure bright lighting and patient cooperative."
        ),
    },
    {
        "id": "image_quality_tips",
        "title": "How to take a good oral cavity photo for AI analysis",
        "content": (
            "Image quality significantly affects OralVision AI accuracy. Best practices: "
            "(1) LIGHTING: Use phone torch or natural daylight — avoid dark images. "
            "(2) POSITION: Ask patient to open mouth as wide as possible and tilt head back slightly. "
            "(3) FOCUS: Hold phone 15–20 cm from mouth — wait for camera to auto-focus before capturing. "
            "(4) COVERAGE: Ensure tongue, cheeks, gums, and palate are all visible. Use a tongue depressor if available. "
            "(5) STABILITY: Keep phone steady — blurry images reduce AI accuracy. "
            "(6) RETAKE: If image is dark, blurry, or mouth is partially closed — retake. "
            "The OralVision camera modal shows a circular guide — position oral cavity inside the circle. "
            "Multiple photos can be taken — use the clearest one."
        ),
    },
]

SUGGESTED_QUESTIONS = [
    "What are the early signs of oral cancer?",
    "What should I do if risk is HIGH?",
    "How does tobacco cause oral cancer?",
    "What is leukoplakia and is it dangerous?",
    "What government schemes cover cancer treatment?",
    "What oral hygiene tips should I give patients?",
    "What does the AI confidence score mean?",
    "How does the OralVision AI work?",
    "How do I take a good oral cavity photo?",
    "How often should patients be screened?",
]


@lru_cache(maxsize=1)
def _load_embedder():
    """Load sentence-transformer model once, cached."""
    try:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Sentence-transformer loaded for RAG chatbot")
        return embedder
    except Exception as e:
        logger.error("Failed to load sentence-transformer: %s", e)
        return None


@lru_cache(maxsize=1)
def _get_kb_embeddings():
    """Pre-compute knowledge base embeddings once."""
    embedder = _load_embedder()
    if embedder is None:
        return None, None
    import numpy as np
    texts = [f"{item['title']}. {item['content']}" for item in KNOWLEDGE_BASE]
    embeddings = embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return texts, embeddings


def _retrieve_top_k(message: str, top_k: int = 3):
    """Retrieve top-k relevant KB entries using cosine similarity."""
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    embedder = _load_embedder()
    _, kb_embeddings = _get_kb_embeddings()

    if embedder is None or kb_embeddings is None:
        return [], []

    query_embedding = embedder.encode([message], convert_to_numpy=True)
    sims = cosine_similarity(query_embedding, kb_embeddings)[0]
    top_indices = np.argsort(sims)[::-1][:top_k]
    return top_indices, sims


async def _gemini_answer_async(
    message: str,
    context_chunks: List[dict],
    history: Optional[List[dict]] = None,
) -> Optional[str]:
    """
    Use Gemini to synthesize a natural language answer from retrieved KB chunks.
    Falls back to None if API unavailable.
    """
    try:
        from app.core.config import get_settings
        settings = get_settings()
        if not settings.google_api_key:
            return None

        import google.generativeai as genai
        genai.configure(api_key=settings.google_api_key)

        # Build context from retrieved chunks
        context = "\n\n".join(
            f"[{c['title']}]\n{c['content']}"
            for c in context_chunks
        )

        # Build conversation history for multi-turn
        history_text = ""
        if history:
            for turn in history[-6:]:  # Last 3 exchanges
                role = "User" if turn["role"] == "user" else "Assistant"
                history_text += f"{role}: {turn['content']}\n"

        system_prompt = (
            "You are OralVision AI, an expert oral cancer clinical assistant built for ASHA workers "
            "and clinicians in rural India. You have deep knowledge of oral oncology, Indian government "
            "health schemes (PM-JAY, NPCDCS, NHM), and clinical protocols.\n\n"
            "RULES:\n"
            "1. Answer ONLY using the provided knowledge context below.\n"
            "2. Be clinically precise, warm, and practical — ASHA workers need actionable guidance.\n"
            "3. For HIGH RISK situations, ALWAYS emphasize immediate referral.\n"
            "4. Mention specific resources (phone numbers, schemes) when relevant.\n"
            "5. Keep answers concise — 3–5 sentences max. Use bullet points for lists.\n"
            "6. If the question is outside oral cancer/health scope, politely redirect.\n"
            "7. Never provide personal medical advice — always recommend professional evaluation.\n\n"
            f"KNOWLEDGE CONTEXT:\n{context}"
        )

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=512,
            ),
        )

        full_message = f"{history_text}User: {message}" if history_text else message
        response = await model.generate_content_async(full_message)
        return response.text.strip()

    except Exception as e:
        logger.warning("Gemini chatbot synthesis failed: %s", e)
        return None


async def answer_query_async(
    message: str,
    top_k: int = 3,
    history: Optional[List[dict]] = None,
) -> dict:
    """
    Full async RAG pipeline with optional Gemini synthesis.
    1. Retrieve top-k KB entries via cosine similarity (run in executor to avoid blocking)
    2. If Gemini available, synthesize a natural language answer (async)
    3. Fallback to direct KB content if Gemini unavailable
    4. Keyword fallback if embeddings fail
    """
    import asyncio
    try:
        # Run CPU-bound embedding search in thread pool
        loop = asyncio.get_running_loop()
        top_indices, sims = await loop.run_in_executor(
            None, _retrieve_top_k, message, top_k
        )

        if len(top_indices) == 0:
            return {
                "answer": _keyword_fallback(message),
                "related_topics": [],
                "sources": [],
                "method": "keyword",
            }

        primary    = KNOWLEDGE_BASE[top_indices[0]]
        supporting = [KNOWLEDGE_BASE[i] for i in top_indices[1:] if sims[i] > 0.20]

        sources = [
            {"title": KNOWLEDGE_BASE[i]["title"], "relevance": round(float(sims[i]), 2)}
            for i in top_indices if sims[i] > 0.15
        ]

        # Async Gemini synthesis
        context_chunks  = [primary] + supporting
        gemini_answer   = await _gemini_answer_async(message, context_chunks, history)

        if gemini_answer:
            return {
                "answer":         gemini_answer,
                "related_topics": [s["title"] for s in supporting],
                "sources":        sources,
                "method":         "gemini_rag",
            }

        # Direct KB content fallback
        answer_parts = [primary["content"]]
        if supporting:
            answer_parts.append(
                "\n\n**Also relevant:** " + " | ".join(s["title"] for s in supporting)
            )

        return {
            "answer":         answer_parts[0],
            "related_topics": [s["title"] for s in supporting],
            "sources":        sources,
            "method":         "semantic",
        }

    except Exception as e:
        logger.error("RAG query failed: %s", e)
        return {
            "answer":  _keyword_fallback(message),
            "sources": [],
            "method":  "keyword_fallback",
            "related_topics": [],
        }


# Keep a sync alias for backwards compatibility (used by test scripts)
def answer_query(
    message: str,
    top_k: int = 3,
    history: Optional[List[dict]] = None,
) -> dict:
    """Synchronous wrapper — only call from non-async (test/script) contexts."""
    import asyncio
    try:
        # asyncio.run() creates a fresh event loop — safe from sync/test contexts
        return asyncio.run(answer_query_async(message, top_k, history))
    except Exception as e:
        logger.error("Sync answer_query wrapper failed: %s", e)
        return {
            "answer": _keyword_fallback(message),
            "sources": [],
            "method": "keyword_fallback",
            "related_topics": [],
        }


def _keyword_fallback(message: str) -> str:
    """Simple keyword fallback when embeddings unavailable."""
    msg = message.lower()
    if any(w in msg for w in ["sign", "symptom", "warning", "लक्षण"]):
        return KNOWLEDGE_BASE[1]["content"]
    if any(w in msg for w in ["risk", "cause", "factor"]):
        return KNOWLEDGE_BASE[2]["content"]
    if any(w in msg for w in ["high", "urgent", "refer", "emergency"]):
        return KNOWLEDGE_BASE[3]["content"]
    if any(w in msg for w in ["prevent", "avoid"]):
        return KNOWLEDGE_BASE[8]["content"]
    if any(w in msg for w in ["tobacco", "bidi", "gutka", "pan", "khaini"]):
        return KNOWLEDGE_BASE[7]["content"]
    if any(w in msg for w in ["treat", "surgery", "chemo", "radiation"]):
        return KNOWLEDGE_BASE[10]["content"]
    if any(w in msg for w in ["asha", "worker", "screen"]):
        return KNOWLEDGE_BASE[11]["content"]
    if any(w in msg for w in ["leukoplakia", "white patch", "sफेद"]):
        return KNOWLEDGE_BASE[15]["content"]
    if any(w in msg for w in ["ayushman", "scheme", "free", "government", "pmjay"]):
        return KNOWLEDGE_BASE[12]["content"]
    if any(w in msg for w in ["how", "photo", "image", "camera", "use"]):
        return KNOWLEDGE_BASE[34]["content"]
    return KNOWLEDGE_BASE[0]["content"]
