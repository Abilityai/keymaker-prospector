# Keymaker Prospector

The prospecting desk of [Keymaker](https://keymaker.agency), a fictional automation agency built in
public during the Agent-Native Agency workshop. A Trinity agent template, Apache 2.0, zero-credential.

**What it does.** Finds specialist recruiting firms of 20-100 people from their public footprint,
qualifies each against the agency's canon (`who-we-serve.md`: two of three signals - size and
specialism, an ATS and a job board, visible hurt), and drafts one first line per firm for the sales
rep to send. Every Monday it delivers ten to the rep's Workspace.

**What it never does.** Send anything. Store a personal email address or phone number. Buy or import
a list. Open or move a deal - a firm becomes a deal only when a conversation starts and Sales opens it.

```
/prospect                       # ten firms, the default field rotation
/prospect --n 5 --field healthcare --region "New England"
/prospect --review              # the list by status; what was handed this month
```

**How it was hired.** Decision 0007 in the canon opened the `prospects` domain and named the
`sales-rep` seat as its owner; the orchestrator created the agent from this repo with `/hire`;
a person granted the edges (orchestrator -> prospector, prospector -> sales), turned autonomy on,
and set the Monday schedule to deliver to the rep. No key to paste: this desk has none.

**Files.** `CLAUDE.md` the rules · `.claude/skills/prospect/` the one playbook ·
`scripts/prospects.py` the only way the list is read or written (every write prints and needs
`--confirm`) · `prospects/prospects.yaml` the list · `drafts/` what the rep reads ·
`.trinity/setup.sh` clones the canon at every start.
