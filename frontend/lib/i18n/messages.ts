import { LanguageCode } from "@/lib/api";

const MESSAGES: Record<LanguageCode, Record<string, string>> = {
  en: {
    slow_internet: "Internet is slow. Please type your message or try again.",
    network_failure: "Network failed. Please speak again or type your message.",
    type_fallback: "You can type your message here.",
    recording: "Recording..."
  },
  hi: {
    slow_internet: "इंटरनेट धीमा है। कृपया लिखें या फिर कोशिश करें।",
    network_failure: "नेटवर्क विफल हुआ। कृपया फिर बोलें या लिखें।",
    type_fallback: "आप अपना संदेश लिख सकते हैं।",
    recording: "रिकॉर्डिंग..."
  },
  bn: {
    slow_internet: "ইন্টারনেট ধীর। লিখুন বা আবার চেষ্টা করুন।",
    network_failure: "নেটওয়ার্ক ব্যর্থ হয়েছে। আবার বলুন বা লিখুন।",
    type_fallback: "আপনি বার্তা লিখতে পারেন।",
    recording: "রেকর্ড হচ্ছে..."
  },
  te: { slow_internet: "ఇంటర్నెట్ నెమ్మదిగా ఉంది. టైప్ చేయండి లేదా మళ్లీ ప్రయత్నించండి.", network_failure: "నెట్‌వర్క్ విఫలమైంది. మళ్లీ చెప్పండి లేదా టైప్ చేయండి.", type_fallback: "మీ సందేశాన్ని టైప్ చేయవచ్చు.", recording: "రికార్డింగ్..." },
  mr: { slow_internet: "इंटरनेट धीमे आहे. लिहा किंवा पुन्हा प्रयत्न करा.", network_failure: "नेटवर्क अयशस्वी झाले. पुन्हा बोला किंवा लिहा.", type_fallback: "तुम्ही संदेश लिहू शकता.", recording: "रेकॉर्डिंग..." },
  ta: { slow_internet: "இணையம் மெதுவாக உள்ளது. தட்டச்சு செய்யுங்கள் அல்லது மீண்டும் முயற்சிக்கவும்.", network_failure: "நெட்வொர்க் தோல்வியடைந்தது. மீண்டும் பேசுங்கள் அல்லது தட்டச்சு செய்யுங்கள்.", type_fallback: "உங்கள் செய்தியை தட்டச்சு செய்யலாம்.", recording: "பதிவு செய்கிறது..." },
  gu: { slow_internet: "ઇન્ટરનેટ ધીમું છે. લખો અથવા ફરી પ્રયત્ન કરો.", network_failure: "નેટવર્ક નિષ્ફળ થયું. ફરી બોલો અથવા લખો.", type_fallback: "તમે તમારો સંદેશ લખી શકો છો.", recording: "રેકોર્ડિંગ..." },
  kn: { slow_internet: "ಇಂಟರ್ನೆಟ್ ನಿಧಾನವಾಗಿದೆ. ಟೈಪ್ ಮಾಡಿ ಅಥವಾ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.", network_failure: "ನೆಟ್‌ವರ್ಕ್ ವಿಫಲವಾಗಿದೆ. ಮತ್ತೆ ಹೇಳಿ ಅಥವಾ ಟೈಪ್ ಮಾಡಿ.", type_fallback: "ನಿಮ್ಮ ಸಂದೇಶವನ್ನು ಟೈಪ್ ಮಾಡಬಹುದು.", recording: "ರೆಕಾರ್ಡಿಂಗ್..." },
  ml: { slow_internet: "ഇന്റർനെറ്റ് മന്ദമാണ്. ടൈപ്പ് ചെയ്യുക അല്ലെങ്കിൽ വീണ്ടും ശ്രമിക്കുക.", network_failure: "നെറ്റ്‌വർക്ക് പരാജയപ്പെട്ടു. വീണ്ടും പറയുക അല്ലെങ്കിൽ ടൈപ്പ് ചെയ്യുക.", type_fallback: "നിങ്ങളുടെ സന്ദേശം ടൈപ്പ് ചെയ്യാം.", recording: "റെക്കോർഡിംഗ്..." },
  pa: { slow_internet: "ਇੰਟਰਨੈੱਟ ਹੌਲੀ ਹੈ। ਲਿਖੋ ਜਾਂ ਮੁੜ ਕੋਸ਼ਿਸ਼ ਕਰੋ।", network_failure: "ਨੈੱਟਵਰਕ ਫੇਲ੍ਹ ਹੋ ਗਿਆ। ਮੁੜ ਬੋਲੋ ਜਾਂ ਲਿਖੋ।", type_fallback: "ਤੁਸੀਂ ਆਪਣਾ ਸੁਨੇਹਾ ਲਿਖ ਸਕਦੇ ਹੋ।", recording: "ਰਿਕਾਰਡਿੰਗ..." },
  or: { slow_internet: "ଇଣ୍ଟରନେଟ ଧୀର। ଲେଖନ୍ତୁ କିମ୍ବା ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ।", network_failure: "ନେଟୱର୍କ ବିଫଳ। ପୁଣି କହନ୍ତୁ କିମ୍ବା ଲେଖନ୍ତୁ।", type_fallback: "ଆପଣ ନିଜ ସନ୍ଦେଶ ଲେଖିପାରିବେ।", recording: "ରେକର୍ଡିଂ..." }
};

export function voiceMessage(languageCode: LanguageCode, key: string) {
  return MESSAGES[languageCode]?.[key] ?? MESSAGES.en[key] ?? "";
}
