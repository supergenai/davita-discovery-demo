# Twilio Voice Call Test

Standalone script that places an outbound call and reads a text-to-speech message.
Self-contained, no dependency on any other project.

## Setup

```bash
cd /Users/arsalan/davita-discovery-demo/twilio
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your Twilio credentials
```

## Run

```bash
python call_test.py --to "+15551234567" --message "This is a Twilio voice test."
```

Options:
- `--to`      destination number (E.164). Falls back to `TO_NUMBER` in `.env`.
- `--message` text to speak (default: canned test sentence).
- `--voice`   Twilio TTS voice (default: `Polly.Joanna`).

## Notes
- `TWILIO_FROM_NUMBER` must be a voice-capable Twilio number.
- On a trial account the destination must be a verified number, and the destination
  country must be enabled under Voice geo permissions. Trial calls are prefixed with
  a Twilio trial notice.
- Confirm results in Twilio Console > Monitor > Logs > Calls.
