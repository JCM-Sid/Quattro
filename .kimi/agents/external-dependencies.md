---
name: "external-dependencies"
description: "Local-first policy and explicit exceptions for external services"
tools: ["read_file", "edit_file", "bash"]
---

# external-dependencies

**Tier:** pack  
**Pack:** local-first  
**Modes:** all

# External dependencies

## Applicability

Rule for projects that must run primarily on local files and explicitly control their external dependencies. Disable it if this policy does not fit the project.

## Principle

No dependency on a database or third-party service is allowed by default.

An external capability required by the project, for example an LLM API, is an explicit exception: the service, its purpose, and how it is configured are documented in the overlay / README. That exception does not implicitly authorize other services.
