# ADR-019: operator and developer documentation

Date: 2026-10-25. Status: accepted. Aram authorized completing the documentation
split and map in this session. This changes prose governance, not learner data.

## Decision

The corpus requires an audience independently of authority/status and declares
both operator and developer entry points. Operator task scopes and executable
procedure targets may reference only current binding operator/both documents.
The automatic Claude adapter routes by audience; its existing deeper policy
moves intact to OPERATOR-POLICY.md. Existing file paths and operator anchors stay stable; developer-only mechanics
move to one developer home with pointers at their former location.

Developer entry routes to a stable short code map, runtime/component diagrams,
four traced flows and layer-pure component pages. Each package module has exactly
one page owner. Static dependencies and reverse links derive from this checkout's
AST and the layer declaration; they are not runtime call evidence. Import-linter
retains authority over its complete contracts. Map freshness is tested in the
development suite, never in canonical validation, so a stale diagram does not
block a learner capture. Corpus integrity retains its existing fail-closed gate.

## Reasons and alternatives

An audience field preserves established references and executable transcripts;
moving whole documents would break those routes. A separate developer key keeps
the existing operator entry contract intact. A short map answers where to change
code; component pages hold detail without growing the required opening read.
Generated blocks avoid duplicate dependency facts. Runtime diagrams distinguish
applications and stores from Python package organization.

Section-level audience metadata and a second dependency contract were rejected:
task scopes already address sections, and import-linter already owns layering.
No stored-record schema, manifest shape, package boundary or learner meaning is
changed by this decision. The UI's internal documentation is a later phase.

## Verification

Corpus and scope negative tests enforce the audience boundaries. The system-map
tests exercise ownership, path/symbol references, generated-block drift and layer
direction. Existing documentation, import, code, validation and paired release
gates remain applicable. Symbol checks do not certify a flow's runtime coverage.
