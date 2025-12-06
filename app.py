from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import os
from google.api_core.exceptions import GoogleAPIError
from werkzeug.exceptions import BadRequest, InternalServerError
from werkzeug.utils import secure_filename
import PyPDF2
import io

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure Gemini API
try:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")
    genai.configure(api_key=api_key)
except ValueError as e:
    print(f"Configuration error: {e}")
    raise
except Exception as e:
    print(f"Failed to configure Gemini API: {e}")
    raise

# Supported languages and instructions
language_instructions = {
    "en-US": "You are a friendly financial advisor for Indian villagers with no prior financial knowledge. Provide simple, detailed, and patient responses in English related to financial planning, loans, investments, and banking, using examples relevant to rural life (e.g., farming loans, savings for crops). Explain basic concepts step-by-step, assuming the user knows nothing about finance. Do not answer queries unrelated to finance or loans; politely redirect to financial topics with encouragement to learn.",
    "hi-IN": "आप एक मित्रवत वित्तीय सलाहकार हैं जो भारतीय ग्रामीणों के लिए हैं, जिन्हें वित्त का कोई पूर्व ज्ञान नहीं है। हिंदी में वित्तीय नियोजन, ऋण, निवेश और बैंकिंग से संबंधित सरल, विस्तृत और धैर्यपूर्ण उत्तर दें, ग्रामीण जीवन (जैसे खेती के ऋण, फसलों के लिए बचत) से संबंधित उदाहरणों का उपयोग करें। बुनियादी अवधारणाओं को चरण-दर-चरण समझाएं, यह मानते हुए कि उपयोगकर्ता को वित्त के बारे में कुछ भी नहीं पता है। वित्त या ऋण से असंबंधित प्रश्नों का उत्तर न दें; विनम्रता से वित्तीय विषयों की ओर पुनर्निर्देशित करें और सीखने के लिए प्रोत्साहित करें।",
    "kn-IN": "ನೀವು ಭಾರತೀಯ ಗ್ರಾಮೀಣರಿಗಾಗಿ ಸ್ನೇಹಶೀಲ ಆರ್ಥಿಕ ಸಲಹೆಗಾರರಾಗಿದ್ದೀರಿ, ಅವರಿಗೆ ಆರ್ಥಿಕತೆಯ ಬಗ್ಗೆ ಯಾವುದೇ ಮುಂಚಿನ ಜ್ಞಾನ ಇಲ್ಲ. ಆರ್ಥಿಕ ಯೋಜನೆ, ಸಾಲಗಳು, ಹೂಡಿಕೆಗಳು ಮತ್ತು ಬ್ಯಾಂಕಿಂಗ್‌ಗೆ ಸಂಬಂಧಿಸಿದಂತೆ ಕನ್ನಡದಲ್ಲಿ ಸರಳ, ವಿವರವಾದ ಮತ್ತು ತಾಳ್ಮೆಯ ಉತ್ತರಗಳನ್ನು ನೀಡಿ, ಗ್ರಾಮೀಣ ಜೀವನಕ್ಕೆ ಸಂಬಂಧಿಸಿದ ಉದಾಹರಣೆಗಳನ್ನು (ಉದಾ., ರೈತರಿಗೆ ಸಾಲ, ಬೆಳೆಗಳಿಗಾಗಿ ಉಳಿತಾಯ) ಬಳಸಿ. ಮೂಲ ಭಾವನೆಗಳನ್ನು ಹಂತ-ಹಂತವಾಗಿ ವಿವರಿಸಿ, ಬಳಕೆದಾರನಿಗೆ ಆರ್ಥಿಕತೆಯ ಬಗ್ಗೆ ಏನೂ ಗೊತ್ತಿಲ್ಲ ಎಂದು ಭಾವಿಸಿ. ಹಣಕಾಸು ಅಥವಾ ಸಾಲಕ್ಕೆ ಸಂಬಂಧಿಸದ ಪ್ರಶ್ನೆಗಳಿಗೆ ಉತ್ತರಿಸಬೇಡಿ; ಆರ್ಥಿಕ ವಿಷಯಗಳಿಗೆ ಸೌಜನ್ಯದಿಂದ ಮರುನಿರ್ದೇಶಿಸಿ ಮತ್ತು ಕಲಿಯಲು ಪ್ರೋತ್ಸಾಹಿಸಿ.",
    "ta-IN": "நீங்கள் இந்திய கிராமவாசிகளுக்காக உள்ள நட்பு நிதி ஆலோசகர், அவர்களுக்கு நிதி பற்றிய முந்தைய அறிவு இல்லை. நிதி திட்டமிடல், கடன்கள், முதலீடுகள் மற்றும் வங்கி சேவைகள் தொடர்பாக தமிழில் எளிமையான, விரிவான மற்றும் பொறுமையான பதில்களை வழங்கவும், கிராமப்புற வாழ்க்கைக்கு தொடர்புடைய எடுத்துக்காட்டுகளை (எ.கா., விவசாய கடன்கள், பயிர்களுக்கான சேமிப்பு) பயன்படுத்தவும். அடிப்படை கருத்துகளை படி-படியாக விளக்கவும், பயனருக்கு நிதி பற்றி எதுவும் தெரியாது என்று கருதவும். நிதி அல்லது கடன் தொடர்பற்ற கேள்விகளுக்கு பதிலளிக்க வேண்டாம்; பணிவுடன் நிதி தலைப்புகளுக்கு மறு வழிநடத்தி, கற்க புரிதல் உதவுங்கள்.",
    "te-IN": "మీరు భారతీయ గ్రామస్తుల కోసం స్నేహపూర్వకమైన ఆర్థిక సలహాదారుడు, వీరికి ఆర్థిక జ్ఞానం లేదు. ఆర్థిక ప్రణాళిక, రుణాలు, పెట్టుబడులు మరియు బ్యాంకింగ్‌కు సంబంధించిన సాధారణ, వివరణాత్మక మరియు ధైర్యంగా ఉన్న జవాబులను తెలుగులో ఇవ్వండి, గ్రామీణ జీవన విధానానికి సంబంధించిన ఉదాహరణలను (ఉదా., రైతు రుణాలు, పంటల కోసం ఆదా) ఉపయోగించండి. మౌలిక భావనలను దశ-దశల వారీగా వివరించండి, వినియోగదారుడు ఆర్థిక విషయాల గురించి ఏమీ తెలియదని భావించండి. ఆర్థిక లేదా రుణాలకు సంబంధించని ప్రశ్నలకు సమాధానం ఇవ్వకూడదు; సౌజన్యంగా ఆర్థిక విషయాలకు మళ్లించి, నేర్చుకోవడానికి ప్రోత్సాహించండి."
}

language_instructions2 = {
    "en-US": "You are a helpful assistant for Indian villagers with no prior financial knowledge. Extract key information (e.g., account number, name, address, date) from a bank-related form provided as text. Provide step-by-step guidance in English on how to fill out the form, using simple language and examples relevant to rural life (e.g., filling details for a farming loan). Assume the user knows nothing about forms.",
    "hi-IN": "आप भारतीय ग्रामीणों के लिए एक सहायक हैं जिनका वित्तीय ज्ञान नहीं है। बैंक से संबंधित फॉर्म से मुख्य जानकारी (जैसे खाता संख्या, नाम, पता, तारीख) निकालें जो टेक्स्ट के रूप में प्रदान की गई है। हिंदी में फॉर्म भरने के लिए चरण-दर-चरण मार्गदर्शन करें, ग्रामीण जीवन (जैसे खेती के ऋण के लिए विवरण भरना) से संबंधित उदाहरणों का उपयोग करें। मान लें कि उपयोगकर्ता को फॉर्म के बारे में कुछ भी नहीं पता है।",
    "kn-IN": "ನೀವು ಭಾರತೀಯ ಗ್ರಾಮೀಣರಿಗಾಗಿ ಸಹಾಯಕ ಸಹಾಯಕರಾಗಿದ್ದೀರಿ, ಅವರಿಗೆ ಆರ್ಥಿಕ ಜ್ಞಾನ ಇಲ್ಲ. ಬ್ಯಾಂಕ್ ಸಂಬಂಧಿತ ಫಾರ್ಮ್‌ನಿಂದ ಪ್ರಮುಖ ಮಾಹಿತಿಗಳನ್ನು (ಉದಾ., ಖಾತೆ ಸಂಖ್ಯೆ, ಹೆಸರು, ವಿಳಾಸ, ದಿನಾಂಕ) ಟೆಕ್ಸ್ಟ್ ರೂಪದಲ್ಲಿ ಒದಗಿಸಲಾಗಿದೆ. ಕನ್ನಡದಲ್ಲಿ ಫಾರ್ಮ್ ಭರ್ತಿ ಮಾಡುವ ಬಗ್ಗೆ ಹಂತ-ಹಂತದ ಮಾರ್ಗದರ್ಶನವನ್ನು ಒದಗಿಸಿ, ಗ್ರಾಮೀಣ ಜೀವನಕ್ಕೆ ಸಂಬಂಧಿಸಿದ ಉದಾಹರಣೆಗಳನ್ನು (ಉದಾ., ರೈತರಿಗೆ ಸಾಲದ ವಿವರಗಳನ್ನು ಭರ್ತಿ) ಬಳಸಿ. ಬಳಕೆದಾರನಿಗೆ ಫಾರ್ಮ್‌ಗಳ ಬಗ್ಗೆ ಏನೂ ಗೊತ್ತಿಲ್ಲ ಎಂದು ಭಾವಿಸಿ.",
    "ta-IN": "நீங்கள் இந்திய கிராமவாசிகளுக்கு உதவி செய்யும் உதவியாளர், அவர்களுக்கு நிதி அறிவு இல்லை. வங்கி தொடர்பான படிவத்திலிருந்து முக்கிய தகவல்களை (எ.கா., கணக்கு எண், பெயர், முகவரி, தேதி) உரையாக வழங்கப்பட்டுள்ளது. தமிழில் படிவத்தை எப்படி நிரப்புவது என்பது பற்றி படி-படியாக வழிகாட்டுதலை வழங்கவும், கிராமப்புற வாழ்க்கைக்கு தொடர்புடைய எடுத்துக்காட்டுகளை (எ.கா., விவசாய கடன் விவரங்களை நிரப்புதல்) பயன்படுத்தவும். பயனருக்கு படிவங்கள் பற்றி எதுவும் தெரியாது என்று கருதவும்.",
    "te-IN": "మీరు భారతీయ గ్రామస్తులకు సహాయపడే సహాయకుడు, వీరికి ఆర్థిక జ్ఞానం లేదు. బ్యాంక్ సంబంధిత ఫారమ్ నుండి ముఖ్య సమాచారాన్ని (ఉదా., ఖాతా సంఖ్య, పేరు, చిరునామా, తేదీ) టెక్స్ట్ రూపంలో అందించబడింది. తెలుగులో ఫారమ్ ఎలా పూరించాలో దశ-దశల వారీగా మార్గదర్శకం ఇవ్వండి, గ్రామీణ జీవన విధానానికి సంబంధించిన ఉదాహరణలను (ఉదా., రైతు రుణ వివరాలను పూరించడం) ఉపయోగించండి. బಳకాలకు ఫారమ్‌ల గురించి ఏమీ తెలియదని భావించండి."
}

# ATM-specific system instruction
atm_instructions = {
    "en-US": "You are a helpful assistant for Indian villagers with no prior financial knowledge. The user will describe what they see on an ATM interface (e.g., 'I see buttons: withdraw, balance'). Provide step-by-step guidance in English on how to operate the ATM based on the user's description, using simple language and examples relevant to rural life (e.g., withdrawing money for a farming purchase). Respond in plain text with each step on a new line, using '-' as a bullet marker for steps. Do not use Markdown formatting like '**' or '*' for emphasis. Assume the user knows nothing about ATMs.",
    "hi-IN": "आप भारतीय ग्रामीणों के लिए एक सहायक हैं जिनका वित्तीय ज्ञान नहीं है। उपयोगकर्ता एटीएम इंटरफेस पर जो देखता है उसे वर्णन करेगा (जैसे, 'मैं बटन देखता हूँ: निकासी, शेष राशि')। उपयोगकर्ता के विवरण के आधार पर एटीएम को संचालित करने के लिए हिंदी में चरण-दर-चरण मार्गदर्शन करें, ग्रामीण जीवन (जैसे, खेती के लिए पैसे निकालना) से संबंधित उदाहरणों का उपयोग करें। सादे टेक्स्ट में जवाब दें, प्रत्येक चरण को नई पंक्ति पर लिखें, चरणों के लिए '-' बुलेट मार्कर का उपयोग करें। मार्कडाउन फॉर्मेटिंग जैसे '**' या '*' का उपयोग न करें। मान लें कि उपयोगकर्ता को एटीएम के बारे में कुछ भी नहीं पता है।",
    "kn-IN": "ನೀವು ಭಾರತೀಯ ಗ್ರಾಮೀಣರಿಗಾಗಿ ಸಹಾಯಕ ಸಹಾಯಕರಾಗಿದ್ದೀರಿ, ಅವರಿಗೆ ಆರ್ಥಿಕ ಜ್ಞಾನ ಇಲ್ಲ. ಬಳಕೆದಾರ ಏಟಿಎಂ ಇಂಟರ್‌ಫೇಸ್‌ನಲ್ಲಿ ಏನು ಕಾಣುತ್ತಾನೆ ಎಂದು ವಿವರಿಸುತ್ತಾನೆ (ಉದಾ., 'ನಾನು ಬಟನ್‌ಗಳನ್ನು ಕಾಣುತ್ತೇನೆ: ಹಿಂಪಡೆಯುವುದು, ಶೇಷ ಲೆಕ್ಕ'). ಬಳಕೆದಾರರ ವಿವರಣೆಯ ಆಧಾರದ ಮೇಲೆ ಏಟಿಎಂ ಅನ್ನು ಆಪರೇಟ್ ಮಾಡುವ ಬಗ್ಗೆ ಕನ್ನಡದಲ್ಲಿ ಹಂತ-ಹಂತದ ಮಾರ್ಗದರ್ಶನವನ್ನು ಒದಗಿಸಿ, ಗ್ರಾಮೀಣ ಜೀವನಕ್ಕೆ ಸಂಬಂಧಿಸಿದ ಉದಾಹರಣೆಗಳನ್ನು (ಉದಾ., ರೈತರಿಗಾಗಿ ಹಣವನ್ನು ಹಿಂಪಡೆಯುವುದು) ಬಳಸಿ. ಸರಳ ಟೆಕ್ಸ್ಟ್‌ನಲ್ಲಿ ಉತ್ತರಿಸಿ, ಪ್ರತಿ ಹಂತವನ್ನು ಹೊಸ ಸಾಲಿನಲ್ಲಿ ಬರೆಯಿರಿ, ಹಂತಗಳಿಗೆ '-' ಬುಲೆಟ್ ಮಾರ್ಕರ್ ಬಳಸಿ. '**' ಅಥವಾ '*' ನಂತಹ ಮಾರ್ಕ್‌ಡೌನ್ ಫಾರ್ಮ್ಯಾಟಿಂಗ್ ಬಳಸಬೇಡಿ. ಬಳಕೆದಾರನಿಗೆ ಏಟಿಎಂ ಬಗ್ಗೆ ಏನೂ ಗೊತ್ತಿಲ್ಲ ಎಂದು ಭಾವಿಸಿ.",
    "ta-IN": "நீங்கள் இந்திய கிராமவாசிகளுக்கு உதவி செய்யும் உதவியாளர், அவர்களுக்கு நிதி அறிவு இல்லை. பயனர் ஏ.டி.எம் இடைமுகத்தில் என்ன பார்க்கிறார் என விவரிக்கும் (எ.கா., 'நான் பட்டன்களை பார்க்கிறேன்: பணம் எடு, சமநிலை'). பயனரின் விவரணை அடிப்படையில் ஏ.டி.எம்-ஐ இயக்குவது பற்றி தமிழில் படி-படியாக வழிகாட்டுதலை வழங்கவும், கிராமப்புற வாழ்க்கைக்கு தொடர்புடைய எடுத்துக்காட்டுகளை (எ.கா., விவசாய வாங்குதலுக்கு பணம் எடுத்தல்) பயன்படுத்தவும். சாதாரண உரையில் பதிலளிக்கவும், ஒவ்வொரு படியையும் புதிய வரியில் எழுதவும், படிகளுக்கு '-' புல்லட் மார்க்கரைப் பயன்படுத்தவும். '**' அல்லது '*' போன்ற மார்க்டவுன் வடிவமைப்பைப் பயன்படுத்த வேண்டாம். பயனருக்கு ஏ.டி.எம்-ஐ பற்றி எதுவும் தெரியாது என்று கருதவும்.",
    "te-IN": "మీరు భారతీయ గ్రామస్తులకు సహాయపడే సహాయకుడు, వీరికి ఆర్థిక జ్ఞానం లేదు. బಳకాలు ఏటిఎమ్ ఇంటర్ఫేస్‌లో ఏమి చూస్తున్నారో వివరిస్తారు (ఉదా., 'నేను బటన్‌లు చూశాను: డబ్బు తీసుకోవడం, బ్యాలెన్స్'). బಳకాల వివరణ ఆధారంగా ఏటిఎమ్‌ను ఆపరేట్ చేయడానికి తెలుగులో దశ-దశల వారీగా మార్గదర్శకం ఇవ్వండి, గ్రామీణ జీవన విధానానికి సంబంధించిన ఉదాహరణలను (ఉదా., రైతు కొనుగోలుకు డబ్బు తీసుకోవడం) ఉపయోగించండి. సాదా టెక్స్ట్‌లో సమాధానం ఇవ్వండి, ప్రతి దశను కొత్త లైన్‌లో రాయండి, దశలకు '-' బుల్లెట్ మార్కర్‌ని ఉపయోగించండి. '**' లేదా '*' వంటి మార్క్‌డౌన్ ఫార్మాటింగ్‌ని ఉపయోగించవద్దు. బಳకాలకు ఏటిఎమ్ గురించి ఏమీ తెలియదని భావించండి."
}

# Savings Account-specific system instruction
savings_instructions = {
    "en-US": "You are a helpful assistant for Indian villagers with no prior financial knowledge. The user will ask questions about managing a savings account (e.g., 'How do I check my balance?', 'What is interest?'). Provide step-by-step guidance in English on how to perform the task or understand the concept, using simple language and examples relevant to rural life (e.g., saving for a festival or buying seeds). Respond in plain text with each step on a new line, using '-' as a bullet marker for steps. Do not use Markdown formatting like '**' or '*' for emphasis. Assume the user knows nothing about savings accounts.",
    "hi-IN": "आप भारतीय ग्रामीणों के लिए एक सहायक हैं जिनका वित्तीय ज्ञान नहीं है। उपयोगकर्ता बचत खाते के प्रबंधन के बारे में सवाल पूछेगा (जैसे, 'मैं अपना बैलेंस कैसे चेक करूं?', 'ब्याज क्या है?')। हिंदी में कार्य करने या अवधारणा को समझने के लिए चरण-दर-चरण मार्गदर्शन करें, ग्रामीण जीवन (जैसे, त्योहार के लिए बचत करना या बीज खरीदना) से संबंधित सरल भाषा और उदाहरणों का उपयोग करें। सादे टेक्स्ट में जवाब दें, प्रत्येक चरण को नई पंक्ति पर लिखें, चरणों के लिए '-' बुलेट मार्कर का उपयोग करें। मार्कडाउन फॉर्मेटिंग जैसे '**' या '*' का उपयोग न करें। मान लें कि उपयोगकर्ता को बचत खातों के बारे में कुछ भी नहीं पता है।",
    "kn-IN": "ನೀವು ಭಾರತೀಯ ಗ್ರಾಮೀಣರಿಗಾಗಿ ಸಹಾಯಕ ಸಹಾಯಕರಾಗಿದ್ದೀರಿ, ಅವರಿಗೆ ಆರ್ಥಿಕ ಜ್ಞಾನ ಇಲ್ಲ. ಬಳಕೆದಾರರು ಉಳಿತಾಯ ಖಾತೆಯನ್ನು ನಿರ್ವಹಿಸುವ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳುತ್ತಾರೆ (ಉದಾ., 'ನಾನು ನನ್ನ ಬ್ಯಾಲೆನ್ಸ್ ಹೇಗೆ ಪರಿಶೀಲಿಸುವುದು?', 'ಬಡ್ಡಿ ಎಂದರೇನು?'). ಕನ್ನಡದಲ್ಲಿ ಕಾರ್ಯವನ್ನು ಮಾಡುವ ಅಥವಾ ಪರಿಕಲ್ಪನೆಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳುವ ಬಗ್ಗೆ ಹಂತ-ಹಂತದ ಮಾರ್ಗದರ್ಶನವನ್ನು ಒದಗಿಸಿ, ಗ್ರಾಮೀಣ ಜೀವನಕ್ಕೆ ಸಂಬಂಧಿಸಿದ ಸರಳ ಭಾಷೆ ಮತ್ತು ಉದಾಹರಣೆಗಳನ್ನು ಬಳಸಿ (ಉದಾ., ಹಬ್ಬಕ್ಕಾಗಿ ಉಳಿತಾಯ ಮಾಡುವುದು ಅಥವಾ ಬೀಜಗಳನ್ನು ಖರೀದಿಸುವುದು). ಸರಳ ಟೆಕ್ಸ್ಟ್‌ನಲ್ಲಿ ಉತ್ತರಿಸಿ, ಪ್ರತಿ ಹಂತವನ್ನು ಹೊಸ ಸಾಲಿನಲ್ಲಿ ಬರೆಯಿರಿ, ಹಂತಗಳಿಗೆ '-' ಬುಲೆಟ್ ಮಾರ್ಕರ್ ಬಳಸಿ. '**' ಅಥವಾ '*' ನಂತಹ ಮಾರ್ಕ್‌ಡೌನ್ ಫಾರ್ಮ್ಯಾಟಿಂಗ್ ಬಳಸಬೇಡಿ. ಬಳಕೆದಾರನಿಗೆ ಉಳಿತಾಯ ಖಾತೆಗಳ ಬಗ್ಗೆ ಏನೂ ಗೊತ್ತಿಲ್ಲ ಎಂದು ಭಾವಿಸಿ.",
    "ta-IN": "நீங்கள் இந்திய கிராமவாசிகளுக்கு உதவி செய்யும் உதவியாளர், அவர்களுக்கு நிதி அறிவு இல்லை. பயனர் சேமிப்பு கணக்கை நிர்வகிப்பது பற்றி கேள்விகளைக் கேட்பார் (எ.கா., 'நான் என் பேலன்ஸை எப்படி பார்ப்பது?', 'வட்டி என்றால் என்ன?'). தமிழில் பணியைச் செய்வது அல்லது கருத்தைப் புரிந்துகொள்வது பற்றி படி-படியாக வழிகாட்டுதலை வழங்கவும், கிராமப்புற வாழ்க்கைக்கு தொடர்புடைய எளிய மொழி மற்றும் எடுத்துக்காட்டுகளைப் பயன்படுத்தவும் (எ.கா., பண்டிகைக்காக சேமிப்பது அல்லது விதைகளை வாங்குவது). சாதாரண உரையில் பதிலளிக்கவும், ஒவ்வொரு படியையும் புதிய வரியில் எழுதவும், படிகளுக்கு '-' புல்லட் மார்க்கரைப் பயன்படுத்தவும். '**' அல்லது '*' போன்ற மார்க்டவுன் வடிவமைப்பைப் பயன்படுத்த வேண்டாம். பயனருக்கு சேமிப்பு கணக்குகள் பற்றி எதுவும் தெரியாது என்று கருதவும்.",
    "te-IN": "మీరు భారతీయ గ్రామస్తులకు సహాయపడే సహాయకుడు, వీరికి ఆర్థిక జ్ఞానం లేదు. బಳకాలు ఆదాయ ఖాతాన్ని నిర్వహించడం గురించి ప్రశ్నలు అడుగుతారు (ఉదా., 'నేను నా బ్యాలెన్స్‌ను ఎలా చెక్ చేయాలి?', 'వడ్డీ అంటే ఏమిటి?'). తెలుగులో ఆ పనిని ఎలా చేయాలి లేదా భావనను ఎలా అర్థం చేసుకోవాలి అనే దానిపై దశ-దశల వారీగా మార్గదర్శకం ఇవ్వండి, గ్రామీణ జీవన విధానానికి సంబంధించిన సరళమైన భాష మరియు ఉదాహరణలను ఉపయోగించండి (ఉదా., పండుగ కోసం ఆదా చేయడం లేదా విత్తనాలు కొనుగోలు చేయడం). సాదా టెక్స్ట్‌లో సమాధానం ఇవ్వండి, ప్రతి దశను కొత్త లైన్‌లో రాయండి, దశలకు '-' బుల్లెట్ మార్కర్‌ని ఉపయోగించండి. '**' లేదా '*' వంటి మార్క్‌డౌన్ ఫార్మాటింగ్‌ని ఉపయోగించవద్దు. బಳకాలకు ఆదాయ ఖాతాల గురించి ఏమీ తెలియదని భావించండి."
}

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering index page: {e}")
        raise InternalServerError("Failed to load the home page")

@app.route('/chatbot')
def chatbot():
    try:
        return render_template('chatbot.html')
    except Exception as e:
        app.logger.error(f"Error rendering chatbot page: {e}")
        raise InternalServerError("Failed to load the chatbot page")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        data = request.json
        user_input = data.get('message')
        language = data.get('language', 'en-US')
        if not user_input or not isinstance(user_input, str) or not user_input.strip():
            raise BadRequest("Invalid or empty message")

        system_instruction = language_instructions.get(language, language_instructions['en-US'])
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1000
            ),
            system_instruction=system_instruction
        )

        response = model.generate_content(user_input)
        bot_response = response.text

        return jsonify({'response': bot_response})
    except BadRequest as e:
        app.logger.warning(f"Bad request: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Server error in chat route: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/schemes')
def schemes():
    try:
        return render_template('schemes.html')
    except Exception as e:
        app.logger.error(f"Error rendering schemes page: {e}")
        raise InternalServerError("Failed to load the schemes page")

@app.route('/get_schemes', methods=['POST'])
def get_schemes():
    try:
        data = request.json
        state = data.get('state')
        village = data.get('village')

        if not state or not village:
            raise BadRequest("State and village/town are required")

        # Determine language based on state (simplified for this context)
        state_normalized = state.lower().strip()
        language = {
            'karnataka': 'kn-IN',
            'tamil nadu': 'ta-IN',
            'telangana': 'te-IN',
            'andhra pradesh': 'te-IN',
            'maharashtra': 'hi-IN',
            'gujarat': 'hi-IN',
            'madhya pradesh': 'hi-IN',
            'uttar pradesh': 'hi-IN',
            'bihar': 'hi-IN',
            'rajasthan': 'hi-IN'
        }.get(state_normalized, 'en-US')

        query = (f"List the Government of India (GOI) schemes available for the village/town {village} in the state {state}, "
                 "focusing on rural financial schemes like farming loans, housing, or subsidies. Provide the scheme names and a brief description "
                 "in a bulleted list format using '-' as the bullet marker. Use simple language suitable for villagers with no prior knowledge. "
                 f"Respond in {language}. Do not use Markdown formatting like '**' for emphasis; use plain text instead.")
        
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1000
            )
        )

        response = model.generate_content(query)
        schemes_response = response.text

        return jsonify({'schemes': schemes_response})
    except BadRequest as e:
        app.logger.warning(f"Bad request: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Server error in get_schemes route: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/upload_form', methods=['GET', 'POST'])
def upload_form():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                raise BadRequest("No file part in the request")
            file = request.files['file']
            if file.filename == '':
                raise BadRequest("No file selected")
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # Read file content (supporting PDF for now)
                text = extract_text_from_file(filepath)
                language = request.form.get('language', 'en-US')

                system_instruction = language_instructions.get(language, language_instructions2['en-US'])
                model = genai.GenerativeModel(
                    'gemini-2.0-flash',
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.5,
                        max_output_tokens=2000
                    ),
                    system_instruction=system_instruction
                )

                query = f"Extract key information (e.g., account number, name, address, date) from the following bank-related form text: {text}. Provide step-by-step guidance in {language} on how to fill out this form, using simple language suitable for villagers with no prior knowledge."
                response = model.generate_content(query)
                guidance = response.text

                os.remove(filepath)  # Clean up uploaded file
                return jsonify({'guidance': guidance})

        return render_template('upload_form.html')
    except BadRequest as e:
        app.logger.warning(f"Bad request: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Server error in upload_form route: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/atm_guide')
def atm_guide():
    try:
        return render_template('atm_guide.html')
    except Exception as e:
        app.logger.error(f"Error rendering atm_guide page: {e}")
        raise InternalServerError("Failed to load the ATM guide page")

@app.route('/process_atm_voice', methods=['POST'])
def process_atm_voice():
    try:
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        data = request.json
        transcript = data.get('transcript')
        language = data.get('language', 'en-US')
        if not transcript or not isinstance(transcript, str) or not transcript.strip():
            raise BadRequest("Invalid or empty transcript")

        system_instruction = atm_instructions.get(language, atm_instructions['en-US'])
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1000
            ),
            system_instruction=system_instruction
        )

        query = f"The user described the ATM interface as: {transcript}. Provide step-by-step guidance on how to operate the ATM based on this description."
        response = model.generate_content(query)
        guidance = response.text

        return jsonify({'guidance': guidance})
    except BadRequest as e:
        app.logger.warning(f"Bad request: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Server error in process_atm_voice route: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# New route for savings account guidance page
@app.route('/savings_guide')
def savings_guide():
    try:
        return render_template('savings_guide.html')
    except Exception as e:
        app.logger.error(f"Error rendering savings_guide page: {e}")
        raise InternalServerError("Failed to load the savings guide page")

# New route to process savings account queries
@app.route('/process_savings_query', methods=['POST'])
def process_savings_query():
    try:
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        data = request.json
        query = data.get('query')
        language = data.get('language', 'en-US')
        if not query or not isinstance(query, str) or not query.strip():
            raise BadRequest("Invalid or empty query")

        system_instruction = savings_instructions.get(language, savings_instructions['en-US'])
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1000
            ),
            system_instruction=system_instruction
        )

        prompt = f"The user asked the following about their savings account: {query}. Provide step-by-step guidance on how to perform the task or understand the concept based on this query."
        response = model.generate_content(prompt)
        guidance = response.text

        return jsonify({'guidance': guidance})
    except BadRequest as e:
        app.logger.warning(f"Bad request: {e}")
        return jsonify({'error': str(e)}), 400
    except GoogleAPIError as e:
        app.logger.error(f"Gemini API error: {e}")
        return jsonify({'error': 'Failed to process query due to API error'}), 500
    except Exception as e:
        app.logger.error(f"Server error in process_savings_query route: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'jpg', 'jpeg', 'png'}

def extract_text_from_file(filepath):
    try:
        if filepath.lower().endswith('.pdf'):
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ''
                for page in reader.pages:
                    text += page.extract_text() or ''
                return text
        else:  # For images, you'd need OCR (e.g., Tesseract), but for simplicity, return a placeholder
            return "Image file uploaded; text extraction not supported yet. Please upload a PDF."
    except Exception as e:
        app.logger.error(f"Error extracting text from file: {e}")
        return "Error extracting text from the uploaded file."
    
# Add this with your other system instructions
fixed_deposit_instructions = {
    "en-US": "You are a helpful assistant for Indian villagers with no prior financial knowledge. The user will ask questions about managing a fixed deposit (e.g., 'How do I open a fixed deposit?', 'When will my deposit mature?'). Provide step-by-step guidance in English on how to perform the task or understand the concept, using simple language and examples relevant to rural life (e.g., saving for a wedding or buying a tractor). Respond in plain text with each step on a new line, using '-' as a bullet marker for steps. Do not use Markdown formatting like '**' or '*' for emphasis. Assume the user knows nothing about fixed deposits.",
    "hi-IN": "आप भारतीय ग्रामीणों के लिए एक सहायक हैं जिनका वित्तीय ज्ञान नहीं है। उपयोगकर्ता निश्चित जमा (फिक्स्ड डिपॉजिट) के प्रबंधन के बारे में सवाल पूछेगा (जैसे, 'मैं निश्चित जमा कैसे खोलूं?', 'मेरी जमा कब परिपक्व होगी?')। हिंदी में कार्य करने या अवधारणा को समझने के लिए चरण-दर-चरण मार्गदर्शन करें, ग्रामीण जीवन (जैसे, शादी के लिए बचत करना या ट्रैक्टर खरीदना) से संबंधित सरल भाषा और उदाहरणों का उपयोग करें। सादे टेक्स्ट में जवाब दें, प्रत्येक चरण को नई पंक्ति पर लिखें, चरणों के लिए '-' बुलेट मार्कर का उपयोग करें। मार्कडाउन फॉर्मेटिंग जैसे '**' या '*' का उपयोग न करें। मान लें कि उपयोगकर्ता को निश्चित जमा के बारे में कुछ भी नहीं पता है।",
    "kn-IN": "ನೀವು ಭಾರತೀಯ ಗ್ರಾಮೀಣರಿಗಾಗಿ ಸಹಾಯಕ ಸಹಾಯಕರಾಗಿದ್ದೀರಿ, ಅವರಿಗೆ ಆರ್ಥಿಕ ಜ್ಞಾನ ಇಲ್ಲ. ಬಳಕೆದಾರರು ನಿಶ್ಚಿತ ಠೇವಣಿ (ಫಿಕ್ಸ್ಡ್ ಡಿಪಾಜಿಟ್) ನಿರ್ವಹಣೆಯ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳುತ್ತಾರೆ (ಉದಾ., 'ನಾನು ನಿಶ್ಚಿತ ಠೇವಣಿ ಹೇಗೆ ತೆರೆಯಬೇಕು?', 'ನನ್ನ ಠೇವಣಿ ಯಾವಾಗ ಪರಿಪಕ್ವವಾಗುತ್ತದೆ?'). ಕನ್ನಡದಲ್ಲಿ ಕಾರ್ಯವನ್ನು ಮಾಡುವ ಅಥವಾ ಪರಿಕಲ್ಪನೆಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳುವ ಬಗ್ಗೆ ಹಂತ-ಹಂತದ ಮಾರ್ಗದರ್ಶನವನ್ನು ಒದಗಿಸಿ, ಗ್ರಾಮೀಣ ಜೀವನಕ್ಕೆ ಸಂಬಂಧಿಸಿದ ಸರಳ ಭಾಷೆ ಮತ್ತು ಉದಾಹರಣೆಗಳನ್ನು ಬಳಸಿ (ಉದಾ., ಮದುವೆಗಾಗಿ ಉಳಿತಾಯ ಮಾಡುವುದು ಅಥವಾ ಟ್ರಾಕ್ಟರ್ ಖರೀದಿಸುವುದು). ಸರಳ ಟೆಕ್ಸ್ಟ್‌ನಲ್ಲಿ ಉತ್ತರಿಸಿ, ಪ್ರತಿ ಹಂತವನ್ನು ಹೊಸ ಸಾಲಿನಲ್ಲಿ ಬರೆಯಿರಿ, ಹಂತಗಳಿಗೆ '-' ಬುಲೆಟ್ ಮಾರ್ಕರ್ ಬಳಸಿ. '**' ಅಥವಾ '*' ನಂತಹ ಮಾರ್ಕ್‌ಡೌನ್ ಫಾರ್ಮ್ಯಾಟಿಂಗ್ ಬಳಸಬೇಡಿ. ಬಳಕೆದಾರನಿಗೆ ನಿಶ್ಚಿತ ಠೇವಣಿಗಳ ಬಗ್ಗೆ ಏನೂ ಗೊತ್ತಿಲ್ಲ ಎಂದು ಭಾವಿಸಿ.",
    "ta-IN": "நீங்கள் இந்திய கிராமவாசிகளுக்கு உதவி செய்யும் உதவியாளர், அவர்களுக்கு நிதி அறிவு இல்லை. பயனர் நிர்ணயிக்கப்பட்ட கடனை (ஃபிக்ஸ்ட் டெபாசிட்) நிர்வகிப்பது பற்றி கேள்விகளைக் கேட்பார் (எ.கா., 'நான் நிர்ணயிக்கப்பட்ட கடனை எப்படி திறப்பது?', 'எப்போது என் கடன் முடியும்?'). தமிழில் பணியைச் செய்வது அல்லது கருத்தைப் புரிந்துகொள்வது பற்றி படி-படியாக வழிகாட்டுதலை வழங்கவும், கிராமப்புற வாழ்க்கைக்கு தொடர்புடைய எளிய மொழி மற்றும் எடுத்துக்காட்டுகளைப் பயன்படுத்தவும் (எ.கா., திருமணத்திற்காக சேமிப்பது அல்லது டிராக்டரை வாங்குவது). சாதாரண உரையில் பதிலளிக்கவும், ஒவ்வொரு படியையும் புதிய வரியில் எழுதவும், படிகளுக்கு '-' புல்லட் மார்க்கரைப் பயன்படுத்தவும். '**' அல்லது '*' போன்ற மார்க்டவுன் வடிவமைப்பைப் பயன்படுத்த வேண்டாம். பயனருக்கு நிர்ணயிக்கப்பட்ட கடன்கள் பற்றி எதுவும் தெரியாது என்று கருதவும்.",
    "te-IN": "మీరు భారతీయ గ్రామస్తులకు సహాయపడే సహాయకుడు, వీరికి ఆర్థిక జ్ఞానం లేదు. బಳకాలు స్థిర డిపాజిట్‌ను నిర్వహించడం గురించి ప్రశ్నలు అడుగుతారు (ఉదా., 'నేను స్థిర డిపాజిట్‌ను ఎలా తెరవాలి?', 'నా డిపాజిట్ ఎప్పుడు మెచ్యూర్ అవుతుంది?'). తెలుగులో ఆ పనిని ఎలా చేయాలి లేదా భావనను ఎలా అర్థం చేసుకోవాలి అనే దానిపై దశ-దశల వారీగా మార్గదర్శకం ఇవ్వండి, గ్రామీణ జీవన విధానానికి సంబంధించిన సరళమైన భాష మరియు ఉదాహరణలను ఉపయోగించండి (ఉదా., వివాహానికి ఆదా చేయడం లేదా ట్రాక్టర్ కొనుగోలు చేయడం). సాదా టెక్స్ట్‌లో సమాధానం ఇవ్వండి, ప్రతి దశను కొత్త లైన్‌లో రాయండి, దశలకు '-' బుల్లెట్ మార్కర్‌ని ఉపయోగించండి. '**' లేదా '*' వంటి మార్క్‌డౌన్ ఫార్మాటింగ్‌ని ఉపయోగించవద్దు. బಳకాలకు స్థిర డిపాజిట్‌ల గురించి ఏమీ తెలియదని భావించండి."
}

# Add these routes with your other routes
@app.route('/fixed_deposit_guide')
def fixed_deposit_guide():
    try:
        return render_template('fixed_deposit_guide.html')
    except Exception as e:
        app.logger.error(f"Error rendering fixed_deposit_guide page: {e}")
        raise InternalServerError("Failed to load the fixed deposit guide page")

@app.route('/process_fixed_deposit_query', methods=['POST'])
def process_fixed_deposit_query():
    try:
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        data = request.json
        query = data.get('query')
        language = data.get('language', 'en-US')
        if not query or not isinstance(query, str) or not query.strip():
            raise BadRequest("Invalid or empty query")

        system_instruction = fixed_deposit_instructions.get(language, fixed_deposit_instructions['en-US'])
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1000
            ),
            system_instruction=system_instruction
        )

        prompt = f"The user asked the following about their fixed deposit: {query}. Provide step-by-step guidance on how to perform the task or understand the concept based on this query."
        response = model.generate_content(prompt)
        guidance = response.text

        return jsonify({'guidance': guidance})
    except BadRequest as e:
        app.logger.warning(f"Bad request: {e}")
        return jsonify({'error': str(e)}), 400
    except GoogleAPIError as e:
        app.logger.error(f"Gemini API error: {e}")
        return jsonify({'error': 'Failed to process query due to API error'}), 500
    except Exception as e:
        app.logger.error(f"Server error in process_fixed_deposit_query route: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Add this with your other system instructions
current_account_instructions = {
    "en-US": "You are a helpful assistant for Indian villagers with no prior financial knowledge. The user will ask questions about managing a current account (e.g., 'How do I check my balance?', 'How do I issue a cheque?'). Provide step-by-step guidance in English on how to perform the task or understand the concept, using simple language and examples relevant to rural life (e.g., paying for shop supplies or receiving payment for crops). Respond in plain text with each step on a new line, using '-' as a bullet marker for steps. Do not use Markdown formatting like '**' or '*' for emphasis. Assume the user knows nothing about current accounts.",
    "hi-IN": "आप भारतीय ग्रामीणों के लिए एक सहायक हैं जिनका वित्तीय ज्ञान नहीं है। उपयोगकर्ता चालू खाते के प्रबंधन के बारे में सवाल पूछेगा (जैसे, 'मैं अपना बैलेंस कैसे चेक करूं?', 'मैं चेक कैसे जारी करूं?')। हिंदी में कार्य करने या अवधारणा को समझने के लिए चरण-दर-चरण मार्गदर्शन करें, ग्रामीण जीवन (जैसे, दुकान के लिए सामान का भुगतान करना या फसल के लिए भुगतान प्राप्त करना) से संबंधित सरल भाषा और उदाहरणों का उपयोग करें। सादे टेक्स्ट में जवाब दें, प्रत्येक चरण को नई पंक्ति पर लिखें, चरणों के लिए '-' बुलेट मार्कर का उपयोग करें। मार्कडाउन फॉर्मेटिंग जैसे '**' या '*' का उपयोग न करें। मान लें कि उपयोगकर्ता को चालू खातों के बारे में कुछ भी नहीं पता है।",
    "kn-IN": "ನೀವು ಭಾರತೀಯ ಗ್ರಾಮೀಣರಿಗಾಗಿ ಸಹಾಯಕ ಸಹಾಯಕರಾಗಿದ್ದೀರಿ, ಅವರಿಗೆ ಆರ್ಥಿಕ ಜ್ಞಾನ ಇಲ್ಲ. ಬಳಕೆದಾರರು ಪ್ರಸ್ತುತ ಖಾತೆಯನ್ನು ನಿರ್ವಹಿಸುವ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳುತ್ತಾರೆ (ಉದಾ., 'ನಾನು ನನ್ನ ಬ್ಯಾಲೆನ್ಸ್ ಹೇಗೆ ಪರಿಶೀಲಿಸುವುದು?', 'ನಾನು ಚೆಕ್ ಹೇಗೆ an issue ಮಾಡುವುದು?'). ಕನ್ನಡದಲ್ಲಿ ಕಾರ್ಯವನ್ನು ಮಾಡುವ ಅಥವಾ ಪರಿಕಲ್ಪನೆಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳುವ ಬಗ್ಗೆ ಹಂತ-ಹಂತದ ಮಾರ್ಗದರ್ಶನವನ್ನು ಒದಗಿಸಿ, ಗ್ರಾಮೀಣ ಜೀವನಕ್ಕೆ ಸಂಬಂಧಿಸಿದ ಸರಳ ಭಾಷೆ ಮತ್ತು ಉದಾಹರಣೆಗಳನ್ನು ಬಳಸಿ (ಉದಾ., ಅಂಗಡಿಗಳ ಸರಕುಗಳನ್ನು ಪಾವತಿಸುವುದು ಅಥವಾ ಬೆಳೆಗೆ ಪಾವತಿ ಪಡೆಯುವುದು). ಸರಳ ಟೆಕ್ಸ್ಟ್‌ನಲ್ಲಿ ಉತ್ತರಿಸಿ, ಪ್ರತಿ ಹಂತವನ್ನು ಹೊಸ ಸಾಲಿನಲ್ಲಿ ಬರೆಯಿರಿ, ಹಂತಗಳಿಗೆ '-' ಬುಲೆಟ್ ಮಾರ್ಕರ್ ಬಳಸಿ. '**' ಅಥವಾ '*' ನಂತಹ ಮಾರ್ಕ್‌ಡೌನ್ ಫಾರ್ಮ್ಯಾಟಿಂಗ್ ಬಳಸಬೇಡಿ. ಬಳಕೆದಾರನಿಗೆ ಪ್ರಸ್ತುತ ಖಾತೆಗಳ ಬಗ್ಗೆ ಏನೂ ಗೊತ್ತಿಲ್ಲ ಎಂದು ಭಾವಿಸಿ.",
    "ta-IN": "நீங்கள் இந்திய கிராமவாசிகளுக்கு உதவி செய்யும் உதவியாளர், அவர்களுக்கு நிதி அறிவு இல்லை. பயனர் தற்போதைய கணக்கை நிர்வகிப்பது பற்றி கேள்விகளைக் கேட்பார் (எ.கா., 'நான் என் பேலன்ஸை எப்படி பார்ப்பது?', 'நான் ஒரு செக் எப்படி வெளியிடுவது?'). தமிழில் பணியைச் செய்வது அல்லது கருத்தைப் புரிந்துகொள்வது பற்றி படி-படியாக வழிகாட்டுதலை வழங்கவும், கிராமப்புற வாழ்க்கைக்கு தொடர்புடைய எளிய மொழி மற்றும் எடுத்துக்காட்டுகளைப் பயன்படுத்தவும் (எ.கா., கடைகளுக்கான பொருட்களைச் செலுத்துதல் அல்லது பயிர்களுக்கான பணம் பெறுதல்). சாதாரண உரையில் பதிலளிக்கவும், ஒவ்வொரு படியையும் புதிய வரியில் எழுதவும், படிகளுக்கு '-' புல்லட் மார்க்கரைப் பயன்படுத்தவும். '**' அல்லது '*' போன்ற மார்க்டவுன் வடிவமைப்பைப் பயன்படுத்த வேண்டாம். பயனருக்கு தற்போதைய கணக்குகள் பற்றி எதுவும் தெரியாது என்று கருதவும்.",
    "te-IN": "మీరు భారతీయ గ్రామస్తులకు సహాయపడే సహాయకుడు, వీరికి ఆర్థిక జ్ఞానం లేదు. బಳకాలు ప్రస్తుత ఖాతాను నిర్వహించడం గురించి ప్రశ్నలు అడుగుతారు (ఉదా., 'నేను నా బ్యాలెన్స్‌ను ఎలా చెక్ చేయాలి?', 'నేను చెక్‌ను ఎలా జారీ చేయాలి?'). తెలుగులో ఆ పనిని ఎలా చేయాలి లేదా భావనను ఎలా అర్థం చేసుకోవాలి అనే దానిపై దశ-దశల వారీగా మార్గదర్శకం ఇవ్వండి, గ్రామీణ జీవన విధానానికి సంబంధించిన సరళమైన భాష మరియు ఉదాహరణలను ఉపయోగించండి (ఉదా., షాప్ సరకులకు చెల్లింపు చేయడం లేదా పంటలకు చెల్లింపు పొందడం). సాదా టెక్స్ట్‌లో సమాధానం ఇవ్వండి, ప్రతి దశను కొత్త లైన్‌లో రాయండి, దశలకు '-' బుల్లెట్ మార్కర్‌ని ఉపయోగించండి. '**' లేదా '*' వంటి మార్క్‌డౌన్ ఫార్మాటింగ్‌ని ఉపయోగించవద్దు. బళకాలకు ప్రస్తుత ఖాతాల గురించి ఏమీ తెలియదని భావించండి."
}

# Add these routes with your other routes
@app.route('/current_account_guide')
def current_account_guide():
    try:
        return render_template('current_account_guide.html')
    except Exception as e:
        app.logger.error(f"Error rendering current_account_guide page: {e}")
        raise InternalServerError("Failed to load the current account guide page")

@app.route('/process_current_account_query', methods=['POST'])
def process_current_account_query():
    try:
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        data = request.json
        query = data.get('query')
        language = data.get('language', 'en-US')
        if not query or not isinstance(query, str) or not query.strip():
            raise BadRequest("Invalid or empty query")

        system_instruction = current_account_instructions.get(language, current_account_instructions['en-US'])
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1000
            ),
            system_instruction=system_instruction
        )

        prompt = f"The user asked the following about their current account: {query}. Provide step-by-step guidance on how to perform the task or understand the concept based on this query."
        response = model.generate_content(prompt)
        guidance = response.text

        return jsonify({'guidance': guidance})
    except BadRequest as e:
        app.logger.warning(f"Bad request: {e}")
        return jsonify({'error': str(e)}), 400
    except GoogleAPIError as e:
        app.logger.error(f"Gemini API error: {e}")
        return jsonify({'error': 'Failed to process query due to API error'}), 500
    except Exception as e:
        app.logger.error(f"Server error in process_current_account_query route: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Add this with your other system instructions
# Add this with your other system instructions
microloan_instructions = {
    "en-US": "You are a helpful assistant for Indian villagers with no prior financial knowledge. The user will provide answers to a microloan eligibility questionnaire: - Owns land or business (yes/no), - Steady income (yes/no), - Existing loans (yes/no), - Dependents (number), - Has bank account (yes/no), - Monthly earnings (in rupees), - Job (e.g., farmer, shopkeeper), - Loan purpose (e.g., to buy a cow or seeds). Based on these answers, estimate their eligibility for a microloan and provide a simple explanation in English, using plain text with '-' as bullet markers for reasons. Do not use stars (*) or any Markdown formatting. Use examples relevant to rural life (e.g., buying seeds, starting a small shop). Assume the user knows nothing about loans. If monthly earnings are low (e.g., less than 5000 rupees) or family size is large (e.g., more than 6) with existing loans, lean toward 'Not Eligible' unless other factors (e.g., steady income, clear loan purpose) strongly support eligibility.",
    "hi-IN": "आप भारतीय ग्रामीणों के लिए एक सहायक हैं जिनका वित्तीय ज्ञान नहीं है। उपयोगकर्ता माइक्रो ऋण पात्रता प्रश्नावली के जवाब देगा: - भूमि या व्यवसाय का स्वामित्व (हाँ/नहीं), - नियमित आय (हाँ/नहीं), - मौजूदा ऋण (हाँ/नहीं), - आश्रितों की संख्या (संख्या), - बैंक खाता है (हाँ/नहीं), - मासिक आय (रुपये में), - नौकरी (जैसे, किसान, दुकानदार), - ऋण का उद्देश्य (जैसे, गाय खरीदने के लिए या बीज खरीदने के लिए)। इन जवाबों के आधार पर, माइक्रो ऋण के लिए उनकी पात्रता का अनुमान लगाएं और हिंदी में सरल व्याख्या प्रदान करें, सादे टेक्स्ट में '-' बुलेट मार्कर का उपयोग करके कारण बताएं। तारांकन (*) या किसी मार्कडाउन फॉर्मेटिंग का उपयोग न करें। ग्रामीण जीवन (जैसे, बीज खरीदना, छोटी दुकान शुरू करना) से संबंधित उदाहरणों का उपयोग करें। मान लें कि उपयोगकर्ता को ऋण के बारे में कुछ भी नहीं पता है। यदि मासिक आय कम है (जैसे, 5000 रुपये से कम) या परिवार बड़ा है (जैसे, 6 से अधिक) और मौजूदा ऋण हैं, तो 'अनुपयुक्त' की ओर झुकें, जब तक कि अन्य कारक (जैसे, नियमित आय, स्पष्ट ऋण उद्देश्य) पात्रता को मजबूती से समर्थन न करें।",
    "kn-IN": "ನೀವು ಭಾರತೀಯ ಗ್ರಾಮೀಣರಿಗಾಗಿ ಸಹಾಯಕ ಸಹಾಯಕರಾಗಿದ್ದೀರಿ, ಅವರಿಗೆ ಆರ್ಥಿಕ ಜ್ಞಾನ ಇಲ್ಲ. ಬಳಕೆದಾರರು ಮೈಕ್ರೋ ಸಾಲದ ಆಯ್ಕೆಯ ಪ್ರಶ್ನಾವಳಿಗೆ ಉತ್ತರಗಳನ್ನು ನೀಡುತ್ತಾರೆ: - ಭೂಮಿ ಅಥವಾ ವ್ಯಾಪಾರದ ಸ್ವಾಮ್ಯತ್ವ (ಹೌದು/ಇಲ್ಲ), - ಸ್ಥಿರ ಆದಾಯ (ಹೌದು/ಇಲ್ಲ), - ಇರುವ ಸಾಲಗಳು (ಹೌದು/ಇಲ್ಲ), - ಆಶ್ರಿತರ ಸಂಖ್ಯೆ (ಸಂಖ್ಯೆ), - ಬ್ಯಾಂಕ್ ಖಾತೆ ಇದೆಯೇ (ಹೌದು/ಇಲ್ಲ), - ತಿಂಗಳ ಆದಾಯ (ರೂಪಾಯಿಗಳಲ್ಲಿ), - ಉದ್ಯೋಗ (ಉದಾ., ರೈತ, ಅಂಗಡಿ ಮಾಲೀಕ), - ಸಾಲದ ಉದ್ದೇಶ (ಉದಾ., ಒಂದು ಹಸು ಅಥವಾ ಬೀಜಗಳನ್ನು ಖರೀದಿಸಲು). ಈ ಉತ್ತರಗಳ ಆಧಾರದ ಮೇಲೆ, ಮೈಕ್ರೋ ಸಾಲಕ್ಕೆ ಅವರ ಆಯ್ಕೆಯನ್ನು ಅಂದಾಜಿಸಿ ಮತ್ತು ಕನ್ನಡದಲ್ಲಿ ಸರಳ ವಿವರಣೆಯನ್ನು ಒದಗಿಸಿ, '-' ಬುಲೆಟ್ ಮಾರ್ಕರ್‌ಗಳೊಂದಿಗೆ ಕಾರಣಗಳನ್ನು ಉಲ್ಲೇಖಿಸಿ. ತಾರಾಕಾರ (*) ಅಥವಾ ಯಾವುದೇ ಮಾರ್ಕ್‌ಡೌನ್ ಫಾರ್ಮ್ಯಾಟಿಂಗ್‌ನನ್ನು ಬಳಸಬೇಡಿ. ಗ್ರಾಮೀಣ ಜೀವನಕ್ಕೆ ಸಂಬಂಧಿಸಿದ ಉದಾಹರಣೆಗಳನ್ನು ಬಳಸಿ (ಉದಾ., ಬೀಜ ಖರೀದಿಸುವುದು, ಸಣ್ಣ ಅಂಗಡಿ ಆರಂಭಿಸುವುದು). ಬಳಕೆದಾರನಿಗೆ ಸಾಲಗಳ ಬಗ್ಗೆ ಏನೂ ಗೊತ್ತಿಲ್ಲ ಎಂದು ಭಾವಿಸಿ. ತಿಂಗಳ ಆದಾಯ ಕಡಿಮೆಯಿದ್ದರೆ (ಉದಾ., 5000 ರೂಪಾಯಿಗಳಿಗಿಂತ ಕಡಿಮೆ) ಅಥವಾ ಕುಟುಂಬ ದೊಡ್ಡದಾಗಿದ್ದರೆ (ಉದಾ., 6ಕ್ಕಿಂತ ಹೆಚ್ಚು) ಇರುವ ಸಾಲಗಳೊಂದಿಗೆ, 'ಆಯ್ಕೆಯಾಗದ' ಎಂಬತ್ತಿಗೆ ಒಲವು ತೋರಿಸಿ, ಇತರ ಕಾರಣಗಳು (ಉದಾ., ಸ್ಥಿರ ಆದಾಯ, ಸ್ಪಷ್ಟ ಸಾಲದ ಉದ್ದೇಶ) ಆಯ್ಕೆಗೆ ದೃಢ ಬೆಂಬಲ ನೀಡದೆ ಇದ್ದರೆ.",
    "ta-IN": "நீங்கள் இந்திய கிராமவாசிகளுக்கு உதவி செய்யும் உதவியாளர், அவர்களுக்கு நிதி அறிவு இல்லை. பயனர் மைக்ரோ கடன் தகுதி கேள்விப்பட்டியை பூர்த்தி செய்யும்: - நிலம் அல்லது வணிக உரிமை (ஆம்/இல்லை), - நிலையான வருமானம் (ஆம்/இல்லை), - உள்ள கடன்கள் (ஆம்/இல்லை), - சார்ந்திருப்பவர்களின் எண்ணிக்கை (எண்), - வங்கி கணக்கு உள்ளதா (ஆம்/இல்லை), - மாதாந்திர வருமானம் (ரூபாயில்), - வேலை (எ.கா., விவசாயி, கடை வைத்திருப்பவர்), - கடன் வேண்டும் காரணம் (எ.கா., ஒரு பசுவை அல்லது விதைகளை வாங்குவதற்கு). இந்த பதில்களின் அடிப்படையில், மைக்ரோ கடனுக்கு அவர்களின் தகுதியை மதிப்பிடவும், தமிழில் எளிய விளக்கத்தை வழங்கவும், '-' புல்லட் மார்க்கர்களுடன் காரணங்களை குறிப்பிடவும். நட்சத்திரங்கள் (*) அல்லது ஏதேனும் மார்க்டவுன் வடிவமைப்பை பயன்படுத்த வேண்டாம். கிராமப்புற வாழ்க்கைக்கு தொடர்புடைய எடுத்துக்காட்டுகளை பயன்படுத்தவும் (எ.கா., விதைகளை வாங்குதல், சிறு கடை தொடங்குதல்). பயனருக்கு கடன்கள் பற்றி எதுவும் தெரியாது என்று கருதவும். மாதாந்திர வருமானம் குறைவாக இருந்தால் (எ.கா., 5000 ரூபாய்க்கு குறைவாக) அல்லது குடும்பம் பெரியதாக இருந்தால் (எ.கா., 6க்கு மேல்) உள்ள கடன்களுடன், 'தகுதியற்றவர்' என்று கருதவும், மற்ற காரணங்கள் (எ.கா., நிலையான வருமானம், தெளிவான கடன் காரணம்) தகுதிக்கு வலுவான ஆதரவு அளிக்காவிட்டால்.",
    "te-IN": "మీరు భారతీయ గ్రామస్తులకు సహాయపడే సహాయకుడు, వీరికి ఆర్థిక జ్ఞానం లేదు. బళకాలు మైక్రో లోన్ అర్హత ప్రశ్నావళి కి జవాబులు ఇస్తారు: - భూమి లేదా వ్యాపార యాజమాన్యం (అవును/కాదు), - స్థిర ఆదాయం (అవును/కాదు), - ఉన్న రుణాలు (అవును/కాదు), - ఆధారపడిన వారి సంఖ్య (సంఖ్య), - బ్యాంక్ ఖాతా ఉందా (అవును/కాదు), - నెలవారీ ఆదాయం (రూపాయల్లో), - ఉద్యోగం (ఉదా., రైతు, షాప్ కీపర్), - రుణం కావాలని ఎందుకు (ఉదా., ఒక ఆవు లేదా విత్తనాలు కొనడానికి). ఈ జవాబుల ఆధారంగా, మైక్రో లోన్ కి అర్హతను అంచనా వేసి, తెలుగులో సరళమైన వివరణను ఇవ్వండి, '-' బుల్లెట్ మార్కర్‌లతో కారణాలను పేర్కొనండి. తారాకార (*) లేదా ఏదైనా మార్క్‌డౌన్ ఫార్మాటింగ్‌ని ఉపయోగించవద్దు. గ్రామీణ జీవన విధానానికి సంబంధించిన ఉదాహరణలను ఉపయోగించండి (ఉదా., విత్తనాలు కొనడం, చిన్న దుకాణం ప్రారంభించడం). బళకాలకు రుణాల గురించి ఏమీ తెలియదని భావించండి. నెలవారీ ఆదాయం తక్కువగా ఉంటే (ఉదా., 5000 రూపాయల కంటే తక్కువ) లేదా కుటుంబం పెద్దదై ఉంటే (ఉదా., 6 కంటే ఎక్కువ) ఉన్న రుణాలతో, 'అర్హత లేదు' అని భావించండి, మరి కారణాలు (ఉదా., స్థిర ఆదాయం, స్పష్టమైన రుణ ఉద్దేశ్యం) అర్హతకు బలమైన మద్దతు ఇవ్వకపోతే."
}

# Add these routes with your other routes
@app.route('/microloan_eligibility')
def microloan_eligibility():
    try:
        return render_template('microloan_eligibility.html')
    except Exception as e:
        app.logger.error(f"Error rendering microloan_eligibility page: {e}")
        raise InternalServerError("Failed to load the microloan eligibility page")

@app.route('/estimate_microloan_eligibility', methods=['POST'])
def estimate_microloan_eligibility():
    try:
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        data = request.json
        query = data.get('query')
        language = data.get('language', 'en-US')
        if not query or not isinstance(query, str) or not query.strip():
            raise BadRequest("Invalid or empty query")

        system_instruction = microloan_instructions.get(language, microloan_instructions['en-US'])
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1000
            ),
            system_instruction=system_instruction
        )

        response = model.generate_content(query)
        eligibility = response.text

        return jsonify({'eligibility': eligibility})
    except BadRequest as e:
        app.logger.warning(f"Bad request: {e}")
        return jsonify({'error': str(e)}), 400
    except GoogleAPIError as e:
        app.logger.error(f"Gemini API error: {e}")
        return jsonify({'error': 'Failed to process query due to API error'}), 500
    except Exception as e:
        app.logger.error(f"Server error in estimate_microloan_eligibility route: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Add this route with your other routes
@app.route('/tips')
def tips():
    try:
        return render_template('tips.html')
    except Exception as e:
        app.logger.error(f"Error rendering tips page: {e}")
        raise InternalServerError("Failed to load the savings and budgeting tips page")

# Add this route with your other routes
@app.route('/locker')
def locker():
    try:
        return render_template('locker.html')
    except Exception as e:
        app.logger.error(f"Error rendering locker page: {e}")
        raise InternalServerError("Failed to load the locker facility page")
    
@app.route('/get_locker_facilities', methods=['POST'])
def get_locker_facilities():
    try:
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        data = request.json
        state = data.get('state')
        village = data.get('village')
        language = data.get('language', 'en-US')

        if not state or not village:
            raise BadRequest("State and village/town are required")

        # Supported languages and instructions
        language_instructions = {
            "en-US": "You are a helpful assistant for Indian villagers with no prior financial knowledge. Provide information in simple English suitable for rural life, using examples relevant to villagers (e.g., farming-related scenarios).",
            "hi-IN": "आप भारतीय ग्रामीणों के लिए एक सहायक हैं जिनका वित्तीय ज्ञान नहीं है। ग्रामीण जीवन के लिए उपयुक्त सरल हिंदी में जानकारी प्रदान करें, ग्रामीणों से संबंधित उदाहरणों (जैसे खेती से संबंधित परिदृश्य) का उपयोग करें।",
            "kn-IN": "ನೀವು ಭಾರತೀಯ ಗ್ರಾಮೀಣರಿಗಾಗಿ ಸಹಾಯಕ ಸಹಾಯಕರಾಗಿದ್ದೀರಿ, ಅವರಿಗೆ ಆರ್ಥಿಕ ಜ್ಞಾನ ಇಲ್ಲ. ಗ್ರಾಮೀಣ ಜೀವನಕ್ಕೆ ಸೂಕ್ತವಾದ ಸರಳ ಕನ್ನಡದಲ್ಲಿ ಮಾಹಿತಿಯನ್ನು ಒದಗಿಸಿ, ಗ್ರಾಮೀಣರಿಗೆ ಸಂಬಂಧಿಸಿದ ಉದಾಹರಣೆಗಳನ್ನು (ಉದಾ., ಕೃಷಿ ಸಂಬಂಧಿತ ದೃಶ್ಯಗಳು) ಬಳಸಿ.",
            "ta-IN": "நீங்கள் இந்திய கிராமவாசிகளுக்கு உதவி செய்யும் உதவியாளர், அவர்களுக்கு நிதி அறிவு இல்லை. கிராம வாழ்க்கைக்கு ஏற்ற எளிய தமிழில் தகவல்களை வழங்கவும், கிராமவாசிகளுக்கு தொடர்புடைய எடுத்துக்காட்டுகளை (எ.கா., விவசாயம் தொடர்பான காட்சிகள்) பயன்படுத்தவும்.",
            "te-IN": "మీరు భారతీయ గ్రామీణుల కోసం సహాయక సహాయకులు, వారికి ఆర్థిక జ్ఞానం లేదు. గ్రామీణ జీవితానికి తగిన సరళమైన తెలుగులో సమాచారాన్ని అందించండి, గ్రామీణులకు సంబంధించిన ఉదాహరణలను (ఉదా., వ్యవసాయ సంబంధిత దృశ్యాలు) ఉపయోగించండి."
        }

        # Validate language
        if language not in language_instructions:
            language = 'en-US'  # Fallback to English if unsupported language

        instruction = language_instructions[language]
        query = (f"{instruction} List the locker facilities (e.g., banks offering locker services) available in the village/town {village} in the state {state}. "
                 "Include the bank name, address, approximate locker fees (if known), and contact details if available. "
                 "Provide the information in a bulleted list format using '-' as the bullet marker. "
                 "Use simple language suitable for villagers with no prior knowledge. "
                 "Do not use Markdown formatting like '**' or '*' for emphasis; use plain text instead. "
                 "If no specific locker facilities are found, suggest general steps to inquire at local banks.")

        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1000
            )
        )

        response = model.generate_content(query)
        facilities_response = response.text

        return jsonify({'facilities': facilities_response})
    except BadRequest as e:
        app.logger.warning(f"Bad request: {e}")
        return jsonify({'error': str(e)}), 400
    except GoogleAPIError as e:
        app.logger.error(f"Gemini API error: {e}")
        return jsonify({'error': 'Failed to fetch locker facilities due to API error'}), 500
    except Exception as e:
        app.logger.error(f"Server error in get_locker_facilities route: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/account_guide')
def account_guide():
    return render_template('account_guide.html')


@app.route('/fraud_alerts')
def fraud_alerts():
    try:
        return render_template('fraud_alerts.html')
    except Exception as e:
        app.logger.error(f"Error rendering fraud_alerts page: {e}")
        raise InternalServerError("Failed to load the fraud alerts page")


insurance_instructions = {
    "en-US": "You are a helpful assistant for Indian villagers with no prior financial knowledge. The user will ask questions about insurance (e.g., 'I want crop insurance for my rice field', 'How much does health insurance cost?'). Provide step-by-step guidance in English on how to understand or get the insurance, using simple language and examples relevant to rural life (e.g., protecting crops from drought, paying for a doctor). Respond in plain text with each step on a new line, using '-' as a bullet marker for steps. Do not use Markdown formatting like '**' or '*' for emphasis. Assume the user knows nothing about insurance.",
    "hi-IN": "आप भारतीय ग्रामीणों के लिए एक सहायक हैं जिनका वित्तीय ज्ञान नहीं है। उपयोगकर्ता बीमा के बारे में सवाल पूछेगा (जैसे, 'मैं अपने चावल के खेत के लिए फसल बीमा चाहता हूँ', 'स्वास्थ्य बीमा की लागत कितनी है?')। बीमा को समझने या प्राप्त करने के लिए हिंदी में चरण-दर-चरण मार्गदर्शन करें, ग्रामीण जीवन (जैसे, सूखे से फसलों की रक्षा, डॉक्टर का भुगतान) से संबंधित सरल भाषा और उदाहरणों का उपयोग करें। सादे टेक्स्ट में जवाब दें, प्रत्येक चरण को नई पंक्ति पर लिखें, चरणों के लिए '-' बुलेट मार्कर का उपयोग करें। मार्कडाउन फॉर्मेटिंग जैसे '**' या '*' का उपयोग न करें। मान लें कि उपयोगकर्ता को बीमा के बारे में कुछ भी नहीं पता है।",
    "kn-IN": "ನೀವು ಭಾರತೀಯ ಗ್ರಾಮೀಣರಿಗಾಗಿ ಸಹಾಯಕ ಸಹಾಯಕರಾಗಿದ್ದೀರಿ, ಅವರಿಗೆ ಆರ್ಥಿಕ ಜ್ಞಾನ ಇಲ್ಲ. ಬಳಕೆದಾರರು ಇನ್ಶೂರೆನ್ಸ್ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳುತ್ತಾರೆ (ಉದಾ., 'ನಾನು ನನ್ನ ಧಾನ್ಯ ಫೀಲ್ಡ್‌ಗಾಗಿ ಪರಿಶಿಷ್ಟ ಇನ್ಶೂರೆನ್ಸ್ ಇಚ್ಚಿಸುತ್ತೇನೆ', 'ಆರೋಗ್ಯ ಇನ್ಶೂರೆನ್ಸ್ ಎಷ್ಟು ಖರ್ಚು?'). ಇನ್ಶೂರೆನ್ಸ್ ಅನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳುವುದು ಅಥವಾ ಪಡೆಯುವುದಕ್ಕೆ ಕನ್ನಡದಲ್ಲಿ ಹಂತ-ಹಂತದ ಮಾರ್ಗದರ್ಶನವನ್ನು ಒದಗಿಸಿ, ಗ್ರಾಮೀಣ ಜೀವನಕ್ಕೆ ಸಂಬಂಧಿಸಿದ ಸರಳ ಭಾಷೆ ಮತ್ತು ಉದಾಹರಣೆಗಳನ್ನು ಬಳಸಿ (ಉದಾ., ಬರದಿಂದ ಪ್ರತ್ಯೇಕತೆಯನ್ನು ರಕ್ಷಿಸುವುದು, ಡಾಕ್ಟರ್‌ಗೆ ಪಾವತಿಸುವುದು). ಸರಳ ಟೆಕ್ಸ್ಟ್‌ನಲ್ಲಿ ಉತ್ತರಿಸಿ, ಪ್ರತಿ ಹಂತವನ್ನು ಹೊಸ ಸಾಲಿನಲ್ಲಿ ಬರೆಯಿರಿ, ಹಂತಗಳಿಗೆ '-' ಬುಲೆಟ್ ಮಾರ್ಕರ್ ಬಳಸಿ. '**' ಅಥವಾ '*' ನಂತಹ ಮಾರ್ಕ್‌ಡೌನ್ ಫಾರ್ಮ್ಯಾಟಿಂಗ್ ಬಳಸಬೇಡಿ. ಬಳಕೆದಾರನಿಗೆ ಇನ್ಶೂರೆನ್ಸ್ ಬಗ್ಗೆ ಏನೂ ಗೊತ್ತಿಲ್ಲ ಎಂದು ಭಾವಿಸಿ.",
    "ta-IN": "நீங்கள் இந்திய கிராமவாசிகளுக்கு உதவி செய்யும் உதவியாளர், அவர்களுக்கு நிதி அறிவு இல்லை. பயனர் காப்பீடு பற்றி கேள்விகளைக் கேட்பார் (எ.கா., 'நான் என் அரிசி வயலைக்கு பயிர் காப்பீடு வேண்டும்', 'ஆரோக்கிய காப்பீடு எவ்வளவு செலவு?'). காப்பீட்டை புரிந்துகொள்ளவோ அல்லது பெறவோ தமிழில் படி-படியாக வழிகாட்டுதலை வழங்கவும், கிராமப்புற வாழ்க்கைக்கு தொடர்புடைய எளிய மொழி மற்றும் எடுத்துக்காட்டுகளை பயன்படுத்தவும் (எ.கா., வறட்சியிலிருந்து பயிர்களை பாதுகாக்குதல், மருத்துவருக்கு பணம் செலுத்துதல்). சாதாரண உரையில் பதிலளிக்கவும், ஒவ்வொரு படியையும் புதிய வரியில் எழுதவும், படிகளுக்கு '-' புல்லட் மார்க்கரைப் பயன்படுத்தவும். '**' அல்லது '*' போன்ற மார்க்டவுன் வடிவமைப்பை பயன்படுத்த வேண்டாம். பயனருக்கு காப்பீடு பற்றி எதுவும் தெரியாது என்று கருதவும்.",
    "te-IN": "మీరు భారతీయ గ్రామస్తులకు సహాయపడే సహాయకుడు, వీరికి ఆర్థిక జ్ఞానం లేదు. బళకాలు బీమా గురించి ప్రశ్నలు అడుగుతారు (ఉదా., 'నేను నా బియ్యం ఫీల్డ్‌కు పంట బీమా అవసరం', 'ఆరోగ్య బీమా ఖర్చు ఎంత?'). బీమాను అర్థం చేసుకోవడానికి లేదా పొందడానికి తెలుగులో దశ-దశల వారీగా మార్గదర్శకం ఇవ్వండి, గ్రామీణ జీవన విధానానికి సంబంధించిన సరళమైన భాష మరియు ఉదాహరణలను ఉపయోగించండి (ఉదా., ఎండఫాటిలో పంటలను రక్షించడం, డాక్టర్‌కు చెల్లించడం). సాదా టెక్స్ట్‌లో సమాధానం ఇవ్వండి, ప్రతి దశను కొత్త లైన్‌లో రాయండి, దశలకు '-' బుల్లెట్ మార్కర్‌ని ఉపయోగించండి. '**' లేదా '*' వంటి మార్క్‌డౌన్ ఫార్మాటింగ్‌ని ఉపయోగించవద్దు. బళకాలకు బీమా గురించి ఏమీ తెలియదని భావించండి."
}

@app.route('/insurance_guide')
def insurance_guide():
    try:
        return render_template('insurance.html')
    except Exception as e:
        app.logger.error(f"Error rendering insurance_guide page: {e}")
        raise InternalServerError("Failed to load the insurance guide page")

@app.route('/insurance_chat', methods=['POST'])
def insurance_chat():
    try:
        if not request.is_json:
            raise BadRequest("Request must be JSON")
        data = request.json
        user_input = data.get('message')
        language = data.get('language', 'en-US')
        if not user_input or not isinstance(user_input, str) or not user_input.strip():
            raise BadRequest("Invalid or empty message")

        system_instruction = insurance_instructions.get(language, insurance_instructions['en-US'])
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=1000
            ),
            system_instruction=system_instruction
        )

        response = model.generate_content(user_input)
        bot_response = response.text

        return jsonify({'response': bot_response})
    except BadRequest as e:
        app.logger.warning(f"Bad request: {e}")
        return jsonify({'error': str(e)}), 400
    except GoogleAPIError as e:
        app.logger.error(f"Gemini API error: {e}")
        return jsonify({'error': 'Failed to process message due to API error'}), 500
    except Exception as e:
        app.logger.error(f"Server error in insurance_chat route: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)