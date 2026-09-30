"""Tiny dependency-light load tester for ComicCraft (uses only httpx + threads).

Examples
  COMICCRAFT_MOCK=1 uvicorn app.main:app &                      # mock AI: measures app overhead only
  python scripts/load_test.py --path / --users 10 --duration 10
  python scripts/load_test.py --path /generate-comic/json --method POST --users 5 --duration 15
Run the server WITHOUT COMICCRAFT_MOCK to measure real Gemini + Stable Diffusion latency.
"""
import argparse
import json
import statistics
import threading
import time

import httpx

PAYLOAD = {"story_prompt": "A brave fox exploring an enchanted forest", "character_name": "Rusty",
           "setting": "forest", "tone": "dramatic", "art_style": "anime"}


def worker(args, stop_at, results):
    with httpx.Client(base_url=args.base_url, timeout=args.timeout) as client:
        while time.time() < stop_at:
            t0 = time.perf_counter()
            try:
                if args.method == "POST" and args.path.endswith("/json"):
                    r = client.post(args.path, json=PAYLOAD)
                elif args.method == "POST":
                    r = client.post(args.path, data=PAYLOAD)
                else:
                    r = client.get(args.path)
                ok = r.status_code == 200
            except Exception:
                ok = False
            results.append((time.perf_counter() - t0, ok))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--path", default="/")
    ap.add_argument("--method", default="GET", choices=["GET", "POST"])
    ap.add_argument("--users", type=int, default=10)
    ap.add_argument("--duration", type=int, default=10)
    ap.add_argument("--timeout", type=float, default=300)
    args = ap.parse_args()

    results: list = []
    start = time.time()
    stop_at = start + args.duration
    threads = [threading.Thread(target=worker, args=(args, stop_at, results)) for _ in range(args.users)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    elapsed = time.time() - start

    times = sorted(t for t, ok in results if ok)
    total, fails = len(results), sum(1 for _, ok in results if not ok)
    out = {
        "path": args.path, "method": args.method, "users": args.users, "duration_s": round(elapsed, 1),
        "requests": total, "errors": fails, "error_rate_pct": round(100 * fails / total, 2) if total else None,
        "avg_s": round(statistics.mean(times), 4) if times else None,
        "p95_s": round(times[int(0.95 * (len(times) - 1))], 4) if times else None,
        "max_s": round(times[-1], 4) if times else None,
        "throughput_rps": round(total / elapsed, 1),
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
