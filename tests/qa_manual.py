"""
Phase 5 Manual QA Script — 5+ diverse API queries.
Validates acceptance criteria across different locations, budgets, cuisines, and edge inputs.
"""
import json
import sys
import time
try:
    import httpx
except ImportError:
    import urllib.request
    httpx = None

BASE = "http://localhost:8000"

def post_json(path, data):
    if httpx:
        r = httpx.post(f"{BASE}{path}", json=data, timeout=15)
        return r.status_code, r.json()
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

def get_json(path):
    if httpx:
        r = httpx.get(f"{BASE}{path}", timeout=10)
        return r.status_code, r.json()
    req = urllib.request.Request(f"{BASE}{path}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, json.loads(resp.read())

results = []

def qa(name, method, path, payload=None, expect_status=200, checks=None):
    try:
        t0 = time.perf_counter()
        if method == "GET":
            status, data = get_json(path)
        else:
            status, data = post_json(path, payload)
        elapsed = (time.perf_counter() - t0) * 1000

        ok = status == expect_status
        detail = ""
        if checks and ok:
            for check_name, check_fn in checks.items():
                try:
                    assert check_fn(data), f"Check '{check_name}' failed"
                except AssertionError as e:
                    ok = False
                    detail += f" FAIL:{check_name}"

        tag = "PASS" if ok else "FAIL"
        print(f"[{tag}] {name} (HTTP {status}, {elapsed:.0f}ms){detail}")
        if not ok:
            print(f"       Response: {json.dumps(data, ensure_ascii=False)[:200]}")
        results.append(ok)
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        results.append(False)

# ── QA Test Cases ───────────────────────────────────────────────

print("=" * 70)
print("Phase 5 Manual QA — API Endpoint Validation")
print("=" * 70)

# 1. Health check
qa("Health check", "GET", "/health", checks={
    "status_ok": lambda d: d["status"] == "ok",
    "dataset_loaded": lambda d: d["dataset_loaded"] is True,
    "count_gt_0": lambda d: d["restaurant_count"] > 50000,
})

# 2. Bangalore + medium + Italian + 4.0
qa("Bangalore medium Italian 4.0", "POST", "/recommendations",
   {"location": "Bangalore", "budget": "medium", "cuisine": "Italian", "min_rating": 4.0},
   checks={
       "has_recs": lambda d: len(d["recommendations"]) > 0,
       "rank_1": lambda d: d["recommendations"][0]["rank"] == 1,
       "has_summary": lambda d: bool(d["summary"]),
       "total_gt_0": lambda d: d["total_candidates"] > 0,
   })

# 3. Koramangala + low + no cuisine + 0.0
qa("Koramangala low Any 0.0", "POST", "/recommendations",
   {"location": "Koramangala", "budget": "low", "min_rating": 0.0},
   checks={
       "has_recs": lambda d: len(d["recommendations"]) > 0,
       "all_fields": lambda d: all(
           r.get("restaurant_name") and r.get("explanation") for r in d["recommendations"]
       ),
   })

# 4. Indiranagar + high + Chinese + 4.5
qa("Indiranagar high Chinese 4.5", "POST", "/recommendations",
   {"location": "Indiranagar", "budget": "high", "cuisine": "Chinese", "min_rating": 4.5},
   checks={
       "has_recs": lambda d: len(d["recommendations"]) > 0,
   })

# 5. Impossible combo → expect relaxation
qa("Impossible combo (relaxation)", "POST", "/recommendations",
   {"location": "Bangalore", "budget": "high", "cuisine": "Ethiopian", "min_rating": 4.9},
   checks={
       "has_recs": lambda d: len(d["recommendations"]) > 0,
       "relaxed": lambda d: d["filters_relaxed"] is not None and len(d["filters_relaxed"]) > 0,
   })

# 6. Unknown location → empty results
qa("Unknown location empty results", "POST", "/recommendations",
   {"location": "Zyxwvutsrqp", "budget": "medium"},
   checks={
       "zero_recs": lambda d: len(d["recommendations"]) == 0,
       "helpful_msg": lambda d: "No restaurants found" in (d.get("summary") or ""),
   })

# 7. Invalid budget → 422
qa("Invalid budget 422", "POST", "/recommendations",
   {"location": "Bangalore", "budget": "ultra"},
   expect_status=422)

# 8. Missing location → 422
qa("Missing location 422", "POST", "/recommendations",
   {"budget": "medium"},
   expect_status=422)

# 9. Rating out of range → 422
qa("Rating > 5 returns 422", "POST", "/recommendations",
   {"location": "Bangalore", "budget": "medium", "min_rating": 6.0},
   expect_status=422)

# 10. Long additional_preferences
qa("Long additional prefs", "POST", "/recommendations",
   {"location": "Bangalore", "budget": "low", "additional_preferences": "x" * 300},
   checks={
       "has_recs": lambda d: len(d["recommendations"]) > 0,
   })

# 11. Metadata endpoints
qa("Cities metadata", "GET", "/metadata/cities", checks={
    "count_gt_50": lambda d: d["count"] > 50,
    "sorted": lambda d: d["items"] == sorted(d["items"]),
})

qa("Cuisines metadata", "GET", "/metadata/cuisines", checks={
    "count_gt_50": lambda d: d["count"] > 50,
})

qa("Budgets metadata", "GET", "/metadata/budgets", checks={
    "three_tiers": lambda d: d["items"] == ["low", "medium", "high"],
})

# ── Summary ─────────────────────────────────────────────────────
print("=" * 70)
passed = sum(results)
total = len(results)
print(f"QA Result: {passed}/{total} passed")
if passed < total:
    sys.exit(1)
print("All manual QA checks passed!")
