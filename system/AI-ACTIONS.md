# AI actions

AI actions are narrow, provider-independent transactions layered over the
canonical LearningOS core. A launcher never grants an assistant general vault
access. It selects a registered action, one exact target, one provider adapter,
and a locked snapshot. The core persists a reviewable request bundle before any
provider interaction.

## First vertical slice: `garden.shelve`

`garden.shelve` prepares one Markdown seed under `knowledge/garden/` for a
structured discussion. The original seed is immutable. Approved deliveries may
only:

- add an explicitly AI-derived transcription under
  `knowledge/garden/transcriptions/`;
- update the seed's separate operational state under
  `operations/ai-actions/garden-state/`;
- add a typed relationship to `operations/ai-actions/relationships.yaml`.

No action may read an external repository, overwrite the original artifact,
delete content, or write outside its capability allowlist. External code
context is supplied only by an explicitly scoped user task; it is never an
ambient AI-action capability.

## Manual-bundle workflow

```bash
python tools/los.py ai-action-list
python tools/los.py ai-action-prepare \
  --action-id garden.shelve \
  --target-kind garden-note \
  --target-id garden-note-example-attention-as-soft-knn \
  --provider manual-bundle \
  --expected-snapshot '<manifest snapshot id>'

python tools/los.py ai-action-import-delivery /path/to/approved-delivery
python tools/los.py ai-action-validate-delivery '<delivery id>'
python tools/los.py capability ai-action.delivery.apply \
  --payload-file /path/to/approved-apply-v2.json
```

Application is a GatewayEnvelopeV2-only write. Its approval kind is
`approved-delivery`, and its payload names the imported `delivery_id`, the
SHA-256 of the exact stored `delivery.yaml` bytes, and an `artifact_sha256`
mapping that covers every `artifact_ref` exactly. The envelope carries the
current canonical snapshot and one expected revision for every transaction
artifact. The approval subject is the standard Gateway V2 hash over that whole
intent. Calling `ai-action-apply-delivery` directly is deliberately refused.

Prepared bundles live under `operations/ai-actions/requests/`. An imported
response is copied into `operations/ai-actions/incoming/` first and only
published to `deliveries/` once it validates against the contract lock, target
checksum, provider identity, explicit approval and capability allowlist — a
rejected bundle never occupies a canonical-looking path. Successful application
is atomic, refreshes the deterministic manifest projection, and creates a
ReceiptV2 under `operations/transactions/` before success is reported.

## Delivery bundle format

An approved delivery is a directory containing `delivery.yaml` plus every
file its operations reference (no symlinks). `delivery.yaml` carries:

| Field | Meaning |
|---|---|
| `schema_version` | `1` |
| `id` | delivery id (non-empty exchange identifier, e.g. `ai-delivery-…`) |
| `type` | must be `ai-action-delivery` |
| `request_id` | the prepared request's id (`operations/ai-actions/requests/<id>/`) |
| `action_id` | must equal the request's `action_id` |
| `producer` | `{provider, adapter}`; only `adapter` is compared — `producer.adapter` must equal the **request's** `provider.adapter` (note the asymmetry: the delivery says `producer`, the request says `provider`) |
| `preconditions` | must equal the request's `preconditions` verbatim (copy from the request's `request.yaml`) |
| `approval` | `user_approved: true` (required) plus `approved_at` (when, by convention) — the recorded user approval of this exact delivery |
| `operations` | non-empty list; each names a `capability` from the request's `allowed-capabilities.json` (never a forbidden one) and, when set, a `target_id` equal to the request target |

Operation shapes per capability:

- `garden.add-transcription`: `artifact_ref` (required, path inside the
  bundle); `supersedes: transcription-<target-id>` required when the seed
  already has a transcription.
- `garden.update`: `patch` mapping with allowlisted fields only (e.g.
  `title`, `state`).
- `relationship.create`: `payload` with `id`, `from: {kind, id}`,
  `relation`, `to: {kind, id}`.
- `unit.material-synthesis.publish`: `artifact_ref` (required) pointing
  at one whole synthesis record.

Shape problems are reported together (up to twelve, then a count of the
rest), so one import round names everything wrong with the bundle;
freshness guards (target moved, original changed) still refuse
immediately. A complete minimal delivery:

```yaml
schema_version: 1
id: ai-delivery-example-001
type: ai-action-delivery
request_id: ai-request-example-001
action_id: garden.shelve
producer: {provider: manual, adapter: manual-bundle}
preconditions: # copied verbatim from the request's request.yaml
  snapshot_id: sha256:<prepared snapshot>
  artifact_revisions: {garden-note-example: 0}
approval: {user_approved: true, approved_at: '2026-09-25T12:00:00+00:00'}
operations:
  - capability: garden.add-transcription
    target_id: garden-note-example
    artifact_ref: artifacts/transcription.md
  - capability: garden.update
    target_id: garden-note-example
    patch: {title: Example, state: developing}
```

## Contracts

| Contract | Owns |
|---|---|
| `system/contracts/ai-actions/` | action registry: targets, mode, `status`, allowed and forbidden capabilities |
| `system/contracts/ai-adapters.yaml` | which providers have an available adapter, and which modes it serves |
| `system/contracts/capabilities.yaml` | the write scope each domain capability may touch |

All three are read by the core. The interface renders a projection of them and
enforces nothing on its own: `ai-action-prepare` refuses an unbuilt action
(`status: planned`) and a provider whose adapter is unavailable, whether the
request arrives from Obsidian or from the CLI.

## Staleness and supersession

Prepared-delivery validity is scoped to the target: a delivery is rejected when
the Garden seed or an original attachment changed after preparation, while an
unrelated edit does not force the discussion to be repeated. Application has a
second, stricter boundary. The approved Gateway V2 intent carries the current
whole-canonical snapshot, so any change after that final approval is refused.
The receipt records the enforced `snapshot_before` and resulting
`snapshot_after`.

Re-shelving a seed that already has an AI transcription requires the delivery to
name what it replaces:

```yaml
operations:
  - capability: garden.add-transcription
    target_id: garden-note-example-attention-as-soft-knn
    artifact_ref: artifacts/transcription.md
    supersedes: transcription-garden-note-example-attention-as-soft-knn
```

The receipt then records the replaced id under `metadata.superseded_ids`.

Before any canonical write the gateway runs a post-action scope check: every
destination must fall inside the `writes:` prefixes its capability declares in
`capabilities.yaml`. Gateway bookkeeping under `operations/ai-actions/` is
exchange state and is deliberately kept out of the canonical tree.
