# WHY-REDESIGN.md

# Why Learning OS v3 Exists

## Purpose

This document explains **why the repository is being redesigned**. It is
intentionally separate from the architecture specification.

The goal is not to justify individual design decisions, but to preserve
the reasoning that motivated the redesign so future changes can be
evaluated against the original objectives.

------------------------------------------------------------------------

# The Original Problem

The repository was never intended to be a note-taking application.

It was built to support long-term technical learning.

The primary challenge was never remembering facts. It was organizing
understanding across lectures, books, papers, implementations, projects,
and conversations.

As the repository grew, it became increasingly successful at storing
knowledge but increasingly expensive to maintain.

The redesign is therefore driven by reducing organizational complexity
while preserving everything that makes the repository valuable.

------------------------------------------------------------------------

# What Worked

Several ideas proved successful and must be preserved:

-   Durable knowledge should be separated from temporary semester work.
-   User-written synthesis is the most valuable knowledge artifact.
-   Retrieval should begin from concepts rather than file locations.
-   Sources should be evaluated in context rather than merely collected.
-   Relationships between concepts are as valuable as the notes
    themselves.
-   Git should preserve the evolution of understanding.

------------------------------------------------------------------------

# Why a Redesign Became Necessary

The previous architecture accumulated several structural problems.

## Manual synchronization

Indexes, metadata and organizational files required manual updates.

This created multiple sources of truth that gradually drifted apart.

## Workflow-driven structure

The repository increasingly reflected semesters, lectures and
operational workflows instead of the underlying knowledge.

Concepts naturally cross those boundaries.

## Over-specialized artifacts

Different learning situations were forced into the same organizational
templates even when they did not fit naturally.

## Growing complexity

As more modules and projects were added, navigation and maintenance
became a larger burden than intended.

The repository gradually optimized for organization instead of
understanding.

------------------------------------------------------------------------

# Design Philosophy of Learning OS v3

The redesign follows a simple principle:

> The repository exists to organize knowledge, not files.

Only durable knowledge should become canonical.

Everything else should either be temporary, generated automatically, or
computed on demand.

The repository should minimize the number of canonical objects while
maximizing retrieval quality.

------------------------------------------------------------------------

# The Desired End State

Learning OS v3 should allow the user to spend cognitive effort on
understanding rather than repository maintenance.

The permanent knowledge model is intentionally small:

-   Notes
-   Concepts
-   Sources
-   Concept Relations

Active work happens inside temporary workspaces.

Indexes, manifests, reports and navigation views are generated.

Agent-produced planning artifacts remain disposable.

------------------------------------------------------------------------

# Success Criteria

The redesign is successful if:

-   adding new knowledge requires minimal organizational decisions;
-   every canonical fact has a single owner;
-   generated artifacts can be recreated at any time;
-   retrieval depends on concepts rather than folders;
-   the repository remains understandable after many years of growth;
-   Claude automates mechanics without silently changing user meaning.

The architecture should remain simple enough that future complexity must
justify itself before becoming permanent.

------------------------------------------------------------------------

# Revision Note (v3.1, 2026-07-16)

The objectives above are unchanged. The consolidated v3.1 specification adds
two pragmatic admissions the original model lacked: administrative facts
(module records) and cross-workspace coordination are real, durable, and
deserve owned homes — otherwise they leak back into notes and hand-maintained
status files, recreating the drift this redesign exists to eliminate.
