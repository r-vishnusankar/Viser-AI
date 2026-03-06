#!/usr/bin/env python3
"""
Check if OpenAI API key has quota available.
Run: python check_openai_quota.py
"""
import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

# Load .env from project root
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16")


def check_quota():
    if not API_KEY or API_KEY == "your_openai_api_key_here":
        print("[X] OPENAI_API_KEY not found in .env")
        print("    Add your key to .env: OPENAI_API_KEY=sk-proj-...")
        return False

    masked = f"...{API_KEY[-4:]}" if len(API_KEY) > 4 else "****"
    print(f"[Key] {masked}")
    print(f"[Model] {MODEL}")
    print("Testing API call...")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=API_KEY)
        # o4-mini uses max_completion_tokens; older models use max_tokens
        kwargs = {"model": MODEL, "messages": [{"role": "user", "content": "Say OK"}]}
        if "o4" in MODEL.lower() or "o1" in MODEL.lower():
            kwargs["max_completion_tokens"] = 5
        else:
            kwargs["max_tokens"] = 5

        resp = client.chat.completions.create(**kwargs)
        reply = resp.choices[0].message.content.strip()
        print(f"[OK] Quota available - API responded: {reply}")
        return True
    except Exception as e:
        err = str(e)
        if "429" in err or "insufficient_quota" in err.lower():
            print("[X] No quota - 429 insufficient_quota")
            print("    Add billing at https://platform.openai.com/account/billing")
        elif "401" in err or "invalid_api_key" in err.lower():
            print("[X] Invalid API key")
            print("    Check your key at https://platform.openai.com/api-keys")
        elif "max_completion_tokens" in err or "max_tokens" in err:
            print(f"[~] Model '{MODEL}' needs different params. Trying gpt-4o-mini...")
            try:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Say OK"}],
                    max_tokens=5,
                )
                reply = resp.choices[0].message.content.strip()
                print(f"[OK] Quota available - gpt-4o-mini works: {reply}")
                return True
            except Exception as e2:
                err2 = str(e2)
                if "429" in err2 or "insufficient_quota" in err2.lower():
                    print("[X] No quota - 429 insufficient_quota")
                else:
                    print(f"[X] gpt-4o-mini failed: {err2[:150]}")
        elif "404" in err or "model" in err.lower() or "does not exist" in err.lower():
            print(f"[X] Model '{MODEL}' not found or not accessible")
            print("    Try OPENAI_MODEL=gpt-4o-mini in .env")
        else:
            print(f"[X] Error: {e}")
        return False


if __name__ == "__main__":
    ok = check_quota()
    sys.exit(0 if ok else 1)
