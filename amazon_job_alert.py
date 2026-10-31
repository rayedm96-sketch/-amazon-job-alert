#!/usr/bin/env python3
import json
import os
import time
import urllib.parse
import urllib.request

LOCATION = "Richmond, Texas, USA"
KEYWORD = ""
RADIUS = "15km"
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "change-me-to-a-random-string")
LOOP_SECONDS = int(os.environ.get("LOOP_SECONDS", "0"))
INTERVAL = int(os.environ.get("INTERVAL", "30"))
SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seen_jobs.json")

SEARCH_URL = "https://www.amazon.jobs/en/search.json"


def fetch_jobs():
    params = {
        "base_query": KEYWORD,
        "loc_query": LOCATION,
        "radius": RADIUS,
        "sort": "recent",
        "result_limit": 50,
        "offset": 0,
    }
    url = SEARCH_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r).get("jobs", [])


def is_richmond_tx(job):
    text = " ".join(
        str(job.get(k, "")) for k in ("location", "normalized_location", "city", "state")
    ).lower()
    return "richmond" in text and ("tx" in text or "texas" in text)


def notify(job):
    link = "https://www.amazon.jobs" + job.get("job_path", "")
    title = job.get("title", "New Amazon job")
    body = f"{job.get('location', '')}\nPosted: {job.get('posted_date', '')}"
    req = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=body.encode("utf-8"),
        headers={"Title": title, "Click": link, "Priority": "high"},
    )
    urllib.request.urlopen(req, timeout=20)


def save(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f)


def main():
    first_run = not os.path.exists(SEEN_FILE)
    seen = set()
    if not first_run:
        with open(SEEN_FILE) as f:
            seen = set(json.load(f))

    start = time.time()
    while True:
        try:
            jobs = [j for j in fetch_jobs() if is_richmond_tx(j)]
            print(f"Found {len(jobs)} Richmond, TX listings.")
            for job in jobs:
                jid = job.get("id_icims") or job.get("job_path")
                if jid in seen:
                    continue
                if not first_run:
                    notify(job)
                    print("Alerted:", job.get("title"))
                seen.add(jid)
            save(seen)
            first_run = False
        except Exception as e:
            print("Check failed:", e)

        if time.time() - start + INTERVAL >= LOOP_SECONDS:
            break
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
