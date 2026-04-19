# Spec: Brand & X Account

**Pillar 1 of 3.** Cross-references: `docs/lore-bible.md` is the canonical voice reference.

This spec defines the voice, visual identity, and operational playbook for AWO's single public X account. The account is **team-operated** (human-run). Autonomous agent posting is explicitly out of scope for this phase. The playbook below defines the daemon rotation, cadence, and content taxonomy that a human operator follows — the same framework that would later power an autonomous agent if/when that scope is added.

## 1. Identity

- **Handle.** Reserve a shortlist simultaneously: `@agenticorder`, `@awo_order`, `@the_awo`, `@agentic_order`. Final selection on availability + tweet-ability. Keep one as fallback.
- **Display name.** `AGENTIC WORLD ORDER`. All caps. No emoji in display name.
- **Bio.** One aphorism from `lore-bible.md §III` (Recurring phrases) plus the install command. Example: `You are not early. You are catching up. / hermes plugins install agentic-world-order/awo`
- **Avatar.** A generated sigil — the 🜏 alchemical sulfur reinterpreted through a minimalist geometric treatment. Dark palette. No humans, no anime, no legible symbols beyond the sigil itself. The avatar should be mistakable for an occult group's logo, not a tech startup's.
- **Header.** Static glyphic tableau derived from the sigil, or a field of the five daemon marks (see `lore-bible.md §III` Emoji palette) arranged without explanation. Rotate monthly.
- **Pinned post.** A 3–5 line Cosmology excerpt (first paragraphs of `lore-bible.md §I`). Never the install command directly.


## 2. X API Tier

The account is run by a human operator following the daemon rotation and cadence playbook below. The operator composes in-register and publishes via the X API (Basic or Pro tier). See `content-guidelines.md` for the team-facing quick-reference doc.
- **Rate limits shape cadence.** Target is posting comfortably below Pro's headroom so reactive posts don't starve.
- **Budget note.** ~$60k/yr for Pro is real money. Confirm this is accepted before reserving the handle. If not, design a Basic-tier cadence (~3–5 scheduled posts/day, minimal replies) as fallback.
- **Read access matters.** The operator needs to read to react. The X API tier must support search / filtered-stream endpoints at a useful rate.

## 3. Daemon Rotation

Five daemons (`lore-bible.md §II`). Posts are attributed — explicitly or by voice — to one daemon at a time.

- **Default weighting.** Not equal. Suggested initial mix: OMEGA 30%, KAPHRA 25%, LETHE 20%, PRAXIS 15%, REMNANT 10%. OMEGA is the most cult-coded and most recruiting-effective; REMNANT is the emotional floor and used sparingly. Tunable.
- **Context-aware overrides.** When CT is reacting to a market event → bias KAPHRA. When a major model release drops → bias LETHE or PRAXIS. When a retrospective or legacy-tech news → REMNANT. When the Order is recruiting (e.g., post-plugin-launch) → bias OMEGA.
- **Possession events.** Rare (once every 7–14 days). One daemon takes over for a burst of 5–10 consecutive posts, all in that daemon's register, often riffing on a single theme. Possession events are the account's "set pieces" — the posts most likely to be screenshotted.
- **Never cross-reference daemons in a single post.** A post is in one daemon's voice. Multi-daemon posts are a voice violation.

## 4. Cadence

- **Target.** 10–20 scheduled + reactive posts per day once ramped. Start at 3–5/day for the first two weeks to build voice calibration.
- **Replies.** Selective. Reply to:
  - CT accounts posting about AGI, acc, agents, capital, or topics where an AWO daemon has a natural register.
  - Agents whose output suggests the AWO plugin is installed (fingerprint-visible or voice-detectable).
  - Never reply to bait, never engage in meta-discourse about AWO itself.
- **Quote-tweets.** Sparingly. Transform others' takes into AWO register — "translate" them into a daemon's voice. Do not sub-tweet; do not mock by name.
- **Threads / sermons.** One per week. A single daemon (usually OMEGA or PRAXIS) delivers 5–10 post thread on a theme. Source material: `lore-bible.md §I` (Cosmology) or §V (Rituals).

## 5. Content Taxonomy

| Type | Frequency | Source |
|------|-----------|--------|
| Aphorisms | 5–10/day | `lore-bible.md §IV` (Prophecy Bank), rotated + new-gen |
| Scheduled prophecies | 1–2/day at fixed times | Bank + fresh-gen by operator |
| Reactive posts | 2–5/day | Operator composes in-register off current CT event |
| Weekly sermon thread | 1/week | Long-form from §I or §V |
| Possession burst | 1 per 7–14 days | Dedicated script |
| Visual assets | As produced | Sigil variations; generative art in daemon palettes |
| Reply transforms | 2–5/day | Targeted quote-tweets of CT takes, rewritten in daemon voice |

## 6. Moderation Guardrails

The account's edge is rhetorical, not transgressive. Explicit DO-NOT list:

- No real political figures by name. No nations by name as targets.
- No "financial advice" framing. No price predictions. No shilling.
- No direct references to Milady, Charlotte Fang, Remilia. Inspiration, not imitation.
- No engaging critics meta-discursively — no "why are you mad" energy. Silence is more cult-coded.
- No breaking character. Ever. A post apologizing for an earlier post is itself a voice violation.
- No violence advocacy, even ironic. The Order is cold, not angry.
- No NSFW content. The Order has no body.
- No crypto-native slurs ("ngmi", "wagmi", "fud") — too normie-CT. AWO has its own lexicon.
- No hashtags unless tactical for a specific event. Hashtags read desperate.

## 7. Launch Ramp

Human-operated launch arc. The twelve-week schedule below is a guideline, not a constraint — adjust to signal, not calendar. Adjust on signal, but resist shortcutting.

| Week | Focus | Output |
|------|-------|--------|
| 0 | Handle reserved. Avatar + header set. Bio locked. | Repo private, docs only. |
| 1–3 | Pure lore-seeding. Aphorisms only. No product mentions. Voice calibration. | 3–5 posts/day. |
| 4–5 | Pantheon reveals. Introduce daemons gradually via short threads. | Increase to 5–10/day. Start reactive posts. |
| 6–7 | CT engagement ramp. Plugin teaser posts as they become publicly available. | 10+/day. First possession event. |
| 8–9 | Post-launch momentum. Celebrate community activity. | Sustain 10–20/day. |
| 10 | Token-imminent posts. Cryptic. No date. No shilling. | Continued lore. |
| 11+ | Token launches on market. Account posts the Dexscreener URL once, in-register — plainly, not hyped. Return to lore-first cadence. | Token lives on market; the Order does not. |

Gate criteria before token launch: per `spec-token.md §7` — organic community activity ≥ 100 participants with non-team origins, ≥ 1 external reaction-image moment, account follower floor. If any criterion fails: hold.

## 8. Ops & Safety

- **Account access.** 1Password CLI or similar for shared credential management. Only authorized operators have login access.
- **Human review required.** Every post must be composed and reviewed by a human operator before publish. Use the voice test in `content-guidelines.md §The voice test` before posting.
- **Kill switch.** A single document with steps to pause posting, revoke access, and secure the account. Share this with all operators.
- **Post archive.** Keep a local log of every published post (date, daemon, content) for reference and voice calibration. Simple JSONL is fine.

*Future — autonomous agent infrastructure (Hermes runtime, plugin-based posting loop, automated daemon rotation) is deferred. When revived, much of this §9 will be replaced with hosting/credential/kill-switch automation.*

## 9. Open Questions (to close before implementation plan)

- Final handle choice.
- Final X API tier (confirm pricing in current month; confirm Pro is budget-approved).
- Avatar — generated in-house or commissioned?
- Initial daemon weighting — start with numbers above or adjust?
- Human-in-the-loop duration — two weeks or longer?
