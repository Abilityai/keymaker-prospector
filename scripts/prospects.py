#!/usr/bin/env python3
"""
The one way Keymaker Prospector reads and writes its list.

Backend: prospects/prospects.yaml in this repo. One row per firm, keyed on its domain.

Commands:
  python3 scripts/prospects.py list [--status qualified|unqualified|handed|in-conversation|closed|declined] [--field F]
  python3 scripts/prospects.py show <domain>
  python3 scripts/prospects.py add --domain D --name N --field F [--region R] --size TEXT --ats TEXT --hurt TEXT \
          --source URL [--source URL ...] --status qualified|unqualified [--first-line TEXT] [--note TEXT] [--confirm]
  python3 scripts/prospects.py mark <domain> --status handed|in-conversation|closed|declined [--note TEXT] [--confirm]
  python3 scripts/prospects.py draft [--date YYYY-MM-DD]        # writes drafts/prospects-<date>.md from qualified, unhanded rows
  python3 scripts/prospects.py summary

Every write prints the change it is about to make and refuses without --confirm.
Rows are never deleted. A domain is never added twice. No field may hold an email address or a phone number.
"""
import argparse
import datetime as dt
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = os.path.join(ROOT, "prospects", "prospects.yaml")
DRAFTS = os.path.join(ROOT, "drafts")

STATUSES = ["qualified", "unqualified", "handed", "in-conversation", "closed", "declined"]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+?\d[\d\s().-]{8,}\d)")


def _yaml():
    try:
        import yaml  # type: ignore
        return yaml
    except ImportError:
        sys.exit("PyYAML is not installed: pip install pyyaml")


def load():
    yaml = _yaml()
    if not os.path.exists(LIST):
        return {"prospects": []}
    with open(LIST) as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("prospects", [])
    return data


def save(data):
    yaml = _yaml()
    os.makedirs(os.path.dirname(LIST), exist_ok=True)
    with open(LIST, "w") as f:
        f.write("# File-backed prospect list (the only backend of scripts/prospects.py).\n")
        f.write("# One row per firm, keyed on domain. Rows are never deleted. No personal data - roles and URLs only.\n")
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def norm_domain(d):
    d = d.strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = re.sub(r"^www\.", "", d)
    return d.split("/")[0]


def find(data, domain):
    domain = norm_domain(domain)
    for p in data["prospects"]:
        if p["domain"] == domain:
            return p
    return None


def no_personal_data(*texts):
    for t in texts:
        if not t:
            continue
        if EMAIL.search(t):
            sys.exit(f"REFUSED: that text contains an email address - the list holds roles and URLs, never personal data: {t!r}")
        if PHONE.search(t) and not re.search(r"\d{4}-\d{2}-\d{2}", t):
            sys.exit(f"REFUSED: that text looks like it contains a phone number - the list holds roles and URLs, never personal data: {t!r}")


def change(label, before, after, confirm):
    print(f"CHANGE: {label}")
    if before is not None:
        print("  before:", before)
    print("  after: ", after)
    if not confirm:
        print("Nothing written. Re-run with --confirm to apply.")
        sys.exit(2)


def cmd_list(a):
    data = load()
    rows = data["prospects"]
    if a.status:
        rows = [p for p in rows if p["status"] == a.status]
    if a.field:
        rows = [p for p in rows if p.get("field", "").lower() == a.field.lower()]
    if not rows:
        print("(no prospects match)")
        return
    print(f"{'domain':32} {'name':28} {'field':12} {'status':16} {'handed_on':10}")
    for p in rows:
        print(f"{p['domain']:32} {p['name'][:28]:28} {p.get('field','')[:12]:12} {p['status']:16} {p.get('handed_on') or '':10}")
    print(f"{len(rows)} row(s)")


def cmd_show(a):
    p = find(load(), a.domain)
    if not p:
        sys.exit(f"no prospect with domain {norm_domain(a.domain)}")
    yaml = _yaml()
    print(yaml.safe_dump(p, sort_keys=False, allow_unicode=True))


def cmd_add(a):
    data = load()
    domain = norm_domain(a.domain)
    if find(data, domain):
        sys.exit(f"REFUSED: {domain} is already on the list (status {find(data, domain)['status']}). A firm is never added twice.")
    if a.status not in ("qualified", "unqualified"):
        sys.exit("a new row is 'qualified' or 'unqualified'; the other statuses come later with `mark`")
    no_personal_data(a.name, a.size, a.ats, a.hurt, a.first_line, a.note, *(a.source or []))
    if a.status == "qualified" and not a.first_line:
        sys.exit("a qualified firm needs --first-line")
    if not a.source:
        sys.exit("at least one --source URL is required; nothing enters the list without one")
    row = {
        "domain": domain,
        "name": a.name,
        "field": a.field,
        "region": a.region or "",
        "size_evidence": a.size,
        "ats_evidence": a.ats,
        "hurt_evidence": a.hurt,
        "sources": a.source,
        "status": a.status,
        "first_line": a.first_line or "",
        "handed_on": None,
        "added_on": dt.date.today().isoformat(),
        "notes": [a.note] if a.note else [],
    }
    change(f"add {domain} as {a.status}", None, row, a.confirm)
    data["prospects"].append(row)
    save(data)
    print(f"added {domain} ({a.status})")


def cmd_mark(a):
    data = load()
    p = find(data, a.domain)
    if not p:
        sys.exit(f"no prospect with domain {norm_domain(a.domain)}")
    if a.status not in STATUSES:
        sys.exit(f"status must be one of {STATUSES}")
    allowed = {
        "qualified": ["handed", "declined", "unqualified"],
        "handed": ["in-conversation", "declined", "unqualified"],
        "in-conversation": ["closed", "declined"],
        "unqualified": ["qualified"],
        "declined": [],
        "closed": [],
    }
    if a.status not in allowed.get(p["status"], []):
        sys.exit(f"REFUSED: {p['domain']} is {p['status']}; it may move to {allowed.get(p['status'])}, not {a.status}")
    no_personal_data(a.note)
    after = dict(p)
    after["status"] = a.status
    if a.status == "handed":
        after["handed_on"] = dt.date.today().isoformat()
    if a.note:
        after["notes"] = p.get("notes", []) + [f"{dt.date.today().isoformat()}: {a.note}"]
    change(f"mark {p['domain']} {p['status']} -> {a.status}", {"status": p["status"]}, {"status": a.status, "handed_on": after.get("handed_on")}, a.confirm)
    p.update(after)
    save(data)
    print(f"{p['domain']} is now {a.status}")


def cmd_draft(a):
    data = load()
    date = a.date or dt.date.today().isoformat()
    rows = [p for p in data["prospects"] if p["status"] == "qualified"]
    if not rows:
        print("no qualified, unhanded firms - nothing to draft")
        return
    os.makedirs(DRAFTS, exist_ok=True)
    path = os.path.join(DRAFTS, f"prospects-{date}.md")
    lines = [f"# Prospects - {date}", "", f"{len(rows)} firm(s) that fit who-we-serve, each with sources and a drafted first line.",
             "Nothing here has been sent. The rep chooses who to contact and sends from their own mailbox.", ""]
    for p in rows:
        lines += [f"## {p['name']} ({p['domain']})", "",
                  f"- Field: {p.get('field','')}  ·  Region: {p.get('region','') or 'n/a'}",
                  f"- Size: {p['size_evidence']}",
                  f"- ATS / job board: {p['ats_evidence']}",
                  f"- The hurt: {p['hurt_evidence']}",
                  "- Sources: " + ", ".join(p["sources"]), "",
                  "**First line (yours to send):**", "", f"> {p['first_line']}", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {os.path.relpath(path, ROOT)} with {len(rows)} firm(s). Now `mark <domain> --status handed --confirm` for each.")


def cmd_summary(a):
    data = load()
    rows = data["prospects"]
    today = dt.date.today()
    week = (today - dt.timedelta(days=7)).isoformat()
    by = {s: sum(1 for p in rows if p["status"] == s) for s in STATUSES}
    found_week = sum(1 for p in rows if (p.get("added_on") or "") >= week)
    qualified_week = sum(1 for p in rows if (p.get("added_on") or "") >= week and p["status"] != "unqualified")
    handed_week = sum(1 for p in rows if (p.get("handed_on") or "") >= week)
    print(f"total rows: {len(rows)}")
    for s in STATUSES:
        print(f"  {s:16} {by[s]}")
    print(f"prospects_found_week={found_week} prospects_qualified_week={qualified_week} prospects_handed_week={handed_week} prospects_in_conversation={by['in-conversation']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("list"); s.add_argument("--status"); s.add_argument("--field"); s.set_defaults(fn=cmd_list)
    s = sub.add_parser("show"); s.add_argument("domain"); s.set_defaults(fn=cmd_show)
    s = sub.add_parser("add")
    for opt in ("--domain", "--name", "--field", "--size", "--ats", "--hurt", "--status"):
        s.add_argument(opt, required=True)
    s.add_argument("--region"); s.add_argument("--source", action="append"); s.add_argument("--first-line"); s.add_argument("--note"); s.add_argument("--confirm", action="store_true")
    s.set_defaults(fn=cmd_add)
    s = sub.add_parser("mark"); s.add_argument("domain"); s.add_argument("--status", required=True); s.add_argument("--note"); s.add_argument("--confirm", action="store_true"); s.set_defaults(fn=cmd_mark)
    s = sub.add_parser("draft"); s.add_argument("--date"); s.set_defaults(fn=cmd_draft)
    s = sub.add_parser("summary"); s.set_defaults(fn=cmd_summary)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
