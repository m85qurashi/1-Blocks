# Delivery C Architecture — Platform Integration

```mermaid
flowchart LR
    TO[TaskObject] --> CB[Context Bundle Builder]
    CB -->|Bundle| INT[Integration Service]
    INT -->|Blueprint slice| BB[Block Service]
    BB -->|Verification artifacts| AR[Artifact Registry]
    AR -->|Immutable links| TO
    INT --> CLI[Unified CLI/CI]
```

**Key Concepts**
- Integration Service maps Flow outputs (TaskObject) to block artifacts via context bundles.
- Artifact registry keeps SRS drafts, reviews, test reports with hash-based links, enabling replayable runs.
- CLI/CI uses Integration Service to drive end-to-end Basel-I commands.
