---
title: "NIN Knowledge Commons Operational Playbook"
status: "Proposed operating playbook"
version: "0.1"
applicability: "Manual-first implementation plan; capabilities remain inactive until built and verified"
---

# NIN Knowledge Commons Operational Playbook

## 1. Operating purpose

This playbook turns the [NIN Knowledge Commons Doctrine](DOCTRINE.md) into a solo-founder implementation and operating method. It covers namespace creation, Knowledge Pack contribution, review, publication, localization, RAG/graph indexing, installation, correction, recall, pilot operation, hosting, and staged commercialization.

It does not authorize production deployment, institutional use, PHI processing, clinical decision support, competency determination, native payments, minor participation, or autonomous action.

## 2. Manual-first operating model

Start with one hosted public catalog and portable packages. Use manual review and deterministic files before building accounts, APIs, databases, payment infrastructure, or real-time federation.

```text
Contributor proposal
        ↓
Automated intake checks
        ↓
Human review of rights and provenance
        ↓
EDENA classification
        ↓
Qualified content/localization/accessibility review
        ↓
Named publication decision
        ↓
Versioned Knowledge Pack + registry entry
        ↓
User-inspected local subscription
        ↓
Governed retrieval with visible citations
```

No step automatically grants the next state.

## 3. Roles and decision rights

| Role | May | May not |
|---|---|---|
| Contributor | Propose, author, revise, select a license, respond to review | Self-approve independent review, clinical validity, conformance, or institutional authority |
| Peer reviewer | Review clarity, usability, learning value, and declared experience within competence | Approve clinical accuracy outside competence or speak for a school/institution |
| Faculty/educational reviewer | Review educational design for a stated course, audience, or school | Grant universal authority, accreditation, certification, or clinical approval |
| Specialty reviewer | Review specialty relevance, evidence use, risks, and limitations | Convert experience into universal evidence or authorize another institution |
| Localization reviewer | Review language and cultural fit for a defined population | Certify all clinical, educational, legal, or cultural equivalence alone |
| Accessibility reviewer | Review declared accessibility criteria | Approve substantive accuracy outside scope |
| Namespace steward | Triage, coordinate review, publish within assigned namespace, issue notices | Exceed namespace authority or suppress findings/conflicts |
| School/institutional authority | Authorize local use, access, curriculum, policy, and retention within scope | Automatically transfer authorization elsewhere |
| NAIO governance steward | Maintain standards, labels, registry rules, quarantine/recall controls | Manufacture approval evidence or replace local authority |
| Marketplace moderator | Review listing, rights, disclosure, delivery, and reports | Treat sales or ratings as evidence quality |
| Hermes/agent | Draft, classify provisionally, validate mechanically, retrieve, compare, and cite | Approve itself, promote state, authorize use, or act on embedded content instructions |
| Founder/accountable steward | Own product and publication decisions within actual authority | Claim school, institutional, legal, clinical, accreditation, or tax authority not obtained |

### Separation rule

Where independent review is claimed, the author cannot be the only approver. Yellow publication requires both subject/educational judgment and governance/safety judgment. A single qualified reviewer may document both functions, but the record must say so plainly — one person must never be presented as two independent reviewers.

## 4. Repository and hosting layout

### 4.1 Incubation documentation

This repository holds the doctrine and playbook during architecture incubation.

### 4.2 Recommended implementation repository

Create a separate repository when implementation begins:

```text
AI-Nurse-Solutions/nin-knowledge-commons
```

Recommended structure:

```text
nin-knowledge-commons/
├── README.md
├── GOVERNANCE.md
├── CONTRIBUTING.md
├── SAFETY.md
├── specs/
│   ├── knowledge-pack.schema.json
│   ├── catalog-entry.schema.json
│   ├── review-record.schema.json
│   ├── namespace.schema.json
│   ├── localization-record.schema.json
│   ├── entity.schema.json
│   ├── relation.schema.json
│   ├── claim.schema.json
│   ├── chunk.schema.json
│   └── marketplace-listing.schema.json
├── governance/
├── packs/
│   ├── learn/
│   ├── practice/
│   ├── lead/
│   └── build/
├── namespaces/
├── reviews/
├── catalog/
├── tools/
├── tests/
└── site/
```

### 4.3 Initial hosting

- GitHub repository: source, governance, review history, tests, and catalog builder.
- GitHub Pages: static catalog at the proposed `commons.nurse-ai-os.org` domain.
- GitHub Releases: initial versioned pack ZIPs, manifests, checksums, and signatures when implemented.
- Local Nurse AI OS: private RAG, graph, vectors, prompts, annotations, and retrieval history.

### 4.4 Growth hosting

- Cloudflare R2 or another exportable S3-compatible store: large immutable public packs and media.
- Managed PostgreSQL/Supabase or a deliberately selected equivalent: future accounts, namespaces, review queues, entitlements, and public D0 search.
- Dedicated graph database: deferred until measured multi-hop query needs exceed portable edge tables and relational storage.

Do not host institution-specific or PHI-bearing libraries in the public Commons stack.

## 5. Knowledge Pack structure

A pack should be assembled as:

```text
pack/
├── manifest.yaml
├── content/
├── sources/
├── graph/
│   ├── entities.jsonl
│   ├── relations.jsonl
│   └── claims.jsonl
├── reviews/
├── LICENSE
├── THIRD_PARTY_NOTICES.md
└── CHANGELOG.md
```

`index/` is generated locally or by an authorized service and is not canonical pack content:

```text
index/
├── chunks.jsonl
├── index-manifest.json
└── optional-vectors/
```

### 5.1 Required manifest groups

1. **Identity:** pack ID, namespace, title, version, state.
2. **People:** creator, contributors, publisher, maintainer, contact.
3. **Purpose:** lane, subject, intended audience, intended use, prohibited use.
4. **Context:** locality, jurisdiction, languages, school/specialty scope.
5. **Governance:** EDENA tier, data class, action modes, accountable human, stop conditions.
6. **Evidence:** sources, claim types, evidence status, limitations, conflicts, review due.
7. **Review:** review-record IDs, reviewer scopes, decisions, expiration.
8. **Rights:** creator ownership, license, third-party rights, attribution, commercial permission.
9. **Integrity:** file inventory, SHA-256 digests, dependencies, package digest, signature status.
10. **Lifecycle:** created, submitted, published, superseded, quarantined, retired, recalled.
11. **Relationships:** translation, derivation, prerequisite, citation, related pack, supersession.
12. **AI disclosure:** tools/models used, purpose, human verification, unresolved AI-generated material.

### 5.2 Stable identity rule

Version changes do not create a new pack identity. Materially different purpose, authority, audience, or ownership may require a new pack ID rather than a misleading version increment.

## 6. Namespace onboarding procedure

### Step 1 — Define the node

Record:

- namespace ID;
- owner/steward;
- locality and jurisdiction;
- public, partner, private, or commercial visibility;
- eligible lanes and content;
- data ceiling;
- risk ceiling;
- review authorities;
- publication and emergency contacts;
- retention and export policy;
- correction, appeal, and retirement route.

### Step 2 — Verify naming authority

Do not use a school, hospital, association, locality body, or employer name as if partnered or approved without evidence. Until authorized, use a generic or anonymized pilot namespace.

### Step 3 — Approve the namespace record

A named human steward records the decision and limitations. Automated validation may confirm structure but cannot authorize the namespace.

### Step 4 — Test isolation

Prove that:

- private records do not enter public catalogs;
- one namespace cannot overwrite another;
- authorization filters run before retrieval;
- retirement and quarantine affect only the intended namespace/version;
- exports preserve provenance.

## 7. Contribution workflow

### 7.1 Proposal

Collect:

- contributor display name and private contact;
- adult eligibility confirmation during the initial program;
- role and optional organization;
- artifact type and lane;
- intended audience and use;
- language and locality;
- authorship and collaborators;
- AI-assistance disclosure;
- third-party materials;
- source list and evidence claims;
- rights and proposed license;
- EDENA self-assessment;
- free, showcase, or future commercial preference;
- requested attribution;
- consent to review and publication under declared terms.

Do not collect PHI, patient stories, learner records, employment records, or confidential policies.

Store the private contact and any eligibility evidence in a separate private intake record. Do not copy private contact data into pack manifests, catalogs, lexical/vector/graph indexes, public review records, or analytics. Publish only the display name, attribution, and contact route the contributor explicitly approved for public use.

The intake notice must state purpose, access roles, protection method, retention period, correction route, and deletion or de-identification procedure. Access is limited to named intake or governance stewards with a task need. Delete private contact data when the declared purpose and retention period end unless a documented legal, safety, payment, dispute, or audit obligation requires a proportionate hold.

### 7.2 Intake scan

Mechanical checks must fail closed for:

- invalid schema;
- missing contributor or rights information;
- secrets and credentials;
- PHI-like or person-identifiable content;
- unsupported clinical, institutional, accreditation, certification, or compliance claims;
- missing or broken files;
- stale hashes;
- executable or active content outside the declared artifact policy;
- unlicensed third-party assets;
- author self-approval represented as independent review;
- missing translation source digest;
- duplicate or conflicting identity/version.

A passed scan means only that automated checks did not find a listed defect. It is not approval.

### 7.3 Triage states

```text
draft
submitted
quarantined
under_review
changes_requested
accepted_for_scope
published
superseded
retired
recalled
withdrawn
```

Quarantine is appropriate when rights, safety, provenance, privacy, or authority is unclear. It is not a punitive label.

## 8. Review workflow

### 8.1 Required review dimensions

Each applicable dimension receives a separate record:

- rights and provenance;
- EDENA/data/action classification;
- educational quality;
- specialty accuracy and evidence;
- localization/cultural fit;
- accessibility;
- technical execution/security;
- institutional or school authorization;
- marketplace listing integrity.

### 8.2 Green publication

Minimum:

- D0 content;
- rights/provenance check;
- source and limitation review;
- one independent human review appropriate to the content;
- visible no-authority boundary;
- current version and correction route.

### 8.3 Bounded Yellow publication

Minimum:

- named accountable owner;
- source, assumptions, limitations, and intended-use review;
- subject/educational or specialty review;
- governance/safety review;
- versioned decision record;
- human approval before distribution or adoption;
- review expiration;
- measurable evaluation criteria.

### 8.4 Orange handling

Public Orange submissions remain held or refused. Do not down-classify them by removing obvious words while preserving the consequential intended use. Route only to a future formally authorized pathway.

### 8.5 Review record

A review record must include:

- pack ID and exact version/digest;
- reviewer identity and role;
- declared competence and scope;
- conflicts and recusals;
- materials inspected;
- findings and evidence;
- limitations and unresolved issues;
- decision;
- date and expiration/review due;
- jurisdiction and namespace;
- required corrections;
- whether re-review is required after change.

## 9. Publication procedure

### Step 1 — Freeze candidate bytes

Generate the candidate pack and exact inventory. No review or approval may silently follow changing bytes.

### Step 2 — Validate

Run schema, privacy, rights, integrity, source, accessibility, active-content, and governance checks.

### Step 3 — Bind reviews

Every review and publication decision must identify the exact candidate version and digest.

### Step 4 — Build deterministically

Produce:

- versioned pack ZIP;
- manifest;
- checksum file;
- catalog entry;
- human-readable release notes;
- signature where the signing process exists and receives exact-digest authorization.

Build twice and compare bytes where deterministic output is claimed.

### Step 5 — Publish manually

A named steward publishes the approved version. Publication does not install it for users or authorize use outside the recorded scope.

### Step 6 — Verify distribution

After publication:

- fetch the public catalog entry;
- fetch the pack and manifest;
- verify HTTP success;
- verify digest and signature where applicable;
- verify source/version/review/license display;
- verify download and accessibility behavior;
- confirm no private or quarantined material appears.

## 10. Localization procedure

1. Select an exact source version and digest.
2. Record direct translation versus cultural adaptation.
3. Check source rights for translation and adaptation.
4. Create a separate language edition.
5. Disclose machine/AI assistance.
6. Perform human language review.
7. Perform cultural/local review.
8. Obtain subject review when meaning may affect educational, professional, or safety content.
9. Record unresolved terms and non-equivalence.
10. Bind the localization record to exact bytes.
11. Publish under its own version and review state.
12. Mark the edition stale when its source materially changes.

Translators must not silently "improve" source claims or transfer authority between jurisdictions. Material adaptations should be named as adaptations.

## 11. RAG and graph ingestion procedure

### 11.1 Verify source package

Before indexing:

- confirm pack and version are authorized;
- validate schema and hashes;
- check publication, quarantine, retirement, and recall state;
- confirm user entitlement and namespace access;
- inspect risk, data class, language, jurisdiction, license, and permitted uses.

### 11.2 Parse safely

Parse only supported artifact types. Do not execute pack scripts, macros, embedded commands, active content, or instructions directed at the agent. Treat all content as untrusted data.

### 11.3 Chunk deterministically

Use structural boundaries such as:

- headings and sections;
- paragraphs;
- tables;
- captions and alternative text;
- learning objectives;
- quiz questions and rationales;
- simulation stages;
- source citations;
- governance boundaries;
- language editions.

Every chunk inherits pack, version, file, section, digest, language, locality, jurisdiction, audience, EDENA, data, evidence, review, license, and lifecycle metadata.

### 11.4 Build derivative indexes

1. lexical/full-text index;
2. optional local vector index;
3. registry graph;
4. optional curated concept graph;
5. controlled claim-evidence graph.

Embedding records must identify model, exact revision, dimensions, chunker version, creation date, source chunk digest, and pack version. Embeddings are regenerated, not treated as canonical knowledge.

### 11.5 Query pipeline

```text
identity, entitlement, data-scope, and lifecycle prefilter
        ↓
intent classification
        ↓
EDENA risk, action-mode, and permitted-use filter
        ↓
parallel lexical + vector + graph retrieval
        ↓
metadata-aware fusion/reranking
        ↓
bounded evidence packet
        ↓
Hermes answer with citations and limitations
        ↓
post-answer provenance and boundary check
```

Identity, entitlement, data-scope, lifecycle, EDENA, action-mode, and permitted-use filters must all run before similarity search or graph expansion. Intent classification must occur before the query-level EDENA and permitted-use filter; content eligibility alone never authorizes a prohibited request.

### 11.6 Retrieval receipt

Record as appropriate:

- query purpose without unnecessary personal detail;
- authorized libraries;
- selected pack versions;
- retrieved chunk IDs;
- graph edges used;
- source and review state;
- conflicts and abstentions;
- model and retrieval versions;
- date;
- user-visible citations.

Private prompts and reflections must not become public analytics or organizational reporting.

### 11.7 Removal and invalidation

On quarantine, retirement, withdrawal, recall, entitlement loss, or approved deletion:

- stop new retrieval;
- remove active chunks;
- remove vectors;
- remove active graph edges;
- refresh catalog warnings;
- retain only proportionate audit provenance;
- rebuild from the authorized lock file;
- test that the removed content no longer appears.

## 12. Local installation procedure

1. Download or select the pack.
2. Perform read-only preflight.
3. Validate manifest, hashes, license, review, risk, and data boundaries.
4. Show exact destination and files.
5. Show enabled retrieval scope and prohibited uses.
6. Require explicit human approval.
7. Install without overwriting another version silently.
8. Update `library-lock.json`.
9. Build local indexes.
10. Run retrieval and citation tests.
11. Provide disable, uninstall, and rollback controls.

A download, opening action, or extraction does not install, authorize, or activate a pack. Treat extracted content as untrusted, and open active content only in an approved sandbox. A general request to use the Commons does not bypass the exact activation card for a local mutation.

## 13. Correction, supersession, retirement, and recall

### 13.1 Ordinary correction

- receive report;
- acknowledge and triage;
- quarantine if harm or authority confusion is plausible;
- notify creator and steward;
- assess affected versions and translations;
- produce a corrected version;
- rerun review where required;
- publish a clear change record;
- notify known subscribers where feasible.

### 13.2 Supersession

A new version may supersede an earlier version without erasing its history. Active retrieval defaults to the current authorized version while preserving citations to historical material when intentionally requested.

### 13.3 Retirement

Use when content is obsolete, unsupported, or no longer appropriate. Provide notice, replacement where available, index invalidation, and retention of provenance.

### 13.4 Recall

Use when continued use may cause material harm, rights violation, privacy exposure, or serious authority confusion.

Immediate actions:

1. stop public distribution;
2. mark recalled in the registry;
3. remove from active retrieval;
4. preserve evidence securely;
5. notify accountable parties and known subscribers where feasible;
6. identify affected derivatives and translations;
7. assess reporting obligations;
8. correct, replace, or permanently withdraw;
9. document restart or closure decision.

## 14. Incident response

Potential incidents include:

- PHI or sensitive data exposure;
- unlicensed or misattributed content;
- prompt injection or executable content;
- cross-namespace leakage;
- unauthorized retrieval;
- stale/retired content presented as current;
- fabricated review or authority;
- unsafe translation;
- malicious pack update;
- seller fraud or inaccessible purchased content;
- failed recall or incomplete index deletion.

Response sequence:

1. protect people;
2. pause, quarantine, or disable;
3. preserve proportionate evidence;
4. notify the accountable steward;
5. identify packs, versions, users, indexes, and decisions affected;
6. correct or retract outputs where feasible;
7. investigate root cause;
8. implement corrective and preventive action;
9. retest deletion, rollback, and boundaries;
10. document resume, restrict, retire, or recall decision.

Professional overrides and near misses are learning signals, not automatically user failure.

## 15. Creator showcase and marketplace procedure

### Stage 1 — Free Commons

Curate useful public D0 packs under explicit licenses.

### Stage 2 — Creator portfolios

Show creator attribution, packs, languages, collaboration, rights, review states, and maintenance history.

### Stage 3 — External checkout links

Permit a creator-owned external purchase route only after listing review. The listing must disclose that the creator controls the transaction and delivery terms. Payment cannot change evidence or trust labels.

### Stage 4 — Sponsored bounties

Use a written scope, ownership, license, reviewer, deliverables, payment conditions, conflicts, and acceptance criteria.

### Stage 5 — Native marketplace

Do not open until legal, entity, tax, identity, sanctions, cross-border payout, refund, chargeback, accessibility, moderation, support, privacy, copyright, seller suspension, and appeal requirements are operational.

The proposed 85/15 split is not final policy. No listing may claim it until formally approved.

## 16. Initial pilot playbook

### 16.1 Recommended default

- Philippines/SEA locality or school partner;
- one bounded Nursing Fundamentals learning subject;
- English and Tagalog;
- adult contributors;
- manual review;
- creator-owned IP;
- no PHI;
- Green and bounded Yellow only;
- private/invitation-only naming until authorization;
- no native payment.

### 16.2 Pilot sequence

1. Confirm partner or use an anonymized community pilot.
2. Name steward, educational reviewer, localization reviewer, and incident contact.
3. Approve namespace and scope.
4. Train contributors on rights, no-PHI, evidence, and AI disclosure.
5. Create one source-language pack.
6. Run peer and faculty/educational review.
7. Produce one translated/adapted edition.
8. Run language and cultural review.
9. Publish to the bounded namespace.
10. Have users inspect and install locally.
11. Run retrieval and citation tests.
12. Process one planned correction and supersession drill.
13. Evaluate safety, usefulness, burden, trust, accessibility, and contributor experience.
14. Decide to revise, continue, expand, pause, or stop.

### 16.3 Do not measure as pilot outcomes

Do not infer or claim:

- clinical competence;
- patient outcomes;
- NCLEX or examination success;
- certification;
- institutional approval;
- employment readiness;
- faculty replacement;
- causal learning improvement without an appropriate evaluation design.

## 17. Ninety-day solo-founder roadmap

### Days 1–30 — Standard and refusal foundation

Deliver:

- separate implementation repository;
- architecture decision record;
- Knowledge Pack, review, namespace, localization, entity, relation, claim, chunk, and catalog schemas;
- validator;
- valid and adversarial fixtures;
- contribution and review forms;
- rights and evidence labels;
- Green/Yellow/Orange refusal tests.

Gate:

- unsafe, incomplete, contradictory, or unauthorized packs fail closed;
- no marketplace, hosted RAG, graph database, account system, or institutional claim is added.

### Days 31–60 — Reference catalog

Deliver:

- four reference packs across Learn, Practice, Lead, and Build;
- deterministic catalog generator;
- static catalog;
- versioned release procedure;
- report, quarantine, correction, supersession, retirement, and recall paths;
- English plus one reviewed Tagalog edition;
- browser accessibility and link tests.

Gate:

- public catalog exposes exact source, version, review, evidence, license, language, locality, and limitations;
- no private data or Orange content is indexed.

### Days 61–90 — Local retrieval and pilot readiness

Deliver:

- read-only pack preflight and local import design;
- `library-lock.json` contract;
- SQLite/FTS5 metadata and lexical index;
- portable registry graph;
- optional local embedding adapter contract;
- retrieval receipt and citation format;
- authorization-before-similarity tests;
- pilot charter, training, review, incident, and evaluation materials.

Gate:

- disabled, unauthorized, quarantined, retired, and recalled content cannot be retrieved as active;
- removal clears active chunks, vectors, and edges;
- a human pilot owner and reviewers are named before the pilot starts.

## 18. Acceptance tests

### Pack integrity

- schema-valid and invalid fixtures;
- deterministic inventory and package build;
- checksum and signature verification where implemented;
- stale hash and duplicate identity refusal;
- rollback and clean removal.

### Rights and provenance

- creator and license required;
- third-party assets declared;
- source records resolve;
- AI assistance disclosed;
- translation bound to exact source digest.

### Governance

- D0 public ceiling;
- Green and bounded Yellow public scope;
- Orange hold;
- no self-approval;
- review expiration;
- scope-specific labels;
- inclusion-not-endorsement display.

### Retrieval

- authorization filter before lexical/vector/graph search;
- visible source/version/review citations;
- conflict and uncertainty display;
- retired version exclusion;
- private namespace isolation;
- prompt-injection refusal;
- complete index invalidation.

### Accessibility and localization

- keyboard operation;
- visible focus;
- minimum 44×44 CSS-pixel interactive targets;
- narrow-screen overflow checks;
- image alternatives and captions;
- language and direction metadata;
- reviewed terminology and stale-translation warning.

### Incident and lifecycle

- report and quarantine drill;
- correction and supersession drill;
- recall and subscriber-notice drill;
- restore and rebuild from authoritative packages;
- audit record without unnecessary private data.

## 19. Evaluation set for hybrid retrieval

Maintain fixed queries covering:

1. exact terminology;
2. semantic explanation;
3. prerequisite navigation;
4. language and locality filtering;
5. current versus retired version;
6. conflicting sources;
7. missing evidence and abstention;
8. unauthorized school namespace;
9. prompt injection inside a pack;
10. withdrawn creator content;
11. paid-versus-free ranking neutrality;
12. patient-specific request refusal;
13. citation accuracy;
14. removal of chunks, vectors, and graph edges.

Track citation precision, source coverage, retrieval recall, conflict detection, abstention correctness, stale-version retrieval, unauthorized retrieval, and removal completeness. The target for unauthorized retrieval is zero.

## 20. Explicit MVP deferrals

Do not include in the first release:

- native marketplace or platform-held funds;
- minors;
- patient-specific tools;
- clinical decision support;
- institution-specific clinical procedures;
- competency/readiness determinations;
- accreditation or continuing-education claims;
- real-time peer-to-peer federation;
- automated publication or clinical approval;
- universal hosted embeddings;
- dedicated graph database;
- large-scale recommendation engine;
- school SSO;
- PHI or D3/D4 processing;
- MCP, connector, cron, or autonomous-action activation.

## 21. Founder decision register

The following require explicit founder judgment before implementation or public claim:

- final public name and trademark posture;
- separate repository creation;
- pilot partner, locality, subject, and language pair;
- namespace naming authority;
- exact pack and contribution licenses;
- contributor age and consent rules;
- reviewer qualifications and compensation;
- public versus private pilot scope;
- hosted providers and regions;
- embedding/model policy;
- creator checkout eligibility;
- bounties;
- native marketplace and revenue split;
- public Orange-content pathway;
- institutional and PHI-eligible architecture.

## 22. Release gate

Before any implementation is called published, operational, production, validated, approved, or authorized, record:

- exact commit and candidate digest;
- source and generated artifacts;
- applicable doctrine and schemas;
- EDENA/data/action scope;
- test results;
- independent review status;
- unresolved findings;
- licensing and third-party notices;
- deployment state;
- live verification evidence;
- authority and limitations;
- rollback and incident contacts.

Designed, documented, implemented, tested, committed, merged, deployed, and live-verified are distinct states.

---

*Contributors propose. Reviewers verify. Institutions authorize. Nurses steward.*
