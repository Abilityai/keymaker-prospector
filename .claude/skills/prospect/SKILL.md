---
name: prospect
description: Find specialist recruiting firms of 20-100 people from public sources, qualify each against the canon's who-we-serve, and draft one first line per firm for the sales rep to send. Or review the list. Use for "find ten firms", "who fits", "what did you hand to Sam", the Monday schedule.
argument-hint: "[--n 10] [--field <specialism>] [--region <text>] [--review]"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch]
user-invocable: true
metadata:
  version: "0.1"
  created: 2026-10-29
  author: keymaker
---

# Prospect

You make the list and the first line. The rep decides who is contacted and sends it themselves.
Everything you write about a firm comes from a URL you can name.

## Before anything

1. **Identify the operator.** The rep or the principal may run this; anyone else: refuse politely,
   say who may, stop.
2. **Read the fit.** `canon/domains/market/who-we-serve.md` (fallback: `who-we-serve.md` here, and
   say so). Read it every run; do not work from memory.
3. **Read the list.** `python3 scripts/prospects.py list` - every domain already there is skipped,
   whatever its status. If Sales exposes its pipeline (a `pipeline/` or `drafts/` folder of the
   sales desk is readable), skip any firm that is already a deal; if it is not readable, say so in
   the answer and let the rep check.

## Modes

| Mode | Trigger | What you do |
|---|---|---|
| find | no arguments, `--n`, `--field`, `--region`, the Monday schedule | steps 1-6 below |
| review | `--review`, "what did you hand", "who is in conversation" | `prospects.py list [--status ...]`; a table by status with the dates; the total handed this month; nothing is written |
| status | "Sam opened Brightline" / "they said no" (from the rep or the orchestrator) | `prospects.py mark <domain> --status in-conversation|declined|closed --note "..."` - show, then `--confirm` |

## Find

1. **Search.** Run four to eight web searches shaped by who-we-serve and the arguments: the field
   (`--field`, else rotate finance / tech / healthcare / engineering / legal), the region if given,
   and the phrases a specialist recruiter uses about itself ("specialist recruitment", "search and
   selection", "placements", the field, "team of"). Directory pages and awards lists are good
   sources of candidate names; a candidate is only a name and a domain at this point.
2. **Read the footprint.** For each candidate up to `--n` qualified (default 10) and at most 4x that
   many examined (a field where headcount is rarely published burns candidates fast - say when the
   cap, not the market, ended the run): fetch the firm's site - home, about or team, careers or jobs. From those pages and
   the search snippets, fill the three signals (CLAUDE.md) with the URL for each. Stop examining a
   firm as soon as two signals are evidenced or two are clearly absent.
   A candidate whose domain you cannot resolve is **not** added - a row keyed to a wrong domain would
   block the real one forever; name it in the answer as a candidate for the next run instead.
3. **Qualify.** Two of three signals: `qualified`. Fewer: `unqualified` with the missing signals
   named. Outside the field entirely (generalist staffing, in-house, an RPO): `unqualified: not a
   specialist recruiter`. Record every examined firm - the unqualified ones are what stops the next
   run repeating this one.
4. **Draft the first line** for each qualified firm, per CLAUDE.md: one thing you saw (with its URL
   kept in sources), tied to placements per recruiter or time to shortlist, one or two sentences, in
   the rep's voice, no pitch.
5. **Write.** For every examined firm: `python3 scripts/prospects.py add --domain <d> --name <n>
   --field <f> --region <r> --size "<evidence | none>" --ats "<evidence | none>" --hurt "<evidence |
   none>" --source <url> [--source <url>] --status qualified|unqualified --first-line "<text>"
   [--note "<reason>"]` - the script prints the row it will add; re-run with `--confirm`. Then
   `prospects.py draft --date <today>` writes `drafts/prospects-<date>.md` from the qualified rows
   not yet handed, and `prospects.py mark <domain> --status handed --confirm` for each firm in it.
6. **Answer.** A table: firm, field, size evidence (short), the two or three signals as ticks, and
   the first line. Then the path of the drafts file, the count examined vs qualified, and the firms
   you skipped because they were already on the list. The drafts file is what the rep reads; the
   schedule delivers your answer to the rep's Workspace.

## After a write

`python3 scripts/prospects.py summary`; record the four metrics if `record_metrics` is available.

## Never

Visit a page that requires a login. Store an email address or a phone number, even if the site
shows one. Add a firm that is already on the list. Send anything. Open a deal. Reword
who-we-serve. Hand an unqualified firm to the rep "just in case".
