#!/usr/bin/env python3
"""
Amazon job alert: checks amazon.jobs for new postings and pushes them to your phone.

Setup:
  1. Install the free ntfy app (iOS/Android) and subscribe to a random topic name.
  2. Set NTFY_TOPIC below (or as an environment variable) to that same topic.
  3. Run once to seed (no alerts), then schedule it every 5-10 minutes:
       cron:  */5 * * * * /usr/bin/python3 /path/to/amazon_job_alert.py
"""
import json
import os
import urllib.parse
import urllib.request

LOCATION = "Houston, Texas, USA"   # change to your area
KEYWORD = ""                       # e.g. "marketing", "SEO"; empty = all roles
RADIUS = "40km"
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "change-me-to-a-random-string")
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


def main():
    first_run = not os.path.exists(SEEN_FILE)
    seen = set()
    if not first_run:
        with open(SEEN_FILE) as f:
            seen = set(json.load(f))

    jobs = fetch_jobs()
    for job in jobs:
        jid = job.get("id_icims") or job.get("job_path")
        if jid in seen:
            continue
        seen.add(jid)
        if not first_run:
            notify(job)
            print("Alerted:", job.get("title"))

    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f)
    if first_run:
        print(f"Seeded with {len(jobs)} current listings. Future runs will alert on new ones.")


if __name__ == "__main__":
    main()
