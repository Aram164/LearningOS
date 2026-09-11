"""The transcript normaliser: what survives an auto-caption, and what does not.

Auto-captions are a rolling display, not a document. Each phrase is emitted two
or three times as the caption scrolls, and every word carries its own timing
tag. Stored raw, one 28-minute video is 255 KB (~64k tokens) of mostly repeated
text — worse to read than not having it. Normalised, the same video is 27 KB
with one timestamp per window, which is what makes a locator able to name a
span the way a book locator names pages.

These tests pin the two properties that matter: the spoken text survives in
order, and the scrolling artefacts do not.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "ingest_transcript",
    Path(__file__).resolve().parents[1] / "tools" / "ingest_transcript.py",
)
ingest = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ingest)


ROLLING = """WEBVTT
Kind: captions
Language: en

00:00:00.080 --> 00:00:02.790 align:start position:0%
 
the<00:00:00.240><c> world</c><00:00:00.640><c> of</c><00:00:01.360><c> algorithms</c>

00:00:02.790 --> 00:00:02.800 align:start position:0%
the world of algorithms
 

00:00:02.800 --> 00:00:04.789 align:start position:0%
the world of algorithms
is<00:00:03.200><c> vast</c><00:00:03.600><c> but</c><00:00:04.000><c> we</c>

00:00:35.000 --> 00:00:38.000 align:start position:0%
can often split them
"""


def test_word_timing_tags_are_stripped():
    segments = ingest.normalise_vtt(ROLLING)
    joined = " ".join(text for _, text in segments)
    assert "<c>" not in joined and "00:00:00.240" not in joined
    assert "the world of algorithms" in joined


def test_the_rolling_repeat_is_dropped_once():
    """The phrase is displayed three times and belongs in the text once."""
    segments = ingest.normalise_vtt(ROLLING)
    joined = " ".join(text for _, text in segments)
    assert joined.count("the world of algorithms") == 1


def test_spoken_order_survives():
    segments = ingest.normalise_vtt(ROLLING)
    joined = " ".join(text for _, text in segments)
    assert joined.index("world") < joined.index("vast") < joined.index("split")


def test_windows_are_the_addressing_unit():
    """Two cues 35s apart land in different windows; nearby ones merge."""
    segments = ingest.normalise_vtt(ROLLING, window=30)
    assert [at for at, _ in segments] == [0, 30]
    assert "can often split them" in segments[1][1]
    assert "can often split them" not in segments[0][1]


SPREAD = "WEBVTT\n\n" + "\n\n".join(
    f"00:00:{s:02d}.000 --> 00:00:{s + 4:02d}.000\nphrase {i}"
    for i, s in enumerate(range(0, 60, 5))
)


def test_a_smaller_window_addresses_more_finely():
    """The window is a choice about how precisely a locator can point."""
    coarse = ingest.normalise_vtt(SPREAD, window=30)
    fine = ingest.normalise_vtt(SPREAD, window=10)
    assert len(coarse) == 2 and len(fine) == 6
    assert [at for at, _ in fine] == [0, 10, 20, 30, 40, 50]
    # Nothing is lost by bucketing: every phrase survives at either width.
    assert " ".join(t for _, t in coarse) == " ".join(t for _, t in fine)


def test_empty_and_headerless_input_is_not_a_crash():
    assert ingest.normalise_vtt("") == []
    assert ingest.normalise_vtt("WEBVTT\n\n") == []
    # Text before any cue has no timestamp to belong to and is dropped.
    assert ingest.normalise_vtt("WEBVTT\n\nstray line\n") == []


@pytest.mark.parametrize("seconds, expected", [
    (0, "00:00"), (65, "01:05"), (750, "12:30"), (3600, "1:00:00"), (3725, "1:02:05"),
])
def test_stamp_reads_as_a_locator(seconds, expected):
    assert ingest.stamp(seconds) == expected


# ---- the guards --------------------------------------------------------------


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/@BrandonFoltz",
    "https://www.youtube.com/c/zedstatistics",
    "https://www.youtube.com/user/jbstatistics",
    "https://www.youtube.com/channel/UCtYLUTtgS3k1Fg4y5tAhLbw",
])
def test_channel_urls_are_recognised_as_unbounded(url):
    """A channel is a subscription, not a source's material."""
    assert ingest.CHANNEL.search(url)


@pytest.mark.parametrize("url", [
    "https://www.youtube.com/watch?v=h7apO7q16V0",
    "https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab",
    "https://youtu.be/h7apO7q16V0",
])
def test_bounded_urls_are_not_treated_as_channels(url):
    assert ingest.CHANNEL.search(url) is None
    assert ingest.YOUTUBE.search(url)


def test_urls_are_found_anywhere_in_a_source_record_without_duplicates():
    source = {
        "id": "source-demo",
        "url": "https://www.youtube.com/watch?v=abc12345678",
        "evaluations": [{"strengths": [
            "see https://www.youtube.com/watch?v=abc12345678 and "
            "https://youtu.be/xyz98765432, plus https://example.invalid/paper.pdf"]}],
    }
    assert ingest.youtube_urls(source) == [
        "https://www.youtube.com/watch?v=abc12345678",
        "https://youtu.be/xyz98765432",
    ]


def test_every_placement_hint_names_a_known_taxonomy_parent():
    """A hint that invents a folder would scatter the ADR-007 tree."""
    builder = (Path(__file__).resolve().parents[1]
               / "tools" / "build_materials_tree.py").read_text(encoding="utf-8")
    for slug, parent in ingest.PLACEMENT_HINT.items():
        assert f'"{parent}"' in builder, f"{slug} -> unknown parent {parent}"


def test_the_rendered_header_declares_what_the_file_is(tmp_path: Path):
    """A transcript must never read as authored knowledge."""
    text = ingest.render(
        {"id": "abc12345678", "title": "A Lecture", "duration": 1800,
         "webpage_url": "https://www.youtube.com/watch?v=abc12345678"},
        [(0, "first span"), (30, "second span")],
        source_id="source-demo", window=30)
    assert "Machine transcript of a third-party video" in text
    assert "Not authored knowledge and not a note" in text
    assert "- source: `source-demo`" in text
    assert "- duration: 30:00" in text
    assert "[00:00] first span" in text and "[00:30] second span" in text
