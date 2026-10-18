import json
import time
from pathlib import Path
from collections import defaultdict
from app.agents.classifier import classify

BASE = Path(__file__).resolve().parent
TICKETS = json.loads((BASE / "test_tickets.json").read_text(encoding="utf-8"))
CACHE_FILE = BASE / "classifier_cache.json"
cache = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}

def save():
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")

# 1. Classify anything not cached yet (stops cleanly on quota errors)
for t in TICKETS:
    if t["message"] in cache:
        continue
    try:
        r = classify(t["message"])
    except Exception as e:
        print("Stopped (quota or error):", str(e)[:150])
        break
    cache[t["message"]] = r.model_dump()
    save()
    print("classified:", t["message"][:50])
    time.sleep(13)

# 2. Score the tickets that have results
fields = ["language", "intent", "order_id", "angry"]
hits = defaultdict(int)
by_lang = defaultdict(lambda: [0, 0])
done = 0
print("\nMISMATCHES")
for t in TICKETS:
    got = cache.get(t["message"])
    if not got:
        continue
    done += 1
    all_ok = True
    for f in fields:
        ok = got[f] == t[f]
        hits[f] += ok
        if not ok:
            all_ok = False
            print(f"  [{f}] {t['message'][:45]!r}: expected {t[f]!r}, got {got[f]!r}")
    by_lang[t["language"]][0] += all_ok
    by_lang[t["language"]][1] += 1

print(f"\nEvaluated {done}/{len(TICKETS)} tickets")
for f in fields:
    if done:
        print(f"  {f}: {hits[f]}/{done} ({100 * hits[f] / done:.0f}%)")
for lang, (ok, n) in by_lang.items():
    print(f"  all fields correct, {lang}: {ok}/{n}")