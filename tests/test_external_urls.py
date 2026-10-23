"""The explicit online validator uses the complete projected URL surface."""

from __future__ import annotations

import urllib.error
from types import SimpleNamespace

from learning_os.derive.validation import generated
from learning_os.derive.validation.generated import (
    ChecksGenerated,
    _collect_http_urls,
    _probe_external_url,
)


class _Response:
    def __init__(self, status: int):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _http_error(request, status: int):
    return urllib.error.HTTPError(
        request.full_url, status, "synthetic", {}, None
    )


def test_url_collection_recurses_without_accepting_unsafe_schemes():
    data = {
        "url": "https://example.org/main",
        "routes": [
            {"url": "http://example.org/lecture"},
            {"url": "javascript:alert(1)"},
            {"identifiers": {"mirror": "https://example.org/mirror"}},
        ],
    }
    assert _collect_http_urls(data) == {
        "https://example.org/main",
        "http://example.org/lecture",
        "https://example.org/mirror",
    }


def test_online_probe_falls_back_from_head_to_bounded_get():
    methods = []

    def opener(request, timeout):
        assert timeout == 10
        methods.append(request.get_method())
        if request.get_method() == "HEAD":
            raise _http_error(request, 404)
        assert request.headers["Range"] == "bytes=0-2047"
        return _Response(200)

    assert _probe_external_url("https://example.org/notebook", opener=opener) == (
        None,
        "HTTP 200",
    )
    assert methods == ["HEAD", "GET"]


def test_online_probe_distinguishes_access_control_from_link_rot():
    def forbidden(request, timeout):
        raise _http_error(request, 403)

    def gone(request, timeout):
        raise _http_error(request, 410)

    assert _probe_external_url("https://example.org/private", opener=forbidden) == (
        "access-controlled",
        "HTTP 403",
    )
    assert _probe_external_url("https://example.org/gone", opener=gone) == (
        "dead-link",
        "HTTP 410",
    )


def test_online_probe_keeps_transport_and_server_failures_advisory():
    def unavailable(request, timeout):
        raise _http_error(request, 503)

    def timeout(_request, timeout):
        raise TimeoutError("synthetic")

    assert _probe_external_url("https://example.org/busy", opener=unavailable) == (
        "transient",
        "HTTP 503",
    )
    assert _probe_external_url("https://example.org/slow", opener=timeout) == (
        "transient",
        "TimeoutError",
    )


def test_online_gate_blocks_rot_but_keeps_access_control_advisory(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        generated,
        "_loaded_http_urls",
        lambda _repo: {
            "https://example.org/gone",
            "https://example.org/private",
        },
    )
    monkeypatch.setattr(generated, "_projected_http_urls", lambda _repo: set())
    monkeypatch.setattr(
        generated,
        "_probe_external_url",
        lambda url: (
            ("dead-link", "HTTP 410")
            if url.endswith("/gone")
            else ("access-controlled", "HTTP 403")
        ),
    )

    class Harness(ChecksGenerated):
        def __init__(self):
            self.repo = SimpleNamespace(root=tmp_path)
            self.issues = []

        def _canonical_texts(self):
            return []

        def err(self, code, message, path=""):
            self.issues.append(("E", code, message, path))

        def warn(self, code, message, path=""):
            self.issues.append(("W", code, message, path))

    harness = Harness()
    harness.check_external_urls()

    assert [(severity, code) for severity, code, *_ in harness.issues] == [
        ("E", "URL-DEAD"),
        ("W", "URL-ACCESS-CONTROLLED"),
    ]


def test_online_audit_reads_link_urls_from_the_texts_already_read(
    mini_repo, monkeypatch
):
    """The URL sweep takes canonical Markdown from the validator's one read.

    It walked and read every note a second time; and a link with a title
    was invisible to it, as to the link check.
    """
    from pathlib import Path

    from learning_os.derive.validation.core import Validator
    from learning_os.store.loader import load_repo

    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    note.write_text(
        note.read_text(encoding="utf-8")
        + '\n[docs](https://example.org/titled "with a title")\n',
        encoding="utf-8")
    monkeypatch.setattr(generated, "_loaded_http_urls", lambda _repo: set())
    monkeypatch.setattr(generated, "_projected_http_urls", lambda _repo: set())
    probed: list[str] = []
    monkeypatch.setattr(generated, "_probe_external_url",
                        lambda url: probed.append(url) or (None, "HTTP 200"))
    validator = Validator(load_repo(mini_repo))
    validator._canonical_texts()
    reads: list[Path] = []
    original = Path.read_text

    def counted(self, *args, **kwargs):
        if self == note:
            reads.append(self)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counted)
    validator.check_external_urls()
    assert probed == ["https://example.org/titled"]
    assert reads == []
