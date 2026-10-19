# Stage Working Notes

## Mental Models

### Tool model

security begins with assets, actors, trust boundaries, capabilities, and threats; entropy, hashes, key-derivation, symmetric encryption, public-key encryption/signatures, and authenticated channels solve different problems. SSH, Git signatures, TLS, password managers, and secret stores compose these primitives under operational assumptions.

### Working practice

minimize privilege and secret lifetime, verify identities, use established protocols/libraries, rotate exposed credentials, keep dependencies updated, and plan incident response.

### Job relevance

source access, package publication, remotes, CI, containers, and coding agents all cross credential and data boundaries.

### Safety rule

this stage teaches use and reasoning, not cryptographic design—never invent crypto or test attacks against systems without authorization.

### Failure mode

confusing hashing with encryption, public keys with secrets, signatures with confidentiality, or deletion from Git with credential revocation.

## Read-only Anchor

Read-only threat model for the Stratum development path: repository, laptop, remote host, package indexes, CI, artifacts, logs, and agent provider. Name secret types and trust boundaries without revealing values, internal endpoints, or operational details.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
