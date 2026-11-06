# -*- coding: utf-8 -*-
"""
WorkConnect Trilingual Translation Dictionary
Supports English (en), Telugu (te), and Hindi (hi).
Includes UI labels, trade names, navigation, buttons, forms, status messages, and voice prompts.
"""

TRANSLATIONS = {
    "en": {
        # Navigation & Brand
        "brand_name": "WorkConnect",
        "tagline": "Local Work. Real Opportunities.",
        "nav_home": "Home",
        "nav_browse_jobs": "Browse Jobs",
        "nav_post_job": "Post a Job",
        "nav_worker_dashboard": "Worker Dashboard",
        "nav_employer_dashboard": "Employer Dashboard",
        "nav_candidate_matcher": "🎯 Candidate Matcher",
        "nav_login": "Login",
        "nav_register": "Register",
        "nav_logout": "Logout",
        "nav_profile": "My Profile",
        "nav_saved_jobs": "Saved Jobs",
        "nav_notifications": "Notifications",

        # Roles
        "role_worker": "Worker / Job Seeker",
        "role_employer": "Employer / Contractor",
        "logged_in_as": "Logged in as",

        # Homepage Hero
        "hero_title": "Find the right work. Build your future.",
        "hero_subtitle": "WorkConnect brings workers and employers together. Discover local opportunities, find skilled people, and make work simpler.",
        "hero_explore_jobs": "Explore Jobs",
        "hero_post_job": "Post a Job",
        "hero_voice_reg": "🎤 Register by Voice (Simple & Easy)",
        "hero_worker_cta": "Register as Worker",
        "hero_employer_cta": "Register as Employer",

        # Trades & Visual Navigation
        "trade_mason": "Mason / Construction",
        "trade_driver": "Driver (Auto/Cab/Truck)",
        "trade_electrician": "Electrician",
        "trade_painter": "Painter",
        "trade_farm_worker": "Farm Worker / Agriculture",
        "trade_carpenter": "Carpenter",
        "trade_plumber": "Plumber",
        "trade_helper": "General Helper",
        "filter_by_trade": "Filter by Trade Picture",
        "all_trades": "All Trades",

        # Job Card & Browse
        "search_placeholder": "Search jobs by title, trade, or location...",
        "all_locations": "All Locations",
        "filter_button": "Filter",
        "reset_filters": "Reset",
        "sort_by": "Sort by",
        "sort_match": "Intelligent Match Score",
        "sort_newest": "Newest First",
        "sort_wage_high": "Wage: High to Low",
        "sort_wage_low": "Wage: Low to High",
        "sort_positions": "Positions Available",
        "daily_wage": "Daily Wage",
        "positions_left": "positions left",
        "listen_job": "🔊 Listen to Job Details",
        "apply_now": "⚡ Apply Now",
        "already_applied": "✓ Applied",
        "job_filled": "Filled",
        "save_job": "Bookmark Job",
        "saved_job": "★ Saved",
        "report_job": "🚩 Report Job",
        "verified_employer": "✓ Verified Employer",
        "why_matches": "Why this job matches you:",

        # Match Explanations
        "match_excellent": "Excellent Match",
        "match_good": "Good Match",
        "match_moderate": "Moderate Match",
        "match_low": "Low Match",
        "match_skill_exact": "Exact trade / skill match",
        "match_location_exact": "Exact locality match",
        "match_wage_good": "Offered wage meets your expected rate",
        "match_exp_good": "Experience fits requirement",
        "match_avail_good": "Availability aligns",

        # Voice AI Registration
        "voice_title": "Voice AI Worker Registration",
        "voice_subtitle": "Speak in Telugu, Hindi, or English to create your profile without typing long forms.",
        "voice_start": "Start Voice Assistant",
        "voice_listening": "Listening... Please speak now",
        "voice_processing": "Processing your voice...",
        "voice_confirm_title": "Confirm your answer",
        "voice_replay_q": "🔊 Replay Question",
        "voice_repeat_ans": "🎤 Speak Again",
        "voice_confirm_btn": "✓ Yes, Continue",
        "voice_edit_manual": "✏️ Edit Manually",
        "voice_q_name": "What is your full name?",
        "voice_q_skill": "What is your main trade or skill? For example: Electrician, Driver, Mason, Painter, or Farm worker.",
        "voice_q_location": "Which town or village do you live in?",
        "voice_q_experience": "How many years of work experience do you have?",
        "voice_q_wage": "What is your expected daily wage in Rupees?",
        "voice_q_email": "What is your email address or phone number?",
        "voice_q_password": "Create a password for your account.",
        "voice_completed": "All details collected! Click Register Profile below.",

        # Auth & Dashboards
        "login_title": "Sign In to WorkConnect",
        "login_worker_tab": "Worker Login",
        "login_employer_tab": "Employer Login",
        "email_label": "Email Address",
        "password_label": "Password",
        "confirm_password_label": "Confirm Password",
        "login_btn": "Sign In",
        "dont_have_account": "Don't have an account?",
        "already_have_account": "Already have an account? Sign In",
        "register_worker_title": "Worker Registration",
        "register_employer_title": "Employer Registration",
        "edit_profile": "Edit Profile & Preferences",
        "save_changes": "Save Changes",

        # Employer Dashboard
        "employer_dashboard_title": "Employer Management Portal",
        "posted_jobs": "Posted Jobs",
        "active_requirements": "Active Requirements",
        "total_applicants": "Total Applicants",
        "post_new_job": "Post New Job Requirement",
        "schedule_interview": "📅 Schedule Meeting",
        "verify_company": "Get Verified Employer Badge",
        "status_pending": "Pending",
        "status_shortlisted": "Shortlisted",
        "status_confirmed": "Confirmed",
        "status_rejected": "Rejected",

        # Extra Features
        "reports_title": "Report suspicious job or account",
        "report_reason_fake": "Fake job or misleading information",
        "report_reason_wage": "Wage dispute / not paying agreed amount",
        "report_reason_spam": "Spam or suspicious behavior",
        "report_reason_other": "Other violation",
        "report_submit": "Submit Report",
        "interviews_title": "Upcoming Meetings",
        "no_interviews": "No meetings scheduled yet.",
        "ai_assistant_btn": "💬 WorkConnect AI",
        "ai_assistant_title": "WorkConnect Smart Assistant",
        "ai_assistant_placeholder": "Ask in English, Telugu, or Hindi (e.g., 'Find painter jobs in Kakinada')...",
        "send": "Send",
        "close": "Close"
    },

    "te": {
        # Navigation & Brand
        "brand_name": "వర్క్ కనెక్ట్",
        "tagline": "స్థానిక పనులు • నిజమైన అవకాశాలు.",
        "nav_home": "హోమ్",
        "nav_browse_jobs": "పనులను చూడండి",
        "nav_post_job": "పనిని పోస్ట్ చేయండి",
        "nav_worker_dashboard": "కూలీల డాష్‌బోర్డ్",
        "nav_employer_dashboard": "యజమాని డాష్‌బోర్డ్",
        "nav_candidate_matcher": "🎯 సరిపోయే పనివారు",
        "nav_login": "లాగిన్",
        "nav_register": "రిజిస్టర్",
        "nav_logout": "లాగౌట్",
        "nav_profile": "నా ప్రొఫైల్",
        "nav_saved_jobs": "దాచుకున్న పనులు",
        "nav_notifications": "నోటిఫికేషన్లు",

        # Roles
        "role_worker": "పనివారు / కూలీలు",
        "role_employer": "యజమాని / కాంట్రాక్టర్",
        "logged_in_as": "లాగిన్ అయ్యారు:",

        # Homepage Hero
        "hero_title": "సరైన పనిని కనుగొనండి. మీ భవిష్యత్తును నిర్మించుకోండి.",
        "hero_subtitle": "వర్క్ కనెక్ట్ పనివారిని మరియు యజమానులను సులభంగా కలుపుతుంది. స్థానిక పనులు, నైపుణ్యం గల కార్మికులను తక్షణమే పొందండి.",
        "hero_explore_jobs": "పనులను వెతకండి",
        "hero_post_job": "పని అవసరం పోస్ట్ చేయండి",
        "hero_voice_reg": "🎤 మాట్లాడి రిజిస్టర్ అవ్వండి (చాలా సులభం)",
        "hero_worker_cta": "కూలీగా నమోదు చేసుకోండి",
        "hero_employer_cta": "యజమానిగా నమోదు చేసుకోండి",

        # Trades & Visual Navigation
        "trade_mason": "మేస్త్రీ / భవన నిర్మాణ పని",
        "trade_driver": "డ్రైవర్ (ఆటో/కారు/ట్రాక్టర్)",
        "trade_electrician": "ఎలక్ట్రీషియన్ / కరెంట్ పని",
        "trade_painter": "పెయింటర్ / రంగుల పని",
        "trade_farm_worker": "వ్యవసాయ కూలీ",
        "trade_carpenter": "వడ్రంగి పని",
        "trade_plumber": "ప్లంబర్ / పైపుల పని",
        "trade_helper": "హెల్పర్ / సహాయకుడు",
        "filter_by_trade": "చిత్రాల ద్వారా పనిని ఎంచుకోండి",
        "all_trades": "అన్ని పనులు",

        # Job Card & Browse
        "search_placeholder": "పని పేరు, వృత్తి లేదా ఊరి పేరుతో వెతకండి...",
        "all_locations": "అన్ని ప్రాంతాలు",
        "filter_button": "ఫిల్టర్",
        "reset_filters": "రీసెట్",
        "sort_by": "క్రమబద్ధీకరించు",
        "sort_match": "బాగా సరిపోయే పనులు",
        "sort_newest": "కొత్తవి మొదట",
        "sort_wage_high": "ఎక్కువ కూలీ మొదట",
        "sort_wage_low": "తక్కువ కూలీ మొదట",
        "sort_positions": "మిగిలిన ఖాళీలు",
        "daily_wage": "రోజువారీ కూలీ",
        "positions_left": "ఖాళీలు మిగిలి ఉన్నాయి",
        "listen_job": "🔊 పని వివరాలను వినండి",
        "apply_now": "⚡ దరఖాస్తు చేసుకోండి",
        "already_applied": "✓ దరఖాస్తు చేయబడింది",
        "job_filled": "పూర్తయింది",
        "save_job": "పనిని దాచుకోండి",
        "saved_job": "★ దాచబడింది",
        "report_job": "🚩 ఫిర్యాదు చేయండి",
        "verified_employer": "✓ ధృవీకరించబడిన యజమాని",
        "why_matches": "ఈ పని మీకు ఎందుకు సరిపోతుంది:",

        # Match Explanations
        "match_excellent": "అద్భుతంగా సరిపోతుంది (ఎక్సలెంట్)",
        "match_good": "బాగా సరిపోతుంది",
        "match_moderate": "ఓ మోస్తరుగా సరిపోతుంది",
        "match_low": "తక్కువగా సరిపోతుంది",
        "match_skill_exact": "మీ వృత్తికి సరిగ్గా సరిపోతుంది",
        "match_location_exact": "మీ సొంత ఊరు లేదా దగ్గర ప్రాంతం",
        "match_wage_good": "మీరు ఆశించిన కూలీ లభిస్తుంది",
        "match_exp_good": "మీ అనుభవానికి తగిన పని",
        "match_avail_good": "మీ లభ్యతకు అనుకూలం",

        # Voice AI Registration
        "voice_title": "వాయిస్ AI ద్వారా సులభమైన రిజిస్ట్రేషన్",
        "voice_subtitle": "రాయడం రాకపోయినా ఫరవాలేదు. తెలుగులో మాట్లాడి మీ ప్రొఫైల్ సులభంగా పూర్తి చేయండి.",
        "voice_start": "వాయిస్ అసిస్టెంట్‌ను ప్రారంభించండి",
        "voice_listening": "వింటున్నాను... దయచేసి ఇప్పుడు మాట్లాడండి",
        "voice_processing": "మీ స్వరాన్ని తనిఖీ చేస్తున్నాము...",
        "voice_confirm_title": "మీ సమాధానాన్ని నిర్ధారించండి",
        "voice_replay_q": "🔊 ప్రశ్నను మళ్ళీ వినండి",
        "voice_repeat_ans": "🎤 మళ్ళీ మాట్లాడండి",
        "voice_confirm_btn": "✓ అవును, సరైనదే",
        "voice_edit_manual": "✏️ మార్చండి",
        "voice_q_name": "మీ పూర్తి పేరు ఏమిటి?",
        "voice_q_skill": "మీరు ఏ పని చేస్తారు? ఉదాహరణకు: ఎలక్ట్రీషియన్, డ్రైవర్, మేస్త్రీ, పెయింటర్, లేదా వ్యవసాయ కూలీ.",
        "voice_q_location": "మీరు ఏ ఊరు లేదా గ్రామంలో ఉంటారు?",
        "voice_q_experience": "మీకు ఎన్ని సంవత్సరాల పని అనుభవం ఉంది?",
        "voice_q_wage": "మీకు రోజుకు ఎంత కూలీ కావాలి?",
        "voice_q_email": "మీ ఈమెయిల్ లేదా ఫోన్ నంబర్ చెప్పండి.",
        "voice_q_password": "మీ ఖాతా కోసం పాస్‌వర్డ్ చెప్పండి.",
        "voice_completed": "అన్ని వివరాలు పూర్తయ్యాయి! కింద ఉన్న రిజిస్టర్ బటన్ నొక్కండి.",

        # Auth & Dashboards
        "login_title": "వర్క్ కనెక్ట్ లోకి ప్రవేశించండి",
        "login_worker_tab": "కూలీల లాగిన్",
        "login_employer_tab": "యజమానుల లాగిన్",
        "email_label": "ఈమెయిల్ చిరునామా",
        "password_label": "పాస్‌వర్డ్",
        "confirm_password_label": "పాస్‌వర్డ్ నిర్ధారించండి",
        "login_btn": "లాగిన్ అవ్వండి",
        "dont_have_account": "ఇంకా ఖాతా లేదా?",
        "already_have_account": "ఇప్పటికే ఖాతా ఉందా? లాగిన్ అవ్వండి",
        "register_worker_title": "కూలీల రిజిస్ట్రేషన్",
        "register_employer_title": "యజమానుల రిజిస్ట్రేషన్",
        "edit_profile": "ప్రొఫైల్ వివరాలను మార్చుకోండి",
        "save_changes": "మార్పులను సేవ్ చేయండి",

        # Employer Dashboard
        "employer_dashboard_title": "యజమానుల నిర్వహణ పోర్టల్",
        "posted_jobs": "పోస్ట్ చేసిన పనులు",
        "active_requirements": "ప్రస్తుత పనులు",
        "total_applicants": "మొత్తం దరఖాస్తుదారులు",
        "post_new_job": "కొత్త పని అవసరాన్ని పోస్ట్ చేయండి",
        "schedule_interview": "📅 సమావేశ సమయం నిర్ణయించండి",
        "verify_company": "ధృవీకరించబడిన బ్యాడ్జ్ పొందండి",
        "status_pending": "వేచి ఉంది (Pending)",
        "status_shortlisted": "ఎంపిక చేయబడింది (Shortlisted)",
        "status_confirmed": "నిర్ధారించబడింది (Confirmed)",
        "status_rejected": "రద్దు చేయబడింది (Rejected)",

        # Extra Features
        "reports_title": "అనుమానాస్పద పని లేదా ఖాతాపై ఫిర్యాదు",
        "report_reason_fake": "తప్పుడు సమాచారం లేదా నకిలీ పని",
        "report_reason_wage": "కూలీ వివాదం / చెప్పిన కూలీ ఇవ్వకపోవడం",
        "report_reason_spam": "స్పామ్ లేదా అసభ్య ప్రవర్తన",
        "report_reason_other": "ఇతర కారణం",
        "report_submit": "ఫిర్యాదు సమర్పించండి",
        "interviews_title": "రాబోయే సమావేశాలు",
        "no_interviews": "ప్రస్తుతం సమావేశాలు ఏవీ లేవు.",
        "ai_assistant_btn": "💬 వర్క్ కనెక్ట్ AI",
        "ai_assistant_title": "వర్క్ కనెక్ట్ స్మార్ట్ అసిస్టెంట్",
        "ai_assistant_placeholder": "తెలుగులో అడగండి (ఉదా: 'నర్సాపురంలో ఎలక్ట్రీషియన్ పనులు చూపించు')...",
        "send": "పంపండి",
        "close": "మూసివేయి"
    },

    "hi": {
        # Navigation & Brand
        "brand_name": "वर्क कनेक्ट",
        "tagline": "स्थानीय काम • असली अवसर.",
        "nav_home": "होम",
        "nav_browse_jobs": "नौकरियां देखें",
        "nav_post_job": "काम पोस्ट करें",
        "nav_worker_dashboard": "श्रमिक डैशबोर्ड",
        "nav_employer_dashboard": "नियोक्ता डैशबोर्ड",
        "nav_candidate_matcher": "🎯 सही उम्मीदवार",
        "nav_login": "लॉग इन",
        "nav_register": "रजिस्टर",
        "nav_logout": "लॉग आउट",
        "nav_profile": "मेरी प्रोफाइल",
        "nav_saved_jobs": "सहेजी गई नौकरियां",
        "nav_notifications": "सूचनाएं",

        # Roles
        "role_worker": "श्रमिक / कामगार",
        "role_employer": "मालिक / ठेकेदार",
        "logged_in_as": "लॉग इन हैं:",

        # Homepage Hero
        "hero_title": "सही काम पाएं। अपना भविष्य संवारें।",
        "hero_subtitle": "वर्क कनेक्ट कामगारों और नियोक्ताओं को आसानी से जोड़ता है। स्थानीय अवसर खोजें और कुशल लोगों से तुरंत जुड़ें।",
        "hero_explore_jobs": "काम खोजें",
        "hero_post_job": "काम की आवश्यकता पोस्ट करें",
        "hero_voice_reg": "🎤 बोलकर रजिस्टर करें (आसान और तेज)",
        "hero_worker_cta": "कामगार के रूप में पंजीकरण करें",
        "hero_employer_cta": "नियोक्ता के रूप में पंजीकरण करें",

        # Trades & Visual Navigation
        "trade_mason": "राजमिस्त्री / निर्माण कार्य",
        "trade_driver": "ड्राइवर (ऑटो/गाड़ी/ट्रैक्टर)",
        "trade_electrician": "इलेक्ट्रीशियन / बिजली मिस्त्री",
        "trade_painter": "पेंटर / रंगाई का काम",
        "trade_farm_worker": "खेत मजदूर / कृषि कार्य",
        "trade_carpenter": "बढ़ई / लकड़ी का काम",
        "trade_plumber": "प्लंबर / नलसाज",
        "trade_helper": "सहायक / हेल्पर",
        "filter_by_trade": "तस्वीरों द्वारा काम चुनें",
        "all_trades": "सभी प्रकार के काम",

        # Job Card & Browse
        "search_placeholder": "काम, हुनर या स्थान के अनुसार खोजें...",
        "all_locations": "सभी स्थान",
        "filter_button": "फ़िल्टर करें",
        "reset_filters": "रीसेट",
        "sort_by": "क्रमबद्ध करें",
        "sort_match": "सर्वोत्तम मेल",
        "sort_newest": "नवीनतम पहले",
        "sort_wage_high": "ज्यादा मजदूरी पहले",
        "sort_wage_low": "कम मजदूरी पहले",
        "sort_positions": "उपलब्ध पद",
        "daily_wage": "दैनिक मजदूरी",
        "positions_left": "पद रिक्त हैं",
        "listen_job": "🔊 काम का विवरण सुनें",
        "apply_now": "⚡ आवेदन करें",
        "already_applied": "✓ आवेदन कर दिया",
        "job_filled": "स्थान भर गया",
        "save_job": "काम सहेजें",
        "saved_job": "★ सहेजा गया",
        "report_job": "🚩 शिकायत करें",
        "verified_employer": "✓ सत्यापित नियोक्ता",
        "why_matches": "यह काम आपके लिए क्यों सही है:",

        # Match Explanations
        "match_excellent": "उत्कृष्ट मेल (Excellent)",
        "match_good": "अच्छा मेल",
        "match_moderate": "मध्यम मेल",
        "match_low": "कम मेल",
        "match_skill_exact": "आपके हुनर से बिल्कुल मेल खाता है",
        "match_location_exact": "आपका अपना शहर या नजदीकी क्षेत्र",
        "match_wage_good": "आपकी मनचाही मजदूरी के अनुरूप",
        "match_exp_good": "आपके अनुभव के अनुकूल",
        "match_avail_good": "आपकी उपलब्धता के अनुसार",

        # Voice AI Registration
        "voice_title": "वॉयस AI द्वारा आसान श्रमिक पंजीकरण",
        "voice_subtitle": "लिखने या पढ़ने में परेशानी? हिंदी में बोलकर बिना फॉर्म भरे अपनी प्रोफाइल बनाएं।",
        "voice_start": "वॉयस असिस्टेंट शुरू करें",
        "voice_listening": "सुन रहा हूँ... कृपया अब बोलें",
        "voice_processing": "आपकी आवाज समझी जा रही है...",
        "voice_confirm_title": "अपने उत्तर की पुष्टि करें",
        "voice_replay_q": "🔊 प्रश्न दोबारा सुनें",
        "voice_repeat_ans": "🎤 दोबारा बोलें",
        "voice_confirm_btn": "✓ हाँ, सही है",
        "voice_edit_manual": "✏️ सुधारें",
        "voice_q_name": "आपका पूरा नाम क्या है?",
        "voice_q_skill": "आप क्या काम करते हैं? जैसे: इलेक्ट्रीशियन, ड्राइवर, राजमिस्त्री, पेंटर, या खेत मजदूर।",
        "voice_q_location": "आप किस गांव या शहर में रहते हैं?",
        "voice_q_experience": "आपको कितने साल का काम का अनुभव है?",
        "voice_q_wage": "आपको रोजाना कितनी मजदूरी चाहिए?",
        "voice_q_email": "आपका ईमेल या फोन नंबर क्या है?",
        "voice_q_password": "अपने खाते के लिए पासवर्ड बनाएं।",
        "voice_completed": "सभी विवरण दर्ज हो गए! नीचे दिए गए रजिस्टर बटन पर क्लिक करें।",

        # Auth & Dashboards
        "login_title": "वर्क कनेक्ट में प्रवेश करें",
        "login_worker_tab": "श्रमिक लॉगिन",
        "login_employer_tab": "नियोक्ता लॉगिन",
        "email_label": "ईमेल पता",
        "password_label": "पासवर्ड",
        "confirm_password_label": "पासवर्ड की पुष्टि करें",
        "login_btn": "लॉग इन करें",
        "dont_have_account": "खाता नहीं है?",
        "already_have_account": "पहले से खाता है? लॉग इन करें",
        "register_worker_title": "श्रमिक पंजीकरण",
        "register_employer_title": "नियोक्ता पंजीकरण",
        "edit_profile": "प्रोफाइल विवरण बदलें",
        "save_changes": "बदलाव सहेजें",

        # Employer Dashboard
        "employer_dashboard_title": "नियोक्ता प्रबंधन पोर्टल",
        "posted_jobs": "पोस्ट की गई नौकरियां",
        "active_requirements": "सक्रिय आवश्यकताएं",
        "total_applicants": "कुल आवेदक",
        "post_new_job": "नया काम पोस्ट करें",
        "schedule_interview": "📅 मीटिंग तय करें",
        "verify_company": "सत्यापित बैज प्राप्त करें",
        "status_pending": "प्रतीक्षारत (Pending)",
        "status_shortlisted": "चयनित (Shortlisted)",
        "status_confirmed": "स्वीकृत (Confirmed)",
        "status_rejected": "अस्वीकृत (Rejected)",

        # Extra Features
        "reports_title": "संदिग्ध नौकरी या खाते की रिपोर्ट करें",
        "report_reason_fake": "गलत जानकारी या फर्जी काम",
        "report_reason_wage": "मजदूरी विवाद / तय राशि न देना",
        "report_reason_spam": "स्पैम या अनुचित व्यवहार",
        "report_reason_other": "अन्य कारण",
        "report_submit": "रिपोर्ट दर्ज करें",
        "interviews_title": "आगामी मीटिंग्स",
        "no_interviews": "वर्तमान में कोई मीटिंग निर्धारित नहीं है।",
        "ai_assistant_btn": "💬 वर्क कनेक्ट AI",
        "ai_assistant_title": "वर्क कनेक्ट स्मार्ट सहायक",
        "ai_assistant_placeholder": "हिंदी में पूछें (जैसे: 'मुझे नरसपुर में ड्राइवर का काम दिखाओ')...",
        "send": "भेजें",
        "close": "बंद करें"
    }
}

SUPPORTED_LANGUAGES = ["en", "te", "hi"]

def get_translation(key, lang="en", default=None):
    """Retrieve translated string for a given key and language code."""
    lang = lang if lang in SUPPORTED_LANGUAGES else "en"
    trans = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    if key in trans:
        return trans[key]
    # Fallback to English
    return TRANSLATIONS["en"].get(key, default or key)


__all__ = ["TRANSLATIONS", "SUPPORTED_LANGUAGES", "get_translation"]
