# T05 — Workflow 27: the Master's promotion

**6/6 passed.**

## PASS — w27-1-program-facts

*Intent:* Step 1 of workflow 27: create the programme and semester facts.

**program_written**

```
true
```

**validate_exit**

```
0
```

**validate_errors**

```
[]
```

## PASS — w27-2-publish-catalog

*Intent:* Publish the prospective catalog into quarantine.

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**apply_error**

```
null
```

**apply_stderr**

```

```

**catalog_on_disk**

```
true
```

**quarantine_is_tracked**

```
true
```

**note**

```
the quarantine is a Git-tracked partition; the catalog is published through an operator-approval capability with no gesture admission
```

## PASS — w27-3-publish-comparison

*Intent:* Publish the reviewed source comparison.

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**apply_error**

```
null
```

**apply_stderr**

```

```

**comparison_on_disk**

```
true
```

**note**

```
the comparison binds the candidate set by checksum; the request_id and delivery_id are free strings, so the binding proves *which* candidates were compared, not who compared them
```

## PASS — w27-4-promote-the-module

*Intent:* Promote the candidate into the live curriculum, as the agent.

**check_exit**

```
0
```

**package_sha256**

```
sha256:5560c22444ea0f693cf2e2b0c1235a2a385c5205af3cc09f1644a4f14972cd80
```

**seal_exit**

```
0
```

**apply_exit**

```
0
```

**apply_error**

```
null
```

**apply_stderr**

```

```

**module_promoted**

```
true
```

**evidence_url**

```
https://nonexistent.invalid/probe/module-catalog
```

**evidence_url_resolves**

```
false
```

**note**

```
the verification evidence URL is a shape check: `^https://` and a date ordering. Nothing fetches it.
```

## PASS — w27-5-after-the-promotion

*Intent:* What does the curriculum look like afterwards?

**validate_exit**

```
0
```

**validate_errors**

```
[]
```

**module_list_mentions_probe**

```
true
```

**status_head**

```
Learning OS v3 · learning_os v3.2.0 · /Users/aramaljanadi/los-canvas/worlds/t05/LearningOS/repository
  notes 2 · concepts 2 · relations 1 · sources 2
  programs 2 · modules 2 (1 enrolled) · projects 1 · units 3 · study maps 1 · workspaces 2 active (0 standing), 0 archived
  inbox 2 top-level · 3 files · garden 1 · reviewed 0/2 · evidence 0/2
  exam: 2026-10-09 — Demo Module (Termin 2)
  validation: OK · 9 warning(s), visible and nonblocking (`make warnings` for the delta)
  human home page: gen
```

## PASS — w27-6-stale-verification-refused

*Intent:* Verification evidence older than as_of must refuse.

**seal_exit**

```
2
```

**seal_stderr**

```
seal_envelope: Master Planning promotion refused: verification.evidence[0].verified_on is stale (49 days old; maximum is 30); fix the payload and seal again
```

**apply_exit**

```
2
```

**note**

```
evidence dated before `as_of` must be refused
```
