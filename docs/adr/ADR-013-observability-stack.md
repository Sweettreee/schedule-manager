# ADR-013 — Observability under a 2 GiB Memory Budget: VictoriaMetrics

**Status**: Accepted
**Date**: 2026-08-22
**Related**: ADR-004, ADR-005, ADR-008, **ADR-024**, ARCH-001, REQ-001 §7, OPS-001

## Context

Block B17 promises "metrics, dashboards, failure alerting" as a deliverable with a visible
result. `OPS-001` said "Prometheus / Grafana, subject to the memory budget in ARCH-001".
Those two statements were never reconciled, and when the ARCH-001 ledger was completed it
turned out they could not be:

| | Approximate resident memory |
|---|---|
| Prometheus (even with short retention) | 250–400 MiB |
| Grafana | 80–150 MiB |
| kube-state-metrics | 40–60 MiB |
| node-exporter | 15–30 MiB |
| **Total** | **385–640 MiB** |

The workload budget on a `t4g.small` after the OS and k3s is about **1,250 MiB**, and the
application, database, ingress, cert-manager and Flux already request **755 MiB** of it.
A conventional Prometheus + Grafana stack does not fit, and B17 is the block most directly
tied to the Cloud/DevOps/SRE goal, so dropping it is not acceptable either.

Observability is also not optional here for a second reason: `REQ-001` §7 defines a freshness
SLO, and `ADR-012` layer B needs a metrics-backed alert rule. Something has to store a time
series.

## Decision

**VictoriaMetrics single-node (`victoria-metrics` in `-retentionPeriod=7d` mode) plus
node-exporter, scraping in Prometheus format. Grafana is deployed at 0 replicas and scaled up
on demand when a dashboard is actually being read.**

kube-state-metrics is **not** installed in v1; the handful of Kubernetes object states that
matter are covered by node-exporter plus the collector's own metrics.

Alert rules run in `vmalert`, which is part of the same binary family and adds ~20 MiB.

## Rationale

- **It fits.** VictoriaMetrics single-node holds roughly 80 MiB resident at this cardinality
  against Prometheus's 250–400 MiB — the ledger closes with 415 MiB of headroom instead of
  being over budget.
- **The skills transfer.** VictoriaMetrics ingests the Prometheus exposition format, speaks
  PromQL (MetricsQL is a superset), and uses Prometheus-format alert rules. Everything
  learned here — instrumenting a service, writing a recording rule, expressing an SLI as a
  query — applies unchanged to Prometheus in any future job. What is *not* learned is
  Prometheus's own storage and federation behaviour, which is a real but narrow gap.
- **Grafana on demand is honest about single-user reality.** A dashboard nobody is looking at
  costs 100 MiB continuously. `kubectl scale deploy/grafana --replicas=1` before looking and
  back to 0 afterwards is a fifteen-second operation, and it turns a permanent cost into an
  occasional one. Alerts, which must always work, do not depend on Grafana.
- **Consistent with ADR-004**: the stack is self-hosted and operated by hand. No exception is
  being claimed here.
- **Consistent with ADR-008**: Flux was chosen over ArgoCD on exactly this reasoning —
  memory, not preference. Choosing VictoriaMetrics over Prometheus for the same reason keeps
  the design coherent rather than making one exception.

## Trade-offs

| Gained | Given up |
|---|---|
| B17 becomes buildable within the memory ledger and the budget | Hands-on experience with Prometheus's own TSDB and its operational quirks |
| PromQL, exporters, alert rules, SLO queries — all still learned | kube-state-metrics-based cluster-object alerts, deferred |
| Alerting works without Grafana running | A dashboard is not instantly available; it takes one command |
| 7-day retention keeps disk and memory bounded | No long-term trend analysis; monthly SLO figures must be recorded in `STATUS.md` before they age out |

The last row is a real operational obligation: the **monthly operations review (OPS-001 §7)
must record the SLO error-budget figure**, because after seven days the raw data is gone.

## Alternatives rejected

- **Prometheus + Grafana as originally implied** — the standard stack and the one with the
  most direct résumé value, but 385–640 MiB against a 495 MiB remaining budget. It does not
  fit, and finding that out at B17 — after paying for the instance — would be the expensive
  way to learn it.
- **Node agent only, with storage and dashboards in Grafana Cloud's free tier** — near-zero
  local memory and the best dashboards. Rejected because it moves the entire observability
  layer, which is the single most career-relevant part of this project, into a service the
  owner would not operate. That is precisely the layer ADR-004 exists to protect, and no
  ADR-004 exception applies: it is neither a security risk to self-host, nor low-learning,
  nor irreversible. Reconsider only if the memory ledger fails again after real measurement.
- **`t4g.medium` (4 GiB) with a nightly shutdown schedule** — the most comfortable option
  technically and it would allow the full standard stack. Rejected because it inverts the
  project's constraint discipline: the 2 GiB limit is what forced ADR-006 (no JVM) and
  ADR-008 (Flux over ArgoCD), and relaxing it here would make those decisions look arbitrary.
  It also adds a shutdown scheduler to operate and makes the dashboard unavailable at night,
  which conflicts with metric M-3.

  > **Cross-reference added 2026-08-25.** What is rejected here is `t4g.medium` **plus** a
  > shutdown — paying for a larger instance and then stopping it. **`ADR-024` subsequently
  > adopted a nightly shutdown on the `t4g.small` already chosen**, 02:00–08:00 KST, and answers
  > the two objections raised above: the scheduler is one rule outside the instance, and the
  > window was chosen to contain no plausible dashboard visit, with an M-3 re-check booked at
  > the first monthly review. The memory argument in this ADR is untouched — a shutdown does not
  > create RAM.
- **Logs-based observability only (no metrics)** — cheaper still, but an SLO expressed over
  time cannot be computed from unaggregated logs on this node.

## Implementation notes for B17

- Scrape targets: node-exporter, the FastAPI app (`prometheus-fastapi-instrumentator`), and
  a small collector exporter publishing `collector_last_success_timestamp_seconds`.
- That one gauge is the SLI (REQ-001 §7) **and** the input to ADR-012 layer B. Define it once.
- `vmalert` rule for layer B:
  `time() - collector_last_success_timestamp_seconds > 30 * 3600`
- Retention 7 days; set `-memory.allowedPercent` conservatively so VictoriaMetrics does not
  expand into the headroom the ledger reserves for other pods.
- Record measured memory back into the ARCH-001 ledger, as B9 did.

## Open questions

- Whether to add kube-state-metrics once measured headroom allows. Revisit after the first
  monthly review with real figures.
- Whether 7-day retention is enough once the SLO has been running for a quarter. If longer
  trends prove useful, the cheapest answer is a monthly export to S3, not a bigger instance.
