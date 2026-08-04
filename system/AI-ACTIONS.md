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
- add a typed relationship to `knowledge/relationships.yaml`.

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

Prepared bundles live under `operations/ai-actions/requests/`. Imported
responses are validated against the contract lock, target checksum, expected
snapshot, provider identity, explicit approval and capability allowlist.
Successful application is atomic and creates a receipt under
`operations/ai-actions/receipts/` before the manifest projection is refreshed.

The action registry is `system/contracts/ai-actions/`; the shared capability
contract is `system/contracts/capabilities.yaml`.
