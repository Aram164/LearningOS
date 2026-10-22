# Every new capability moves the fixture's pinned fingerprint in ~70 files

Task: add the governed program-semester update capability
(`program.semester.update`) and keep the recorded surfaces green.

Observed: the scenario corpus and the procedure transcripts pin the
rich-world fixture's canonical fingerprint as a literal, and that
fingerprint covers `system/schema` and `system/contracts`. One new
request schema therefore moved the pin in 7 case files, 10 case data
files, 26 procedure transcripts and 23 recorded scenarios; the pinned
envelopes also carry an approval digest computed over the fingerprint,
so those had to be recomputed as well or the case refuses with
`approval subject does not match the current capability intent`. The
same pass ran after `module.create`, in commit `b560390f` ("bring the
recorded surfaces and transcripts back to the new tree").

Impact: every capability costs an hour of mechanical re-pinning across
roughly seventy files, and a missed pin fails a scenario or a transcript
rather than anything about the capability under test. The safety benefit
that pass does provide stands: the recordings are characterization
evidence, so a changed tree legitimately changes what they record.

Smallest improvement to investigate: let the harness substitute the live
fixture fingerprint where a case pins it, and normalize the fingerprint
in the recorded free text the way it already normalizes a snapshot found
under a `snapshot`-named key. Retain the byte-for-byte comparison of the
recordings and the transcripts' real snapshot.

Filed on 2026-10-22: [LearningOS #7](https://github.com/Aram164/LearningOS/issues/7),
with the file lists, the reproduction, the scope limit and the acceptance
criteria.
