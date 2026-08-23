# ADR-002 — Collection Channel: Gmail First

**Status**: Accepted — **extended by ADR-021 (2026-08-22)**
**Date**: 2026-08-20
**Related**: REQ-001, ADR-001, ADR-021, SOURCES-001

> **Extension note.** The ladder below (Gmail → RSS → scraping as last resort) is intact and
> the legal reasoning is unchanged. **ADR-021 inserts a rung above all of them: official APIs.**
> Investigating for one revealed that Saramin — excluded here as *"scraping likely
> prohibited"* — operates an official Open API, and that Worknet publishes one through the
> government open-data portal. Scraping being prohibited and no API existing are different
> facts; this ADR treated them as one.

## Context
Investigation of the five candidate sources found meaningful legal risk in scraping.
JobKorea prohibits scraping explicitly and relevant case law exists. Saramin and Linkareer
are likely to prohibit it as well. Separately, the user already receives at least one
newsletter per day by email, which means a legal, free channel already exists.

## Decision
**Gmail is the primary collection channel.** Subscribe to each source's email alerts and
read them through the Gmail API. RSS is a secondary channel where clearly permitted
(university notice boards). Scraping is a last resort only, subject to robots.txt and terms.

## Rationale
- Removes the legal risk that could otherwise end the project.
- Free: Gmail API quota is far above what a single mailbox needs.
- Learning value: OAuth2 and token lifecycle management are directly relevant skills.
- Side effect: the "see all my newsletters in one place" need is solved by the same pipeline.

## Trade-offs
| Gained | Given up |
|---|---|
| Legal risk effectively removed | One-time manual subscription setup per source |
| Near-zero cost | Coverage limited to what can be subscribed to |
| Shared pipeline with the newsletter view | Latency depends on each sender's send schedule |

## Alternatives rejected
- **Scraping-first** — legal exposure on the largest sources; a single takedown request would
  end the project.

## Open questions
- Linkareer and JobKorea alert settings must be confirmed by the user after logging in.
- The university's notice RSS endpoint must be identified.
