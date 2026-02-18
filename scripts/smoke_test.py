import requests

BACKEND = "http://127.0.0.1:8000"

def main():
    r = requests.get(f"{BACKEND}/health")
    r.raise_for_status()
    print("health:", r.json())

    # PDF parse
    with open("assets/demo.pdf", "rb") as f:
        r = requests.post(f"{BACKEND}/api/paper/parse", files={"file": f})
    r.raise_for_status()
    parsed = r.json()
    text = parsed.get("full_text", "")
    print("parse len:", len(text))
    assert len(text) > 50

    # summary
    r = requests.post(f"{BACKEND}/api/paper/summary", json={"text": text[:4000], "mode": "mvp"})
    r.raise_for_status()
    print("summary one_liner:", r.json()["one_liner"])

    # profile
    r = requests.post(f"{BACKEND}/api/write/profile", json={"text": "Our experiment shows that...", "domain": "cs"})
    r.raise_for_status()
    print("profile:", r.json()["structural"])

    # transfer
    r = requests.post(f"{BACKEND}/api/write/transfer", json={
        "text": "Our experiment shows that the model works.",
        "target_journal": "Nature",
        "formality": 0.85,
        "domain": "cs"
    })
    r.raise_for_status()
    print("transfer rewritten:", r.json()["rewritten"][:80], "...")
    print("OK ✅")

if __name__ == "__main__":
    main()