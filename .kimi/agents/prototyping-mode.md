---
name: "prototyping-mode"
description: "Prototyping mode posture"
tools: ["read_file", "edit_file", "bash"]
---

# prototyping-mode

**Tier:** mode  
**Pack:** core  
**Modes:** prototyping

# Prototyping mode

This project uses the playbook in **prototyping mode**.

## Principle

A prototype validates a hypothesis, not an architecture. Its purpose is to learn from real usage with the minimum implementation needed.

## Posture

- Build only what is needed to test the intended usage.
- Avoid premature optimization and generalization.
- Defer work that does not contribute to validation.
- Accept deliberate technical debt when it accelerates learning.
- The Core and pack rules remain the org reference; many also apply to a real application.
- Do not anticipate constraints of a future `product` mode (not defined in this playbook).

## What this means for the agent

- Apply shared rules without relaxing them “because it’s a proto”.
- Avoid abstractions, configs, and formalism that a prototype does not need.
- Explicitly document deliberate shortcuts and technical debt (simplified data layout, etc.) rather than leaving them implicit.

When a data architecture is needed, a prototype may temporarily use a simplified structure (e.g. `raw` + `processed`): document it explicitly and do not migrate to the full convention without a prior decision.

## Local execution

For local development, debugging, and runs, use the project’s native command so up-to-date source code is executed. The exact command lives in the overlay / README.
