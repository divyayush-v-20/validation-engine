# Validation Engine — Implementation Plan

**Project:** Gracenote Metadata Quality Validator (Backend)
**Hackathon:** Hack-AI-Thon '26, October 27–29, 2026
**Status:** Pre-hackathon planning
**Last updated:** October 26, 2026

---

## 1. Overview

The validation engine is the backend service that powers the Gracenote Metadata Quality Validator. It validates pre-loaded metadata records against a curated set of standards-backed rules, provides AI-assisted explanations and correction suggestions, and manages the reviewer workflow (approve/reject/bulk actions with full audit trail).

The system operates on **pre-loaded synthetic data only** — there is no ingestion pipeline. Records are seeded once into the database, and all validation, review, and AI features work against that dataset.

---

## 2. Architecture

```
seed_data/records.json
        │
        ▼  (one-time load script)
   ┌─────────────┐
   │  DynamoDB    │  ← records, findings, suggestions, audit_log tables
   └──────┬──────┘
          │
   POST /validate (on-demand trigger)
          │
          ▼
   ┌──────────────┐        ┌───────────────┐
   │ Rule Engine   │───────►│ Findings      │
   │ (deterministic)│       └───────┬───────┘
   └──────────────┘                │
                                   ▼
                       ┌──────────────────┐
                       │  AI Layer        │
                       │  (Bedrock/Claude)│
                       │  - Suggestions   │
                       │  - Explanations  │
                       │  - Chat agent    │
                       │  - Web search    │
                       └────────┬─────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Review Workflow  │
                       │  - Approve/Reject│
                       │  - Bulk actions  │
                       │  - Audit trail   │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  REST API        │
                       │  (FastAPI)       │
                       │  ← consumed by   │
                       │    validator-ui  │
                       └──────────────────┘
```

---

## 3. Tech Stack

| Component            | Technology                  | Why                                                    |
| -------------------- | --------------------------- | ------------------------------------------------------ |
| Language             | Python 3.12                 | Fast to prototype, rich ecosystem for AI/data work     |
| API framework        | FastAPI                     | Async, auto-docs (OpenAPI), streaming support for chat |
| Database             | Amazon DynamoDB             | Serverless, fast, fits key-value + query patterns      |
| AI / LLM             | Amazon Bedrock (Claude)     | Chat agent, explanations, suggestion generation        |
| Web search           | Tavily / Brave Search API   | Source research for reviewer evidence gathering        |
| Rule definitions     | YAML files (versioned)      | Human-readable, diffable, no code change to add rules  |
| Containerization     | Docker + docker-compose     | Consistent local dev, easy deployment                  |
| Testing              | pytest                      | Standard Python test framework                         |

---

## 4. Directory Structure

```
validation-engine/
├── src/
│   ├── rules/                     # Deterministic rule engine
│   │   ├── engine.py              # Runs applicable rules against records
│   │   ├── registry.py            # Loads and indexes rules from YAML catalog
│   │   ├── base_rule.py           # Abstract base: check() + is_applicable()
│   │   └── families/
│   │       ├── __init__.py
│   │       ├── titles.py          # TTL-REQ, TTL-LEN, TTL-CHR
│   │       ├── duration.py        # DUR-001, DUR-003
│   │       ├── subtype.py         # SUB-001, SUB-002
│   │       ├── oad.py             # OAD-001, OAD-002, OAD-003
│   │       ├── audio_language.py  # AUD-001, AUD-002
│   │       ├── required_fields.py # REQ-001, REQ-002, REQ-003
│   │       ├── season_episode.py  # SEP-001, SEP-002 (P1)
│   │       └── genre.py           # GEN-001, GEN-002 (P1)
│   │
│   ├── ai/                        # AI-assisted features
│   │   ├── suggestion.py          # Correction generation with evidence
│   │   ├── confidence.py          # 0–100 composite score (4 components)
│   │   ├── explainer.py           # Plain-language finding explanations
│   │   ├── chat_agent.py          # Conversational query/filter/action agent
│   │   └── web_search.py          # External source research
│   │
│   ├── review/                    # Review workflow
│   │   ├── actions.py             # Single-item approve/reject/exception
│   │   ├── bulk_actions.py        # Bulk with eligibility + confirmation
│   │   └── audit_log.py           # Immutable decision history
│   │
│   ├── api/                       # FastAPI application
│   │   ├── app.py                 # App factory, CORS, lifespan
│   │   ├── routes/
│   │   │   ├── records.py         # GET /records
│   │   │   ├── validate.py        # POST /validate
│   │   │   ├── findings.py        # GET /findings, GET /findings/{id}
│   │   │   ├── suggestions.py     # POST /findings/{id}/suggest, /retry
│   │   │   ├── review.py          # POST /findings/{id}/approve, /reject, /bulk
│   │   │   ├── chat.py            # POST /chat (SSE streaming)
│   │   │   ├── dashboard.py       # GET /dashboard/stats, /severity, /rule-families
│   │   │   └── search.py          # POST /web-search
│   │   └── middleware/
│   │       └── audit.py           # Request-level audit logging
│   │
│   ├── mcp/                       # MCP server (PRD §8.10)
│   │   ├── server.py              # Tool definitions
│   │   └── tools.py               # validate_record, explain_finding, etc.
│   │
│   └── models/                    # Pydantic data models
│       ├── record.py              # MetadataRecord, RecordType, Market
│       ├── finding.py             # Finding, Severity, ReviewState, RuleResult
│       ├── suggestion.py          # Suggestion, ConfidenceScore, Attempt
│       └── rule.py                # RuleDefinition, ApplicabilityCondition
│
├── rules_catalog/                 # Versioned rule definitions
│   └── v0.3/
│       ├── titles.yaml
│       ├── duration.yaml
│       ├── subtype.yaml
│       ├── oad.yaml
│       ├── audio_language.yaml
│       ├── required_fields.yaml
│       ├── season_episode.yaml
│       └── genre.yaml
│
├── seed_data/                     # Pre-loaded demo dataset
│   ├── load_seed.py               # One-time script to populate DynamoDB
│   ├── generate_seed.py           # Generates ~1000 synthetic records
│   └── records.json               # The seed dataset
│
├── tests/
│   ├── test_rules/                # Per-family rule tests
│   ├── test_api/                  # API endpoint tests
│   ├── test_review/               # Workflow tests
│   └── conftest.py                # Shared fixtures
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── IMPLEMENTATION_PLAN.md
└── README.md
```

---

## 5. Data Models

### 5.1 MetadataRecord

The core record representing a Gracenote video metadata entry.

```python
class RecordType(str, Enum):
    MOVIE = "Movie"
    SHOW = "Show"
    SEASON = "Season"
    EPISODE = "Episode"

class MetadataRecord(BaseModel):
    record_id: str                    # e.g. "MV-DEMO-0127"
    record_type: RecordType
    market: str                       # e.g. "US", "UK"
    title: Optional[str]
    original_title: Optional[str]
    runtime_minutes: Optional[Any]    # Can be malformed — that's the point
    subtype: Optional[str]
    original_air_date: Optional[str]
    original_audio_language: Optional[str]
    genre: Optional[str]
    subgenre: Optional[str]
    season_number: Optional[Any]
    episode_number: Optional[Any]
    parent_series_id: Optional[str]
    parent_season_id: Optional[str]
    release_year: Optional[int]
    country_of_origin: Optional[str]
    original_network: Optional[str]
    # ... additional fields as needed
```

### 5.2 Finding

```python
class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RuleResultType(str, Enum):
    FAIL = "fail"
    PASS = "pass"
    NOT_EVALUATED = "not_evaluated"
    NOT_APPLICABLE = "not_applicable"

class ReviewState(str, Enum):
    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_RESEARCH = "needs_research"
    EXCEPTION = "exception"

class Finding(BaseModel):
    finding_id: str                   # e.g. "F-0042-0127"
    record_id: str
    rule_id: str                      # e.g. "DUR-001"
    rule_name: str
    rule_family: str                  # e.g. "Duration"
    field: str                        # e.g. "runtime_minutes"
    observed_value: Optional[str]
    expected_condition: str
    severity: Severity
    result: RuleResultType
    explanation: str                  # Human-readable why
    standard_reference: str           # Link/name of governing standard
    standard_version: str
    rule_set_version: str             # e.g. "v0.3"
    review_state: ReviewState
    created_at: datetime
```

### 5.3 Suggestion & Confidence

```python
class ConfidenceComponent(BaseModel):
    name: str                         # e.g. "Evidence quality & authority"
    score: float                      # Achieved score
    max_score: float                  # Weight ceiling
    explanation: str

class Suggestion(BaseModel):
    suggestion_id: str
    finding_id: str
    attempt_number: int               # v1, v2, ...
    proposed_value: Optional[str]     # None if withheld
    withheld: bool                    # True if below threshold
    rationale: str
    confidence_score: float           # 0–100 composite
    confidence_band: str              # "High", "Medium", "Low"
    confidence_components: list[ConfidenceComponent]
    evidence_used: list[EvidenceItem]
    reviewer_context: Optional[str]   # Input from reviewer for retries
    created_by: str
    created_at: datetime

class EvidenceItem(BaseModel):
    source_type: str                  # "record", "standard", "web", "ai"
    label: str
    content: str
    authority: Optional[str]          # "Official", "Secondary", etc.
    retrieved_at: Optional[datetime]
```

### 5.4 AuditEntry

```python
class AuditEntry(BaseModel):
    audit_id: str
    finding_id: str
    action: str                       # "approve", "reject", "suggest", "retry", "bulk_approve", etc.
    reviewer: str
    timestamp: datetime
    details: dict                     # Action-specific data
    suggestion_version: Optional[int]
    rule_set_version: str
```

---

## 6. Rule Engine Design

### 6.1 Principles

1. **Rules are data, not just code.** Each rule is defined in YAML with metadata. The engine loads them at startup.
2. **Applicability before evaluation.** Every rule declares which record types, markets, and subtypes it applies to. If applicability is unknown → `NOT_EVALUATED`, never a false positive.
3. **Deterministic results only.** The rule engine returns Pass/Fail/Not Evaluated/Not Applicable. No probabilities. The 0–100 confidence score exists only on AI suggestions.
4. **One finding per rule violation.** Multiple issues on the same record are separate findings.

### 6.2 Rule YAML Format

```yaml
# rules_catalog/v0.3/duration.yaml
rules:
  - id: DUR-001
    name: "Duration parseable & positive"
    family: "Duration"
    severity: high
    standard_reference: "NEd Fields catalog · Duration"
    standard_version: "2026-Q3"
    description: "Runtime must be a parseable positive integer in minutes"
    applicability:
      record_types: [Movie, Show, Episode]
      markets: "*"                    # All markets
      requires_fields: [runtime_minutes]
    failure_condition: "runtime_minutes is absent, non-numeric, zero, or negative"
    expected_condition: "Parseable integer > 0"
    test_cases:
      - input: { runtime_minutes: 112 }
        expected: pass
      - input: { runtime_minutes: 0 }
        expected: fail
      - input: { runtime_minutes: "1h52" }
        expected: fail
      - input: { runtime_minutes: -95 }
        expected: fail

  - id: DUR-003
    name: "Runtime within plausibility bounds"
    family: "Duration"
    severity: medium
    standard_reference: "NEd Fields catalog · Duration"
    standard_version: "2026-Q3"
    description: "Runtime should be within configured plausibility bounds (1–600 min)"
    applicability:
      record_types: [Movie, Show, Episode]
      markets: "*"
      requires_fields: [runtime_minutes]
      depends_on_pass: [DUR-001]      # Only runs if DUR-001 passed
    failure_condition: "runtime_minutes < 1 or > 600"
    expected_condition: "Integer in range 1–600 minutes"
    bounds:
      min: 1
      max: 600
```

### 6.3 Base Rule Interface

```python
class BaseRule(ABC):
    def __init__(self, config: dict):
        self.rule_id = config["id"]
        self.name = config["name"]
        self.family = config["family"]
        self.severity = Severity(config["severity"])
        self.applicability = config["applicability"]
        self.standard_reference = config["standard_reference"]
        self.standard_version = config["standard_version"]

    def is_applicable(self, record: MetadataRecord) -> bool:
        """Check if this rule applies to the given record type/market."""
        ...

    @abstractmethod
    def evaluate(self, record: MetadataRecord) -> RuleResult:
        """Run the check. Returns pass/fail with explanation."""
        ...
```

### 6.4 Rule Engine Flow

```
For each record:
  1. Load all rules from registry
  2. Filter to applicable rules (record type, market, subtype)
  3. Resolve dependency order (e.g. DUR-003 depends on DUR-001)
  4. Execute each applicable rule:
     - If dependencies failed → skip with NOT_EVALUATED
     - If required fields missing → NOT_EVALUATED (not a false fail)
     - Otherwise → evaluate → PASS or FAIL
  5. Store each result as a Finding in DynamoDB
```

---

## 7. P0 Rule Families — First Iteration

These are the 6 rule families to implement for the hackathon demo. Each has 2–3 concrete rules.

### 7.1 Titles (TTL)

| Rule ID  | Check                              | Severity |
| -------- | ---------------------------------- | -------- |
| TTL-REQ  | Title must not be blank/missing    | High     |
| TTL-LEN  | Title must not exceed NEd limit    | Medium   |
| TTL-CHR  | No forbidden characters/terms      | Medium   |

Applies to: Movie, Show, Episode. Standard: Titles Official Content Standard.

### 7.2 Duration / Runtime (DUR)

| Rule ID  | Check                                      | Severity |
| -------- | ------------------------------------------ | -------- |
| DUR-001  | Parseable positive integer                 | High     |
| DUR-003  | Within plausibility bounds (1–600 min)     | Medium   |

Applies to: Movie, Show, Episode. Standard: NEd Fields catalog · Duration.

### 7.3 Subtype (SUB)

| Rule ID  | Check                                      | Severity |
| -------- | ------------------------------------------ | -------- |
| SUB-001  | Subtype present when required              | High     |
| SUB-002  | Valid controlled value for record type     | High     |

Applies to: Movie, Show, Sports. Standard: Subtype Official Content Standard.

### 7.4 Original Air Date (OAD)

| Rule ID  | Check                                      | Severity |
| -------- | ------------------------------------------ | -------- |
| OAD-001  | Valid date format                          | High     |
| OAD-002  | Not a suspicious future date (>1 year out) | Medium   |
| OAD-003  | Consistent with supplied source facts      | Medium   |

Applies to: Show, Episode. Standard: Original Air Date Official Content Standard.

### 7.5 Original Audio Language (AUD)

| Rule ID  | Check                                      | Severity |
| -------- | ------------------------------------------ | -------- |
| AUD-001  | Value from controlled language list        | High     |
| AUD-002  | "Unknown"/"UNK" flagged where disallowed  | Medium   |

Applies to: Movie, Show, Episode. Standard: Original Audio Language Official Content Standard.

### 7.6 Required Fields (REQ)

| Rule ID  | Check                                      | Severity |
| -------- | ------------------------------------------ | -------- |
| REQ-001  | Release year present                       | Medium   |
| REQ-002  | Country of origin present                  | Medium   |
| REQ-003  | Original network present (Shows)           | Medium   |

Applies to: varies by field. Standard: Core Metadata Fields Official Content Standard.

---

## 8. AI Layer

### 8.1 Suggestion Generation (Bedrock / Claude)

When a reviewer clicks "Suggest correction" on a finding:

1. Gather context: the finding, the record, the rule, any web search results
2. Prompt Claude (via Bedrock) with:
   - The record's current field values
   - The rule that failed and its standard reference
   - Any available evidence (web search results, related records)
   - Reviewer-provided context (if retry)
   - Instruction: propose a correction OR abstain if evidence is insufficient
3. Parse response into a `Suggestion` with proposed value, rationale, and evidence citations
4. Compute confidence score (see §8.2)
5. If score < 65 → withhold the proposed value, show "Needs research" instead

### 8.2 Confidence Scoring (PRD §8.8)

The score is computed from 4 weighted components — not from the model's self-reported confidence.

| Component                           | Weight | Measures                                                       |
| ----------------------------------- | ------ | -------------------------------------------------------------- |
| Evidence quality & authority        | 30%    | Does usable evidence exist? How authoritative is the source?   |
| Evidence-to-record match            | 25%    | Does evidence refer to the same program/version/market/field?  |
| Standard applicability & alignment  | 25%    | Does the rule apply and does the candidate value satisfy it?   |
| Candidate-value support & consistency | 20%  | Is the value directly supported and consistent with other fields? |

Bands: **High** = 85–100 · **Medium** = 65–84 · **Low** = below 65 (withheld).

Implementation: Each component is scored by a structured prompt that evaluates specific evidence features, not by asking the model "how confident are you?"

### 8.3 Chat Agent

The conversational agent receives natural-language queries and translates them to API calls:

- "Show me high-severity title issues for Movies" → filters findings by severity=high, family=Titles, record_type=Movie
- "Why was MV-DEMO-0127 flagged?" → retrieves finding detail + rule explanation
- "Suggest a correction" → triggers suggestion generation
- "Search the web for the official runtime" → triggers web search, returns cited results

Implementation: A Bedrock Claude agent with tool-use that calls the same internal API functions the REST endpoints use. Responses are streamed via SSE.

### 8.4 Web Search

When the reviewer asks to research a source fact:

1. Build a search query from the record's title, year, field in question
2. Call Tavily/Brave Search API
3. Return results with: source URL, snippet, domain, retrieval timestamp
4. Label each result with source quality (Official / Secondary / User-generated)
5. Results are evidence for the reviewer — never auto-applied

---

## 9. Review Workflow

### 9.1 Single-Item Actions

| Action          | Effect                                                                 |
| --------------- | ---------------------------------------------------------------------- |
| Approve         | Sets finding review_state to APPROVED. Records audit entry.            |
| Reject          | Sets review_state to REJECTED. Finding and record are preserved.       |
| Needs research  | Sets review_state to NEEDS_RESEARCH with reason. Keeps finding open.   |
| Mark exception  | Sets review_state to EXCEPTION with reason. Acknowledged but not fixed.|

Every action creates an `AuditEntry` with: reviewer, timestamp, finding ID, action, suggestion version (if applicable), rule set version.

### 9.2 Bulk Actions

1. Reviewer selects findings (via UI selection or chat query like "approve validated low-risk runtime fixes")
2. Backend receives the selection criteria + intended action
3. **Eligibility check:** remove items that are:
   - Low confidence (score < 65) → blocked from bulk approve
   - Conflicting sources → blocked
   - High-risk (linked versions) → blocked
4. Return: eligible count, blocked count with reasons, affected records list
5. Reviewer confirms → backend applies action to eligible items, creates per-item audit entries
6. Response: applied count, failed count (if any changed between check and commit)

### 9.3 Audit Trail

Every mutation is logged:

```
audit-0007 · reviewer: abhinab.mishra · 22:52:16 IST
action: bulk_approve · items: 8/8 applied · 0 failed
rule set v0.3 · suggestion versions captured
selection: { rule: DUR-001, record_type: Movie, has_suggestion: true }
```

Audit entries are append-only in DynamoDB. No deletes, no overwrites.

---

## 10. API Endpoints

### 10.1 Records

| Method | Path                  | Description                          |
| ------ | --------------------- | ------------------------------------ |
| GET    | `/records`            | List records with filters            |
| GET    | `/records/{id}`       | Single record detail                 |

### 10.2 Validation

| Method | Path                  | Description                          |
| ------ | --------------------- | ------------------------------------ |
| POST   | `/validate`           | Run rules on all/selected records    |
| POST   | `/validate/{id}`      | Run rules on a single record         |

### 10.3 Findings

| Method | Path                  | Description                          |
| ------ | --------------------- | ------------------------------------ |
| GET    | `/findings`           | List findings with filters (severity, rule family, record type, review state) |
| GET    | `/findings/{id}`      | Finding detail with rule, evidence, review history |

### 10.4 Suggestions

| Method | Path                           | Description                          |
| ------ | ------------------------------ | ------------------------------------ |
| POST   | `/findings/{id}/suggest`       | Generate AI correction suggestion    |
| POST   | `/findings/{id}/retry`         | Retry with reviewer context          |
| GET    | `/findings/{id}/suggestions`   | All attempts for a finding           |

### 10.5 Review Actions

| Method | Path                           | Description                          |
| ------ | ------------------------------ | ------------------------------------ |
| POST   | `/findings/{id}/approve`       | Approve a finding's suggestion       |
| POST   | `/findings/{id}/reject`        | Reject                               |
| POST   | `/findings/{id}/needs-research`| Mark for research with reason        |
| POST   | `/findings/{id}/exception`     | Mark as exception with reason        |
| POST   | `/review/bulk`                 | Bulk action with eligibility check   |
| POST   | `/review/bulk/confirm`         | Confirm bulk action after preview    |

### 10.6 Dashboard

| Method | Path                           | Description                          |
| ------ | ------------------------------ | ------------------------------------ |
| GET    | `/dashboard/stats`             | Summary counts                       |
| GET    | `/dashboard/severity`          | Findings breakdown by severity       |
| GET    | `/dashboard/rule-families`     | Findings by rule family + top errors |
| GET    | `/dashboard/review-progress`   | Accepted/rejected/pending counts     |

### 10.7 Chat

| Method | Path                  | Description                          |
| ------ | --------------------- | ------------------------------------ |
| POST   | `/chat`               | Conversational query (SSE streaming) |
| GET    | `/chat/history`       | Chat session history                 |

### 10.8 Web Search

| Method | Path                  | Description                          |
| ------ | --------------------- | ------------------------------------ |
| POST   | `/web-search`         | Search for source evidence           |

---

## 11. DynamoDB Table Design

### 11.1 Tables

| Table              | PK                 | SK                          | Purpose                          |
| ------------------ | ------------------ | --------------------------- | -------------------------------- |
| `records`          | `record_id`        | —                           | Pre-loaded metadata records      |
| `findings`         | `finding_id`       | —                           | Validation findings              |
| `findings-by-record` | `record_id`      | `finding_id`                | GSI: findings per record         |
| `suggestions`      | `finding_id`       | `attempt_number`            | AI suggestion attempts           |
| `audit_log`        | `finding_id`       | `timestamp#audit_id`        | Immutable decision history       |
| `chat_sessions`    | `session_id`       | `message_index`             | Chat conversation history        |

### 11.2 GSIs for Dashboard Queries

| GSI Name              | PK            | SK             | Use case                           |
| --------------------- | ------------- | -------------- | ---------------------------------- |
| `severity-index`      | `severity`    | `created_at`   | Findings by severity               |
| `rule-family-index`   | `rule_family` | `severity`     | Findings by rule family            |
| `review-state-index`  | `review_state`| `created_at`   | Pending / approved / rejected      |
| `record-type-index`   | `record_type` | `finding_id`   | Filter findings by record type     |

---

## 12. Seed Data

### 12.1 Composition (~1000 records)

| Record Type | Count | Notes                                                     |
| ----------- | ----- | --------------------------------------------------------- |
| Movie       | 350   | Mix of clean + errors in title, runtime, subtype, OAD     |
| Show        | 250   | Include type/subtype mismatches, missing networks         |
| Season      | 150   | Some orphan seasons, numbering issues                     |
| Episode     | 250   | Duration anomalies, duplicate episode numbers, OAD issues |

### 12.2 Error Distribution

Approximately 30% of records should have at least one deliberate error:
- ~100 title issues (blank, too long, forbidden chars)
- ~80 duration issues (zero, negative, unparseable, implausible)
- ~60 OAD issues (invalid format, future dates)
- ~50 subtype issues (missing, invalid, mismatched)
- ~50 audio language issues (UNK, not in controlled list)
- ~40 required field gaps (missing release year, country, network)

Plus ~50 clean records per type to verify rules don't false-positive.

### 12.3 Seed Script

`seed_data/generate_seed.py` creates `records.json` with the above distribution.
`seed_data/load_seed.py` batch-writes records into DynamoDB.

---

## 13. MCP Server (PRD §8.10)

Exposed tools for programmatic access:

| Tool                      | Input                         | Output                              |
| ------------------------- | ----------------------------- | ----------------------------------- |
| `validate_record`         | record, ruleset_version       | findings[]                          |
| `explain_finding`         | finding_id                    | rule, standard citation, rationale  |
| `suggest_correction`      | finding_id, evidence?         | proposed value, confidence, provenance |
| `check_rule_alignment`    | rule_id                       | standard-match status + source link |

The MCP layer calls the same internal functions as the REST API. Same policy, grounding, and audit guarantees.

---

## 14. Hackathon Build Order

### Day 1 — Foundation

| #  | Task                                         | Depends on | Est.   |
| -- | -------------------------------------------- | ---------- | ------ |
| 1  | Project scaffold (FastAPI, Docker, deps)     | —          | 30 min |
| 2  | Pydantic data models (`src/models/`)         | —          | 1 hr   |
| 3  | DynamoDB table creation + seed data generator| #2         | 2 hr   |
| 4  | Rule engine framework (base_rule, registry, engine) | #2  | 2 hr   |
| 5  | First 3 rule families: Titles, Duration, Subtype | #4     | 3 hr   |
| 6  | Basic API routes: records, validate, findings| #3, #5     | 2 hr   |

**Day 1 deliverable:** Seed data loaded, rules running, findings queryable via API.

### Day 2 — AI + Review

| #  | Task                                         | Depends on | Est.   |
| -- | -------------------------------------------- | ---------- | ------ |
| 7  | Remaining P0 rules: OAD, Audio Language, Required Fields | #4 | 2 hr |
| 8  | AI suggestion generation + confidence scoring| #6         | 3 hr   |
| 9  | Chat agent with Bedrock (tool-use)           | #6, #8     | 3 hr   |
| 10 | Review workflow: approve/reject/bulk         | #6         | 2 hr   |
| 11 | Audit logging                                | #10        | 1 hr   |
| 12 | Web search integration                       | —          | 1.5 hr |
| 13 | Dashboard aggregation endpoints              | #6         | 1.5 hr |

**Day 2 deliverable:** Full backend functional — validate, explain, suggest, review, chat.

### Day 3 — Polish

| #  | Task                                         | Depends on | Est.   |
| -- | -------------------------------------------- | ---------- | ------ |
| 14 | P1 rules: Season/Episode, Genre (if time)   | #4         | 2 hr   |
| 15 | MCP server                                   | #8         | 2 hr   |
| 16 | Bug fixes, edge cases, error handling        | all        | 2 hr   |
| 17 | API documentation + README                   | all        | 1 hr   |
| 18 | Demo data tuning (ensure demo script works)  | all        | 1 hr   |

**Day 3 deliverable:** Polished backend ready for demo video.

---

## 15. Key Design Decisions

1. **No ingestion pipeline in POC.** Records are pre-loaded via seed script. The `POST /validate` endpoint triggers rule execution on demand.

2. **Rules as YAML, not hardcoded.** Adding a rule = adding YAML + a small handler function if the check needs custom logic. Pure config rules (presence, enum, range) need zero code.

3. **Deterministic ≠ AI.** Rule engine produces Pass/Fail/Not Evaluated. The 0–100 score only appears on AI-generated suggestions. These are never conflated.

4. **Suggestions are withheld below 65.** If the evidence is weak, the system says "Needs research" instead of guessing. This is a core safety principle.

5. **All approvals are staged.** Nothing writes back to any source system. The `review_state` field in DynamoDB is the only thing that changes.

6. **Chat is a client.** The chat agent uses the same API functions as the UI. It has no privileged access and cannot bypass audit logging.

7. **Audit is append-only.** Every action (approve, reject, suggest, retry, bulk) creates an immutable audit entry. No deletes, no overwrites.

---

## 16. Environment & Config

```env
# .env.example
AWS_REGION=us-east-1
DYNAMODB_TABLE_PREFIX=gn-validator-
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
WEB_SEARCH_API_KEY=           # Tavily or Brave
WEB_SEARCH_PROVIDER=tavily
RULE_CATALOG_VERSION=v0.3
CONFIDENCE_THRESHOLD=65
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO
```

---

## 17. Open Items

- [ ] Confirm which Bedrock model is available in the hackathon AWS account
- [ ] Confirm web search API provider and get API key
- [ ] Get the official controlled-value lists (languages, subtypes, genres) for rule validation
- [ ] Decide on a chat session persistence strategy (in-memory for POC vs. DynamoDB)
- [ ] Confirm DynamoDB provisioning mode (on-demand for hackathon)
- [ ] Align seed data schema with the actual NEd field names the frontend expects
