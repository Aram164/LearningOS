"""`los dossier`: serve one unit's materialized context bundle.

Read-only. Resolves the unit's knowledge map, module source map, routes,
and manifest-digest evidence, then serves the cached semantic dossier when
its hashes still match — otherwise rebuilds and best-effort stores the
fresh bundle under ``generated/dossiers/``. The cache is a rebuilt view,
never canonical state: a store failure never fails the read, and a cache
file whose content fails its hashes is refused and rebuilt, never served.
"""
