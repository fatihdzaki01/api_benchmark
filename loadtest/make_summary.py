import csv
import html
import os
import re
import sys

PERCENTILES = ["50%", "66%", "75%", "80%", "90%", "95%", "98%", "99%", "99.9%", "99.99%", "100%"]
DISPLAY_PERCENTILES = ["50%", "75%", "90%", "95%", "99%", "100%"]


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def load_aggregated(path):
    if not os.path.exists(path):
        return None
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Name") or "").strip()
            if name == "" or name.lower() == "aggregated":
                return row
    return None


def row_stats(row):
    if row is None:
        return None
    requests = _int(row.get("Request Count"))
    failures = _int(row.get("Failure Count"))
    error_pct = (failures / requests * 100.0) if requests else 100.0
    percentiles_s = {
        p: _num(row.get(p, 0)) / 1000.0 for p in PERCENTILES
    }
    return {
        "requests": requests,
        "failures": failures,
        "rps": _num(row.get("Requests/s")),
        "error_pct": error_pct,
        "p_s": percentiles_s,
    }


def read_thresholds():
    max_err = float(os.environ.get("LOCUST_MAX_ERROR_PCT", "10"))
    max_p99_s = float(os.environ.get("LOCUST_MAX_P99_S", "60"))
    return max_err, max_p99_s


def cmd_check(path):
    max_err, max_p99_s = read_thresholds()
    st = row_stats(load_aggregated(path))
    if st is None:
        print("NO DATA - skip deteksi batas")
        sys.exit(0)
    over_err = st["error_pct"] > max_err
    over_p99 = st["p_s"]["99%"] > max_p99_s
    print(
        "aggregated: req=%d rps=%.2f error=%.2f%% p99=%.3fs "
        "(limit error>%s%% | p99>%ss)"
        % (st["requests"], st["rps"], st["error_pct"], st["p_s"]["99%"], max_err, max_p99_s)
    )
    sys.exit(1 if (over_err or over_p99) else 0)


def users_from_path(path):
    m = re.search(r"_(\d+)_users_stats\.csv$", path)
    return int(m.group(1)) if m else 0


def fmt_seconds(value):
    return f"{value:.3f}"


def cmd_build(results_dir, prefix, paths):
    max_err, max_p99_s = read_thresholds()
    rows = []
    for p in paths:
        st = row_stats(load_aggregated(p))
        if st is None:
            continue
        users = users_from_path(p)
        over = st["error_pct"] > max_err or st["p_s"]["99%"] > max_p99_s
        rows.append(
            {
                "users": users,
                "rps": st["rps"],
                "error_pct": st["error_pct"],
                "p_s": st["p_s"],
                "over": over,
                "link": f"{prefix}_{users}_users.html",
            }
        )
    rows.sort(key=lambda r: r["users"])

    print(f"{'users':>7} {'rps':>10} {'err%':>8} " + " ".join(f"{p:>10}" for p in DISPLAY_PERCENTILES))
    for r in rows:
        print(
            f"{r['users']:>7} {r['rps']:>10.2f} {r['error_pct']:>8.2f} "
            + " ".join(f"{fmt_seconds(r['p_s'][p]):>10}" for p in DISPLAY_PERCENTILES)
            + ("   <<< BATAS" if r["over"] else "")
        )

    out = os.path.join(results_dir, f"{prefix}_ringkasan_seconds.html")
    thead = "".join(f"<th>{html.escape(p)}</th>" for p in DISPLAY_PERCENTILES)
    tbody = []
    for r in rows:
        cls = ' class="limit"' if r["over"] else ""
        cells = "".join(
            f"<td>{fmt_seconds(r['p_s'][p])}</td>" for p in DISPLAY_PERCENTILES
        )
        mark = "BATAS" if r["over"] else "OK"
        tbody.append(
            "<tr%s><td>%d</td><td>%.2f</td><td>%.2f%%</td>%s"
            "<td>%s</td><td><a href='%s'>HTML</a></td></tr>"
            % (cls, r["users"], r["rps"], r["error_pct"], cells, mark, html.escape(r["link"]))
        )

    page = f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<title>Ringkasan Benchmark {prefix} (satuan second)</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 24px; }}
  table {{ border-collapse: collapse; margin-top: 16px; }}
  th, td {{ border: 1px solid #bbb; padding: 6px 10px; text-align: right; }}
  th {{ background: #eef; }}
  tr.limit {{ background: #ffe1e1; font-weight: bold; }}
  .note {{ color: #555; font-size: 13px; }}
</style>
</head>
<body>
<h1>Ringkasan Benchmark <code>{html.escape(prefix)}</code></h1>
<p>Semua latensi dalam <strong>detik (s)</strong>. Ambang batas: error &gt; {max_err}% ATAU p99 &gt; {max_p99_s}s.</p>
<table>
<thead><tr><th>Users</th><th>RPS</th><th>Error %</th>{thead}<th>Status</th><th>Laporan</th></tr></thead>
<tbody>
{''.join(tbody)}
</tbody>
</table>
<p class="note">Cara baca: cari baris pertama berstatus BATAS. User count terakhir yang masih OK = batas kemampuan sistem (sebelum error naik / latency p99 membengkak).</p>
</body>
</html>
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"\nRingkasan tersimpan: {out}")


def main():
    if len(sys.argv) < 2:
        print("usage: make_summary.py check <stats.csv> | build <outdir> <prefix> <stats.csv...>")
        sys.exit(2)
    cmd = sys.argv[1]
    if cmd == "check":
        cmd_check(sys.argv[2])
    elif cmd == "build":
        cmd_build(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        print(f"perintah tidak dikenal: {cmd}")
        sys.exit(2)


if __name__ == "__main__":
    main()
