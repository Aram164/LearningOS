# Stage Working Notes

## Mental Models

### Tool model

SSH authenticates a server to the client with host keys and usually authenticates the user with public-key credentials; it can carry a shell, one command, file transfer, and forwarded connections. tmux owns persistent server-side sessions independent of one terminal connection.

### Working practice

verify host identity, use scoped keys and config aliases, quote with awareness of local versus remote parsing, and keep long work in named sessions.

### Job relevance

remote servers, CI runners, and development hosts should behave predictably when the network disconnects.

### Safety rule

never disable host-key checking as a convenience and never copy private keys to a server.

### Failure mode

confusing authentication direction, exposing forwarded services broadly, or assuming nohup/tmux changes program correctness.

## Read-only Anchor

Read-only planning for Stratum-related remote work: document the approved host alias, repository path, environment activation, and reconnect procedure without exposing hostnames, usernames, keys, tokens, or internal URLs in the plan. Do not initiate new external access from this exercise.

## Component


## Verified Against



## External Code Boundary

Any Stratum paths above refer to the sibling `semestercontext/Stratum/` worktree. They are optional read-only learning anchors: LearningOS does not index, validate, manage, or write that codebase.
