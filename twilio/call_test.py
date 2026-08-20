#!/usr/bin/env python3
"""Standalone Twilio outbound voice-call test.

Places a real outbound call and reads a text-to-speech message via inline TwiML.
No web server / public URL needed. This is a self-contained diagnostic tool and
depends on nothing outside this folder.

Usage:
    python call_test.py --to "+15551234567" --message "This is a Twilio voice test."

Config (env vars, or a .env file in this folder):
    TWILIO_ACCOUNT_SID   required
    TWILIO_AUTH_TOKEN    required
    TWILIO_FROM_NUMBER   required  (a voice-capable Twilio number, e.g. +15550001111)
    TO_NUMBER            optional  (fallback for --to)
"""

from __future__ import annotations

import argparse
import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is optional; plain env vars still work.
    pass

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

DEFAULT_MESSAGE = "This is an awesome team! Best wishes."
DEFAULT_VOICE = "Polly.Joanna"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Place a test Twilio voice call.")
    parser.add_argument(
        "--to",
        default=os.getenv("TO_NUMBER"),
        help="Destination number in E.164 format, e.g. +15551234567 "
        "(falls back to TO_NUMBER env var).",
    )
    parser.add_argument(
        "--message",
        default=DEFAULT_MESSAGE,
        help="Text to speak on the call.",
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        help=f"Twilio TTS voice (default: {DEFAULT_VOICE}).",
    )
    return parser.parse_args()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"ERROR: missing required environment variable {name}", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> None:
    args = parse_args()

    account_sid = require_env("TWILIO_ACCOUNT_SID")
    auth_token = require_env("TWILIO_AUTH_TOKEN")
    from_number = require_env("TWILIO_FROM_NUMBER")

    if not args.to:
        print(
            "ERROR: no destination number. Pass --to or set TO_NUMBER.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = Client(account_sid, auth_token)

    # Fail fast on bad credentials before attempting to dial.
    try:
        account = client.api.accounts(account_sid).fetch()
        print(f"Authenticated. Account status: {account.status}")
    except TwilioRestException as exc:
        print(f"ERROR: credential check failed: {exc}", file=sys.stderr)
        sys.exit(1)

    response = VoiceResponse()
    response.say(args.message, voice=args.voice)

    try:
        call = client.calls.create(
            to=args.to,
            from_=from_number,
            twiml=str(response),
        )
    except TwilioRestException as exc:
        print(f"ERROR: call failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Call placed. SID: {call.sid}  status: {call.status}")
    print("Check Twilio Console > Monitor > Logs > Calls for delivery details.")


if __name__ == "__main__":
    main()
