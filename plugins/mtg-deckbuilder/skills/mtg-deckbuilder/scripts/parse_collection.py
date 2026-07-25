#!/usr/bin/env python3
"""Parse a card-collection CSV export into normalised collection JSON.

Auto-detects Moxfield, Archidekt, Deckbox and ManaBox layouts by header,
with a generic fallback (any CSV with a name column and optional
count/set/collector-number columns). Duplicate rows and multiple printings
of the same card are aggregated into one entry with a total owned count and
a per-printing breakdown.

Usage:
  python3 parse_collection.py "My Collection.csv" --out collection.json
"""
import argparse
import csv
import json
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

NAME_COLS = ["name", "card name", "card"]
COUNT_COLS = ["count", "quantity", "qty", "reg qty", "amount"]
SET_CODE_COLS = ["edition", "set code", "edition code", "set", "code"]
SET_NAME_COLS = ["edition name", "set name"]
CN_COLS = ["collector number", "card number", "collector_number", "number"]
FOIL_COLS = ["foil", "finish", "printing"]
PROXY_COLS = ["proxy"]

LAYOUTS = {
    "moxfield": {"count", "name", "edition", "collector number"},
    "manabox": {"name", "set code", "quantity", "collector number"},
    "archidekt": {"quantity", "name", "edition code"},
    "deckbox": {"count", "name", "edition", "card number"},
}


def pick(headers, candidates):
    for c in candidates:
        if c in headers:
            return c
    return None


def detect_layout(headers):
    hs = set(headers)
    for layout, required in LAYOUTS.items():
        if required <= hs:
            return layout
    return "generic"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path")
    ap.add_argument("--out", help="write collection JSON here (default: stdout)")
    args = ap.parse_args()

    path = Path(args.csv_path)
    if not path.exists():
        sys.exit(f"ERROR: file not found: {path}")

    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(8192)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        raw_headers = reader.fieldnames or []
        headers = {(h or "").strip().lower(): h for h in raw_headers}
        layout = detect_layout(headers)

        name_col = pick(headers, NAME_COLS)
        if not name_col:
            sys.exit(f"ERROR: no card-name column found. Headers: {raw_headers}")
        count_col = pick(headers, COUNT_COLS)
        set_col = pick(headers, SET_CODE_COLS)
        set_name_col = pick(headers, SET_NAME_COLS)
        cn_col = pick(headers, CN_COLS)
        proxy_col = pick(headers, PROXY_COLS)

        cards = OrderedDict()   # norm name -> entry
        warnings = []
        rows = 0
        for row in reader:
            get = lambda col: (row.get(headers[col]) or "").strip() if col else ""
            name = get(name_col)
            if not name:
                continue
            rows += 1
            try:
                count = int(float(get(count_col))) if get(count_col) else 1
            except ValueError:
                warnings.append(f"row {rows}: bad count {get(count_col)!r} for {name!r}; assumed 1")
                count = 1
            if count <= 0:
                continue
            if proxy_col and get(proxy_col).lower() in ("true", "1", "yes"):
                warnings.append(f"{name}: {count} proxy cop(y/ies) included — flag to the user")
            setcode = get(set_col).lower()
            # Deckbox puts full set names in 'Edition'; keep them but mark them
            if setcode and (len(setcode) > 6 or " " in setcode):
                setcode = ""
                if set_name_col is None:
                    set_name_col_val = get(set_col)
                    warnings_key = f"{name}: set given as name not code ({set_name_col_val!r})"
                    if warnings_key not in warnings:
                        warnings.append(warnings_key)
            cn = get(cn_col)

            key = " ".join(name.lower().split())
            entry = cards.setdefault(key, {
                "name": name, "count": 0, "printings": [],
            })
            entry["count"] += count
            for p in entry["printings"]:
                if p["set"] == setcode and p["collector_number"] == cn:
                    p["count"] += count
                    break
            else:
                entry["printings"].append(
                    {"set": setcode, "collector_number": cn, "count": count})

    for entry in cards.values():
        # primary printing = the one with the most owned copies
        best = max(entry["printings"], key=lambda p: p["count"])
        entry["set"] = best["set"]
        entry["collector_number"] = best["collector_number"]

    result = {
        "csv_path": str(path.resolve()),
        "source_layout": layout,
        "parsed_at": datetime.now().isoformat(timespec="seconds"),
        "distinct_cards": len(cards),
        "total_copies": sum(e["count"] for e in cards.values()),
        "warnings": warnings,
        "cards": list(cards.values()),
    }
    out = json.dumps(result, indent=1)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"Parsed {result['distinct_cards']} distinct cards "
              f"({result['total_copies']} copies) from {path.name} "
              f"[layout: {layout}] -> {args.out}")
        for w in warnings[:20]:
            print(f"  warning: {w}")
    else:
        print(out)


if __name__ == "__main__":
    main()
