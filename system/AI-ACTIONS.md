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

No action may read `Job/`, overwrite the original artifact, delete content, or
write outside its capability allowlist. A job-derived export requires explicit
operator confirmation and still does not grant access to the employer
repository.

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
python tools/los.py ai-action-apply-delivery '<delivery id>'
```

Prepared bundles live under `operations/ai-actions/requests/`. An imported
response is copied into `operations/ai-actions/incoming/` first and only
published to `deliveries/` once it validates against the contract lock, target
checksum, provider identity, explicit approval and capability allowlist — a
rejected bundle never occupies a canonical-looking path. Successful application
is atomic and creates the standard transaction receipt under
`operations/transactions/` before
the manifest projection is refreshed.

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

Staleness is scoped to the target. A delivery is rejected when the Garden seed
or an original attachment changed after preparation; unrelated edits elsewhere
in the repository do not invalidate prepared work. The repository fingerprint is
still recorded in the request and in the receipt's `snapshot_before` /
`snapshot_after` as provenance.

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
