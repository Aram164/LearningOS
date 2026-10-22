"""Fault proofs for shared plan guards unreachable from the rich-world inputs.

The real public handler first assembles a valid package. Inject a malformed
internal handoff or collaborator failure at that boundary, then require the
actual pipeline witness and an unchanged canonical tree. Publicly expressible
refusals remain scenarios rather than being excused by these proofs.
"""

import copy


def prove(mini_repo, tmp_path, monkeypatch, *, site):
    import arch_effects
    import scenario_harness as harness
    import test_scenarios_zz_refusal_sites as a9

    import learning_os.app.handlers.plan as plan

    operation, slug = site.rsplit('.', 1)
    case_id = 'import-success' if operation == 'module.plan.import' else 'revise-success'
    ctx = a9._a9_world(operation, case_id, tmp_path)
    doc = harness.load_case_file(a9.CASES_DIR / f'{operation}.yaml')
    case = next(case for case in doc['cases'] if case['id'] == case_id)
    payload = harness._substitute(copy.deepcopy(case['request']), ctx)
    if payload.get('file'):
        payload['file'] = str((ctx.root / payload['file']).resolve())
    expected_exit = 2
    original = plan._execute_plan_import

    def boom(error):
        def fail(*args, **kwargs):
            raise error
        return fail

    def handoff(context, request, **kwargs):
        nonlocal expected_exit
        package = copy.deepcopy(kwargs['package'])
        request = dict(request)
        unit = copy.deepcopy(context.repo().units['unit-demo-l01'].data)
        study_map = copy.deepcopy(next(sm.data for sm in context.repo().study_maps.values()
                                     if sm.unit_id == 'unit-demo-l01'))
        if slug == 'module-patch-escape':
            package['module_patch'] = {'id': 'module-other'}
        elif slug in ('source-patches-nonlist', 'units-nonlist', 'workspace-updates-nonlist'):
            field = {'source-patches-nonlist': 'source_patches', 'units-nonlist': 'units',
                     'workspace-updates-nonlist': 'workspace_updates'}[slug]
            package[field] = 'internal corruption'
        elif slug == 'source-map-foreign':
            package['source_map'] = {'module_id': 'module-other'}
        elif slug in ('source-patch-unknown', 'source-patch-splice'):
            package['source_patches'] = [{'id': 'source-nope' if slug.endswith('unknown')
                                          else 'source-demo-book'}]
            if slug.endswith('splice'):
                monkeypatch.setattr(plan, '_replace_registry_list_record', boom(ValueError('a9 splice fault')))
        elif slug in ('unit-invalid', 'map-foreign-unit', 'stage-note-escape'):
            package['units'] = [{'unit': unit, 'study_map': study_map}]
            if slug == 'unit-invalid':
                unit['module_id'] = 'module-other'
            elif slug == 'map-foreign-unit':
                study_map['unit_id'] = 'unit-other'
            else:
                study_map['stages'][0]['working_note'] = 'work/inbox/escape.md'
        elif slug in ('synthesis-unknown-unit', 'synthesis-destination'):
            package['material_syntheses'] = [{'unit_id': 'unit-nope' if slug.endswith('unknown-unit')
                                              else 'unit-demo-l01', 'dossier': {'id': 'a9-dossier'}}]
            if slug == 'synthesis-destination':
                monkeypatch.setattr(plan, 'synthesis_destination', boom(plan.MaterialSynthesisError('a9 destination fault')))
        elif slug in ('workspace-not-joined', 'workspace-splice'):
            package['workspace_updates'] = [{'id': 'workspace-nope' if slug.endswith('not-joined')
                                             else 'workspace-demo', 'sections': {'Next Action': 'probe'}}]
            if slug.endswith('splice'):
                monkeypatch.setattr(plan, '_replace_h2_section', boom(ValueError('a9 section fault')))
        elif slug in ('ordering-preflight-failed', 'routing-preflight-failed'):
            name = '_module_plan_ordering_problems' if slug.startswith('ordering') else '_module_plan_routing_problems'
            monkeypatch.setattr(plan, name, lambda *a, **k: ['a9 injected preflight fault'])
            expected_exit = 1
        elif slug in ('lineage-preflight-failed', 'lineage-admission-failed'):
            monkeypatch.setattr(plan, '_phaseB_validate', lambda *a, **k:
                                (['a9 lineage fault'], [], {}, {}) if slug.endswith('preflight-failed')
                                else ([], ['a9-changed'], {}, {}))
            if slug.endswith('admission-failed'):
                monkeypatch.setattr(plan, '_phaseB_ledger_text', boom(plan.LineageError('a9 ledger fault')))
            else:
                expected_exit = 1
        elif slug == 'noop-revision':
            kwargs['minimal_writes'] = True
            monkeypatch.setattr(plan, '_drop_unchanged_writes', lambda writes: {})
        elif slug in ('staged-outside-package', 'staged-unavailable'):
            request['staged_basis'] = 'unit-nope' if slug.endswith('outside-package') else 'unit-demo-l01'
            if slug == 'staged-unavailable':
                monkeypatch.setattr(plan, 'current_unit_material_basis', boom(OSError('a9 material read fault')))
        elif slug in ('validation-crash', 'validation-preflight-failed', 'inventory-preflight-failed', 'report-out-failed'):
            request['check'] = True
            if slug == 'validation-crash':
                monkeypatch.setattr(plan, '_module_plan_validation_errors', boom(ValueError('a9 validator fault')))
            elif slug == 'validation-preflight-failed':
                monkeypatch.setattr(plan, '_module_plan_validation_errors', lambda *a, **k: ['a9 validation fault'])
                expected_exit = 1
            elif slug == 'inventory-preflight-failed':
                monkeypatch.setattr(plan, '_observed_material_binding', lambda *a, **k: (None, ['a9 inventory fault']))
                expected_exit = 1
            else:
                kwargs['report_out'] = str(tmp_path / 'report.json')
                monkeypatch.setattr(plan, '_save_check_report_and_compact', lambda *a, **k: (None, (2, 'a9 report write fault')))
        else:
            raise AssertionError(f'unhandled proof {site}')
        kwargs['package'] = package
        return original(context, request, **kwargs)

    if slug.startswith('promotion-'):
        from types import SimpleNamespace

        payload = copy.deepcopy(next(c for c in doc['cases'] if c['id'] == 'promotion-refused')['request'])
        original_promotion = plan._master_promotion_import
        digest = 'sha256:' + '1' * 64
        monkeypatch.setattr(plan, 'prepare_master_promotion', lambda *a: SimpleNamespace(
            package_sha256=digest, expected_revisions={'module-demo': 99}))
        monkeypatch.setattr(plan, '_master_promotion_preflight', lambda *a, **k: [])

        def promotion(context, request):
            nonlocal expected_exit
            request = dict(request)
            if slug == 'promotion-needs-approval':
                assert request['approve']
                request.pop('approve')
            elif slug == 'promotion-needs-snapshot':
                assert request['expected_snapshot']
                request.pop('expected_snapshot')
            elif slug == 'promotion-hash-mismatch':
                request['package_sha256'] = 'sha256:' + '2' * 64
                expected_exit = 3
            elif slug in ('promotion-preflight-failed', 'promotion-revisions-mismatch'):
                request['package_sha256'] = digest
                if slug == 'promotion-preflight-failed':
                    monkeypatch.setattr(plan, '_master_promotion_preflight', lambda *a, **k: ['a9 preflight fault'])
                    expected_exit = 1
                else:
                    expected_exit = 3
            return original_promotion(context, request)
        monkeypatch.setattr(plan, '_master_promotion_import', promotion)
    elif slug == 'assembled-contract-failed':
        monkeypatch.setattr(plan, '_module_plan_contract_problems', lambda *a, **k: ['a9 assembled package fault'])
        if operation == 'module.plan.import':
            # The ordinary handler validates the source contract before
            # compact assembly. Let that first check pass, fail the second.
            calls = []
            def assembled_only(*a, **k):
                calls.append(1)
                return [] if len(calls) == 1 else ['a9 assembled package fault']
            monkeypatch.setattr(plan, '_module_plan_contract_problems', assembled_only)
            def compact(context, request, **kwargs):
                return plan._compact_plan_import(context, request, context.root, kwargs['source'],
                                                 kwargs['package_bytes'], kwargs['package'])
            monkeypatch.setattr(plan, '_execute_plan_import', compact)
            monkeypatch.setattr(plan, '_assemble_compact_module_revision',
                                lambda repo, module_id, revision: (revision, []))
    elif slug in ('reviewed-needs-file', 'needs-file-or-record'):
        from dataclasses import replace
        entry = a9.REGISTRY[operation]
        def changed_request(context, request):
            request = dict(request)
            if slug == 'needs-file-or-record':
                request.pop('file', None)
                request.pop('record', None)
            else:
                request['apply_reviewed_sha256'] = request['file_sha256']
                source = request.pop('file')
                content = (ctx.root / source).read_bytes()
                monkeypatch.setattr(plan, '_read_content_bound_file', lambda *a, **k: (source, content))
            return entry.handler(context, request)
        monkeypatch.setitem(a9.REGISTRY, operation, replace(entry, handler=changed_request))
    else:
        monkeypatch.setattr(plan, '_execute_plan_import', handoff)

    before = arch_effects.capture_tree(ctx.root)
    outcome, lines = a9._a9_run_gateway(ctx.root, operation, payload, case.get('artifact_ids', []),
                                      'a9-helper-' + slug, tmp_path, monkeypatch)
    assert arch_effects.capture_tree(ctx.root) == before
    assert outcome.exit_code == expected_exit
    assert len(lines) == 1 and lines[0]['site'] == site, (site, lines)
    assert lines[0]['operation'] == operation
    assert lines[0]['class'] in ('WriteRefused', 'RevisionConflict')
