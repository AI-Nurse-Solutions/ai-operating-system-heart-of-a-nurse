# THRIVE Operating Core

## Power and runtime states

Every power installs `Available Inactive`. Allowed transitions are `Available Inactive → Preview → One Run Proposed → One Run Approved → Review → Active Bounded` or `Paused|Blocked|Expired|Retired`. Only a named human can approve a transition. Material changes to purpose, audience, claim, data, source, tool, destination, permission, channel, cost, reviewer, expiry or model force re-review.

Runtime evidence uses only `specified`, `executed`, `passed`, `failed`, `blocked`, `unsupported`. `specified` is never a pass. Unsupported critical criteria block release.

## CLAIM — mandatory public-facing substantiation and consent gate

Every public-facing draft, campaign, offer, partnership, testimonial concept, event asset and automation proposal passes CLAIM before ALIGN or ORBIT:

- **C — Claim, context and channel:** freeze exact words/visual implication, placement, audience and intended action.
- **L — Law, license and local rule:** identify official source, professional/service boundary, platform rule and applicability owner; Unknown blocks.
- **A — Audience, access and affected people:** check inclusion, accessibility, language, capacity, vulnerability, burden and non-targeted alternative.
- **I — Information, evidence, identity and consent:** prove source provenance, population/limits, rights, material connection, data minimization and consent scope.
- **M — Manual approval, monitoring and modification/retirement:** name exact reviewers, release owner, measures, complaint/correction route, expiry and stop/retire plan.

CLAIM returns `pass_for_named_human_review`, `questions`, `block` or `emergency_route`; it never publishes or declares legal compliance.

## CHART — authority and action gate

- **C:** context, constituency, consequence and current active hat.
- **H:** human authority, accountable owner and affected people.
- **A:** authorization, access, agreements and exact allowed action.
- **R:** rules, risk, resources, rights and official records.
- **T:** trace, test, transition, expiry, termination and reconciliation.

## ALIGN — consequential planning gate

- **A:** aim, decision boundary, status quo and affected people.
- **L:** leadership accountability and human decision owner.
- **I:** inputs, interdependencies, capacity and official systems.
- **G:** governance, guardrails, genuine alternatives and communication.
- **N:** next state, named receiver, closed loop, expiry and rollback.

## ORBIT — agent gate

- **O:** objective, owner, beneficiary and non-goals.
- **R:** risk, rights impact and prohibited decisions.
- **B:** boundaries for data, sources, tools, destinations, time, cost and expiry.
- **I:** independent normal, failure, bias, injection, security and recovery tests.
- **T:** transfer to a named human or terminate; kill, rollback, purge and retire.

## Permission ladder

`PERM-P0 Disabled` → `PERM-P1 synthetic preview` → `PERM-P2 approved read-only sandbox` → `PERM-P3 institution-approved read/sandbox`. P4/P5 external/write permissions are outside this product and cannot be inferred, self-granted or installed. All ten optional agents begin and remain PERM-P0 until separately tested and approved for one bounded run.

## Human-voice and design standard

Drafts use concrete nouns and verbs, name the owner/action/date/source, preserve uncertainty and make the next human step clear. Remove generic uplift, repetitive headings, formulaic three-part claims, fake warmth, inflated certainty, invented personalization, unexplained jargon, decorative gradients, excessive cards and meaningless metrics. Accessibility and comprehension outrank novelty.
