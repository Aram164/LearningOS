"""Adversarial controls for A8 classification, extraction and parser evidence."""
from __future__ import annotations

import argparse
import json

import pytest
import test_arch_doc_commands as lint

import los


@pytest.fixture
def products(tmp_path, monkeypatch):
    monkeypatch.setattr(lint, "ROOT", tmp_path)
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "demo.py").write_text("# synthetic parser target\n")
    demo = argparse.ArgumentParser()
    demo.add_argument("item")
    demo.add_argument("--count", type=int)
    demo.add_argument("--mode", choices=["first", "second"])
    return {"los": los.build_parser(), "demo": demo}


def scan(text, products):
    rows = lint._evaluate(lint._document_rows(text), products)
    return [row for row in rows if row.get("reason")], rows


def declaration(text, kind="command"):
    return '<!-- los:reference ' + json.dumps({"kind": kind, "text": text}) + ' -->\n'


@pytest.mark.parametrize("command", [
    "los goal", "los capability", "los source-revise --check",
    "los collection-entry-revise --check", "los unknown-command",
    "los inspect --not-an-option", "los observe req --activity x --result typo",
    "tools/demo.py item --count nope", "tools/demo.py item --mode typo",
    "python tools/los.py", "tools/demo.py", "los capability x --payload-file",
])
def test_malformed_full_examples_always_fail(command, products):
    failures, _ = scan('```bash\n' + command + '\n```', products)
    assert failures, command


@pytest.mark.parametrize("command", [
    "los goal", "los capability", "los source-revise --check",
    "los collection-entry-revise --check", "tools/demo.py --mode first",
])
def test_only_explicit_references_complete_required_metadata(command, products):
    failures, rows = scan(declaration(command) + 'The API is `' + command + '`.', products)
    assert not failures, failures
    row = next(row for row in rows if row['category'] == 'reference')
    assert row['original_argv'] != row['synthesized_argv']
    if command != 'tools/demo.py --mode first':
        assert scan('The API is `' + command + '`.', products)[0]


@pytest.mark.parametrize("command,kind", [
    ("los unknown-command", "command"),
    ("los capability --typo", "command"),
    ("tools/demo.py --mode typo", "command"),
    ("tools/demo.py --count nope", "command"),
    ("tools/demo.py --mode", "command"),
    ("los goal --help", "command"),
    ("los goal real-goal", "command"),
])
def test_reference_declarations_cannot_hide_invalid_supplied_tokens(command, kind, products):
    assert scan(declaration(command, kind) + 'The API is `' + command + '`.', products)[0]


def test_option_reference_is_distinct_from_missing_option_value(products):
    fragment = 'los source-feedback --resource-id'
    assert not scan(declaration(fragment, 'option') + 'The option is `' + fragment + '`.', products)[0]
    assert scan(declaration(fragment) + 'The option is `' + fragment + '`.', products)[0]
    assert scan('Run `' + fragment + '`.', products)[0]


@pytest.mark.parametrize('prefix', ['Run ', 'Execute ', 'Invoke ', 'Use ', 'Run this command: ', 'For example: '])
def test_execution_prose_cannot_be_downgraded(prefix, products):
    fragment = 'los capability'
    failures, _ = scan(declaration(fragment) + prefix + '`' + fragment + '`.', products)
    assert failures


def test_annotation_scope_and_shape_are_fail_closed(products):
    for text in [
        declaration('los goal') + 'There is no command here.',
        declaration('los goal') + '`los goal` and `los goal`.',
        declaration('los goal') + declaration('los goal') + '`los goal`.',
        declaration('los goal') + '```bash\nlos goal\n```',
        '<!-- los:reference {"kind":"command", "text":"los goal", "ignore":true} -->\n`los goal`.',
        '<!-- los:reference not-json -->\n`los goal`.',
    ]:
        assert scan(text, products)[0], text


@pytest.mark.parametrize('separator', [' | ', ' && ', ' || ', '; '])
def test_every_executable_shell_stage_is_checked(separator, products):
    assert scan('```bash\nlos status' + separator + 'los unknown-command\n```', products)[0]
    assert not scan('```bash\nlos status' + separator + 'los validate\n```', products)[0]


@pytest.mark.parametrize('command', [
    'eval "$(los unknown-command)"',
    'A=$(los unknown-command) && echo "$A"',
    'echo "$(echo "$(los unknown-command)")"',
    "sh -c 'los unknown-command'",
])
def test_executed_substitutions_and_static_shell_scripts_are_checked(command, products):
    assert scan('```bash\n' + command + '\n```', products)[0]


@pytest.mark.parametrize('command', [
    "echo '$(los unknown-command)'", 'echo "\\$(los unknown-command)"',
    'echo "los unknown-command"', "A='los unknown-command' && echo \"$A\"",
    'python -c \'print("los unknown-command")\'',
    'echo \'{"hint":"tools/demo.py --bad"}\'',
])
def test_quoted_nonexecuted_data_is_not_an_invocation(command, products):
    failures, rows = scan('```bash\n' + command + '\n```', products)
    assert not failures, failures
    assert not any(row['category'] == 'invocation' for row in rows)


def test_scrut_output_and_input_are_separate_with_continuations(products):
    valid = '```scrut\n$ los inspect \\\n  THING\nlos unknown-command --bad\n```'
    assert not scan(valid, products)[0]
    invalid = '```scrut\n$ los inspect \\\n --bad\nlos status\n```'
    assert scan(invalid, products)[0]
    rows = scan(valid, products)[1]
    assert any(row['category'] == 'scrut-output' for row in rows)
    assert any(row['category'] == 'invocation' for row in rows)


def test_tool_reference_existence_and_actual_invocation(products):
    assert not scan('The file is `tools/demo.py`.', products)[0]
    assert scan('The file is `tools/unknown.py`.', products)[0]
    assert scan('```bash\npython tools/demo.py\n```', products)[0]


def test_explicit_typed_placeholders_do_not_repair_literal_values(products):
    assert not scan('`tools/demo.py ITEM --count COUNT --mode <first|second>`', products)[0]
    assert not scan('`los unit-plan-revise UNIT --file FILE --apply-reviewed-sha256 sha256:REVIEWED_HASH --review-report REPORT`', products)[0]
    assert scan('`tools/demo.py ITEM --mode <first|typo>`', products)[0]
    assert scan('`tools/demo.py ITEM --count nope`', products)[0]
    assert scan('`los unit-plan-revise UNIT --file FILE --apply-reviewed-sha256 sha256:bad --review-report REPORT`', products)[0]
    assert scan('`tools/demo.py ITEM --mode <first`', products)[0]


def test_output_annotation_preserves_actual_argv_and_quoted_arrows(products):
    assert not scan('```bash\nlos status → output\n```', products)[0]
    assert scan('```bash\nlos status --bad → output\n```', products)[0]
    assert not scan('```bash\nlos inspect "a → b"\n```', products)[0]


def test_expansion_macro_requires_exact_shape_and_guarded_transcript(products, tmp_path):
    transcript = tmp_path / 'system/procedures/start-here.md'
    transcript.parent.mkdir(parents=True)
    transcript.write_text('$ los plan-edit-context UNIT --brief --expected-snapshot SNAP\n')
    def macro(span, path='system/procedures/start-here.md'):
        return '<!-- los:macro ' + json.dumps({'text': span, 'transcript': path}) + ' -->\n`' + span + '`'
    assert not scan(macro('python tools/los.py <expansion>'), products)[0]
    assert scan('`python tools/los.py <expansion>`', products)[0]
    assert scan(macro('python tools/los.py <expansion> --bad'), products)[0]
    assert scan(macro('python tools/los.py <unknown>'), products)[0]
    assert scan(macro('python tools/los.py <expansion>', 'system/procedures/missing.md'), products)[0]


def test_compact_documented_option_alternatives_check_every_branch(products):
    assert not scan('`los goal GOAL_ID --reject|--defer|--close`', products)[0]
    assert scan('`los goal GOAL_ID --reject|--unknown`', products)[0]


def test_generated_markers_and_nontarget_markup_are_not_a8_annotations(products):
    assert not scan('<!-- los:generated name=capability-count -->\ncounts\n<!-- /los:generated -->', products)[0]
    assert not scan('A literal `` `#tags` `` and `a < b`.', products)[0]


def test_embedded_and_quoted_explicit_metavariables(products):
    assert not scan('`los inspect "<record id>"`', products)[0]
    assert not scan('`los capability capture.create --payload-file <out>/envelope.json`', products)[0]
    assert scan('`los capability capture.create --payload-file <out/envelope.json`', products)[0]


def test_inline_tool_invocation_context_still_requires_operands(products):
    assert scan('Run `tools/demo.py`.', products)[0]


def test_original_substitution_argv_stays_visible(products):
    failures, rows = scan('```bash\nlos inspect "$(echo demo)"\n```', products)
    assert not failures
    row = next(row for row in rows if row['category'] == 'invocation')
    assert row['original_argv'] == ['inspect', '$(echo demo)']
    assert row['synthesized_argv'] != row['original_argv']


@pytest.mark.parametrize('command', ['if true; then los unknown-command; fi', 'sudo los unknown-command', '(los unknown-command)', '{ los unknown-command; }', 'exec los unknown-command', 'env -S "los unknown-command"', 'command -p los unknown-command'])
def test_unsupported_target_bearing_shell_syntax_fails_explicitly(command, products):
    failures, _ = scan('```bash\n' + command + '\n```', products)
    assert failures
    assert any('unsupported target-bearing' in row['reason'] for row in failures)


def test_macro_transcript_cannot_traverse_outside_procedure_root(products, tmp_path):
    outside = tmp_path / 'system/outside.md'
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text('$ los inspect X --expected-snapshot SNAP\n')
    (tmp_path / 'system/procedures').mkdir(exist_ok=True)
    declaration = '<!-- los:macro ' + json.dumps({
        'text': 'python tools/los.py <expansion>',
        'transcript': 'system/procedures/../outside.md',
    }) + ' -->\n`python tools/los.py <expansion>`'
    assert scan(declaration, products)[0]


@pytest.mark.parametrize('relative', ['extra.txt', 'nested/extra.md'])
def test_macro_transcript_must_be_in_actual_runner_population(products, tmp_path, relative):
    transcript = tmp_path / 'system/procedures' / relative
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text('$ los inspect X --expected-snapshot SNAP\n')
    annotation = '<!-- los:macro ' + json.dumps({
        'text': 'python tools/los.py <expansion>',
        'transcript': 'system/procedures/' + relative,
    }) + ' -->\n`python tools/los.py <expansion>`'
    assert scan(annotation, products)[0]
