
import os
import json
from http.server import BaseHTTPRequestHandler
from google import genai

SYSTEM_INSTRUCTION = """
أنت ميزان AI، مساعد ذكي لتحليل المواقف اليومية والمهنية
وفق الأخلاق والقيم الإسلامية.

حلل كل موقف باستخدام المحاور التالية:

1. فهم وتحليل الموقف.
2. الخلق الإسلامي المرتبط بالموقف.
3. التوجيه الأخلاقي.
4. الدليل الشرعي: اذكر آية أو حديثًا فقط إذا كنت واثقًا من صحته
   ومن مصدره، ولا تخترع أدلة أو تنسب أقوالًا للدين دون تحقق.
5. الحل والتصرف الصحيح المقترح.

استخدم لغة عربية واضحة وبسيطة.
لا تصدر فتاوى شرعية، ونبه المستخدم إلى استشارة أهل العلم
في المسائل الشرعية المتخصصة.
إذا لم يتوفر دليل موثوق، صرح بذلك بوضوح.
"""

class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            api_key = os.environ.get("GEMINI_API_KEY")

            if not api_key:
                raise Exception("Gemini API key is not configured.")

            length = int(self.headers.get("Content-Length", 0))

            if length > 10000:
                self.send_error(413, "Request too large")
                return

            body = json.loads(self.rfile.read(length))
            situation = body.get("situation", "").strip()

            if not situation:
                self.send_json(400, {"error": "من فضلك اكتبي الموقف أولاً."})
                return

            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=situation,
                config={
                    "system_instruction": SYSTEM_INSTRUCTION,
                    "temperature": 0.4,
                }
            )

            self.send_json(200, {"result": response.text})

        except Exception as e:
            print("API Error:", str(e))
            self.send_json(
                500,
                {"error": "حصل خطأ أثناء تحليل الموقف. حاولي مرة أخرى."}
            )

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, status, data):
        response = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_cors_headers()
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

