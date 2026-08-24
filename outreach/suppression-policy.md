# MOTIONX outreach — suppression & contact-frequency policy

Suppression is checked **immediately before** every draft/send. If the
suppression list cannot be read, the routine pauses (hard stop) — never guess.

Source of truth: `~/.motionx-outreach/suppression.csv` (outside the repo).

## Suppression reasons
Opted out · negative reply · hard bounce · wrong recipient · already contacted ·
existing client · conflict · user manually suppressed · no longer appropriate.

## Treat as an opt-out (→ MOTIONX/Do Not Contact + suppress, stop immediately)
"no thanks" · "not interested" · "please remove me" · "stop emailing" · "don't
contact me" · "unsubscribe" · "take me off your list". Do not argue or send a
confirmation unless required.

## Bounces
Hard bounce → suppress that address, mark lead Bounced, add MOTIONX/Bounced.
Never guess a replacement address. Never auto-redirect to another employee.

## Out-of-office
Record the return date. Not human engagement. Reschedule the single permitted
follow-up for after they return. Do not repeatedly email the company.

## Frequency caps
- Never contact the same **domain** again within **90 days** unless: they replied
  positively, they explicitly asked for later contact, or Charles approves.
- One recipient per company. Never message multiple people at one company.
- Exactly one automated follow-up per lead, ever.

## Seeds (already in suppression.csv)
- **Firebelly Tea** (firebellytea.com)
- **Insane Hot Sauce**

Seeded as a precaution per Charles's instruction. Do not contact unless Charles
explicitly approves. (Note: neither appears in `charles@madebymotionx.com` Sent
mail as of 2026-06-19 — the only Sent item was an unfilled template test to
daichunyu666@gmail.com.)
