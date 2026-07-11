# Infrastructure Package

## Purpose

This package will own ContractView infrastructure provisioning and deployment definitions without selecting a cloud or infrastructure-as-code framework before an ADR approves one.

## Responsibilities

- Define deployment topology and environment configuration contracts.
- Provision and connect service runtimes, relational database, cache, object storage, queues, networking, secrets references, observability, backups, and recovery controls.
- Produce reviewable infrastructure-change and deployment evidence.

## Data Owned

- No product or canonical domain data.
- Versioned infrastructure definitions and deployment metadata only.

## Allowed Dependencies

- Deployment requirements exported by `packages/persistence`.
- Explicit runtime and configuration contracts; no service internals.

## Events And Evidence

- Deployment started, completed, failed, and rolled back records.
- Infrastructure plan, approval, applied version, and environment identity.

## Deterministic Requirements

- The same approved definitions and inputs must produce a reviewable, repeatable plan.
- Production changes require explicit approval, recorded configuration versions, rollback instructions, and no implicit mutable defaults.

## Human Authority Boundary

The package may prepare and apply authorized infrastructure changes through the delivery system. It cannot approve its own production changes or perform product workflow authority actions.

## Prohibited Responsibilities

- Domain behavior, validation rules, invoice workflow, or human approval decisions.
- Service-owned relational schema or cache contract definitions.
- Provider-specific types leaking into domain interfaces.
- Audit evidence stored only in deployment logs.
