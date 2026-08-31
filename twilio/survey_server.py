from http.server import HTTPServer, BaseHTTPRequestHandler

TWIML = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna-Neural"><prosody rate="95%">Hey there, thanks for calling. I just have a few quick questions about how you've been doing with your kidney care — it'll only take a minute.</prosody></Say>
  <Pause length="1"/>
  <Say voice="Polly.Joanna-Neural"><prosody rate="95%">First question — roughly how many days a week are you going in for dialysis right now?</prosody></Say>
  <Pause length="4"/>
  <Say voice="Polly.Joanna-Neural"><prosody rate="95%">Second — have you been sticking to the low-phosphorus, low-potassium diet your dietitian recommended?</prosody></Say>
  <Pause length="4"/>
  <Say voice="Polly.Joanna-Neural"><prosody rate="95%">Third — since your last treatment, have you noticed any swelling in your legs or ankles?</prosody></Say>
  <Pause length="4"/>
  <Say voice="Polly.Joanna-Neural"><prosody rate="95%">And last one — on a scale of one to ten, how are your energy levels feeling this week compared to last week?</prosody></Say>
  <Pause length="4"/>
  <Say voice="Polly.Joanna-Neural"><prosody rate="95%">That's it! Really appreciate you taking the time. Your care team will be following up with you soon. Take care!</prosody></Say>
</Response>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._respond()
    def do_POST(self):
        self._respond()
    def _respond(self):
        body = TWIML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/xml")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, fmt, *args):
        print(f"[call] {args[0]} {args[1]}")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print(f"Survey server running on port {port}")
    HTTPServer(("", port), Handler).serve_forever()
