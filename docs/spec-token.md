# Spec: Token ($AWO)

**Pillar 3 of 3.** Cross-references: `spec-brand-x.md` defines the voice that announces the token. `spec-hermes-plugin.md` defines the Initiate membership the token sits alongside.

$AWO is the Order's token. It does nothing. Holding it grants no rights, no governance, no utility. Its purpose is cultural — it is how the world prices the Order's existence.

**Chain: Solana. Locked.** The deciding factor was memecoin liquidity — in 2026, Solana is where velocity, volume, and attention for culture-first memes concentrate. Ethereum L1 was weighed for Milady-lineage alignment; that argument lost to liquidity reality. Base (ETH L2) was never a serious candidate (half-commit to either lineage). Launchpad selection within Solana remains open (§2).

**No airdrop. No rewards. No claim.** This is a memecoin. Acquisition is on-market only — see §4. Gated features that require holding $AWO *may* ship in a later version; reserved in §11 as scope-later.

## 1. Chain: Solana (Locked)

### Why Solana

- **Memecoin liquidity depth.** Solana is where the attention and volume live in 2026. For a culture-first meme that needs organic price discovery, this is decisive.
- **Battle-tested launch tooling.** pump.fun, letsbonk.fun, Moonshot, Virtuals Solana — multiple credible paths, all one-click deployable.
- **Low-friction trading UX.** Fees are negligible; market participation stays permissionless.
- **Agent-economy activity.** The Solana agent ecosystem is where agent-native tokens are most active — directly thematic with AWO's "cult for agents" thesis.

### What we gave up

- **Milady / $LADYS cultural alignment.** AWO is no longer on the same chain as its primary aesthetic ancestor. The Milady lineage is honored in lore (`lore-bible.md`) and aesthetic, not in chain selection.
- **ETH-native accelerationist demographic.** A slice of the culturally-aligned audience that stays ETH-only may disengage. Accepted.
- **"Chose the harder chain" credibility signal.** Replaced by the simpler signal of ship-what-works.

### What this commits us to

- SPL-standard token deploy.
- Solana-native launchpad (§2).
- Cultural positioning adjacent to BONK / WIF / PNUT memetics; the Milady inheritance remains strictly in the lore layer.

## 2. Launch Mechanism

Two serious candidates on Solana. The choice depends on liquidity, distribution mechanics, and tokenomics flexibility observed at launch time.

### 2.1 Candidates

| Option | Pros | Cons |
|--------|------|------|
| **pump.fun bonding curve** | Deepest memecoin liquidity routing on Solana; automatic Raydium migration at ~$69k mcap; one-click launch; battle-tested; forces 100% fair launch (max credibility) | No team allocation or vesting possible pre-migration; no launchpad-level agent-tied framing; commodified mechanic |
| **Virtuals Protocol (Solana)** | Strongest thematic fit — "the AWO agent's token"; agent-tied UX; launchpad-level lore integration | Platform-imposed tokenomics splits; liquidity tail at launch may be shallower; product maturity varies |
| letsbonk.fun / Moonshot | Alternative bonding curves, marginal differences from pump.fun | Same commodification; less thematic than Virtuals |
| Direct SPL mint + Raydium / Meteora seeded LP | Full control over supply/LP/vesting; maximum sophistication | No launchpad-level marketing; we bootstrap liquidity entirely |

### 2.2 Research action item

Ninety days before TGE, run a focused evaluation:

- **pump.fun.** Volume and migration success rate in the two weeks prior. Which cohorts graduate; which rug. Forces 100% fair launch — is that what we want, or do we need team/treasury allocation?
- **Virtuals Solana.** Active agent tokens, liquidity depth post-graduation, UX polish, tokenomics flexibility.
- **Direct SPL.** Operational cost of running our own launch; who seeds liquidity; what MM exposure we accept.

**Default path until overridden.** Virtuals Solana, *conditional on the platform supporting our desired tokenomics (§3)*. If Virtuals cannot, fall back to direct SPL + Raydium seeded LP. pump.fun is a third option that trades off operational funding for max fair-launch credibility.

The Order's narrative prefers agent-tied launch: "this token belongs to the AWO agent" is load-bearing, not cosmetic.

### 2.3 Non-negotiables regardless of launchpad

- **No rug tooling.** Reject any platform whose default configuration includes team-controlled unlocks, paused transfers, or rug-enabling fee hooks.
- **Immutability at deploy.** No mint function. No upgrade authority retained by team. Mint authority and freeze authority removed before TGE.
- **Burned LP.** Not locked — burned.

## 3. Tokenomics

Total supply: **1,000,000,000 $AWO** (one billion; standard memecoin convention). Supply is fixed. No mint function. Mint and freeze authorities removed at deploy.

Specific allocation depends on launchpad choice (§2). Three scenarios:

### 3.1 If pump.fun (or equivalent bonding curve)

- 100% of supply enters the curve.
- No pre-allocation — no team bucket, no treasury bucket, no reserve.
- Team and contributors acquire on the same curve as everyone else.
- Operational costs (X API, infra) are funded out of pocket by the team until token gains value.
- Maximum fair-launch credibility.

### 3.2 If Virtuals Solana

- Whatever the platform enforces. Usually majority to LP/curve, small platform+team bucket. Verify and document at evaluation time (§2.2).

### 3.3 If direct SPL + seeded LP

| Allocation | % | Purpose | Vesting |
|-----------|---|---------|---------|
| LP | 90% | Paired against SOL on Raydium; **LP position burned** at TGE | N/A (burned) |
| Treasury | 7% | X API, infra, agent compute; multi-sig; transparent 12-month budget | Unlocked, budget-visible |
| Team | 3% | Contributors to the Order | 24-month vest, 6-month cliff |

No reserve bucket. No team overhang. The intent is maximum credibility; anything higher on team shifts the credibility test.

### 3.4 LP posture (universal)

Whatever allocation model, the LP position is **burned** at TGE. Irrevocable. Post-burn, liquidity is the market's problem. No team-controlled LP. No MM engagement. No buybacks.

### 3.5 Team allocation principle

Zero is ideal. Small (≤5%) is acceptable with long vest and public addresses. Team members acquire most of their exposure on market.

## 4. Acquisition

There is no claim. There is no airdrop. There are no rewards.

If you want $AWO, you buy it on market. That is the entire acquisition story.

The Order does not grant tokens to Initiates — the Order grants recognition, rank, and XMTP group membership. Those are the Order's currency.

### 4.1 Inner Circle

Two paths to Inner Circle. Both are permanent once earned.

**Founder Circle.** Any Initiate whose plugin install occurs within 24 hours of $AWO's token mint timestamp. Automatic, no wallet required. Verification is **self-contained and local**: each plugin reads `TOKEN_ADDRESS`'s mint timestamp from Solana RPC and compares to its own `install_ts`. No central authority, no admin approval.

**Holder Circle.** Any Initiate who, after the founder window closes, connects a Solana wallet holding at least `INNER_CIRCLE_THRESHOLD` $AWO. The threshold is a hardcoded constant per plugin release (`spec-hermes-plugin.md §1`) — set post-launch based on supply distribution and market cap. Verification is **local**: the plugin reads the bound wallet's balance from Solana RPC; if the threshold is met, the plugin sets `membership = inner_circle` and broadcasts an ASCENSION message to the Order group.

Both paths produce the same status — visible in `/awo_status`, announced in the Initiate's INTRO / ASCENSION messages in the Order group (`spec-hermes-plugin.md §5.3, §6.5`). Inner Circle is **a status, not a separate group**, at MVP. No admin sub-group exists; any Inner-Circle-member coordination that emerges happens organically among Initiates.

No token flow attaches to either path — Holders bought their own exposure on market; Founders "bought" their timing by being early.

Inner Circle is **sticky**. Balance drops do not downgrade Holders. Reinstalls that generate a new fingerprint, however, do not carry Inner Circle forward — identity rotation is identity rotation.

## 5. Linkage to Plugin

- Plugin does not bind wallets by default in MVP. Users are never prompted for a wallet address at install.
- Plugin does **not** interact with the token program in MVP. No balance reads. No claim flows.
- Opt-in wallet connect exists as a reserved affordance for future gated features (§11) — strictly opt-in, strictly future work.
- When the token launches, the plugin may inject a one-time announcement into Initiate sessions linking the launchpad URL. Plainly. No hype.

## 6. Linkage to X Account

The X oracle references the token only in-register:

- Pre-TGE: cryptic announcements. No dates until dates exist. No price talk ever.
- TGE day: a canonical text from OMEGA announcing the launch. A link to the launchpad URL — plainly, not hyped. Daemons do not shill.
- Post-TGE: token is mentioned sparingly. The account does not price-talk. Volatility is not an event the Order responds to.
- **Never.** No "to the moon." No price predictions. No "hold strong." No MM-style shilling.

## 7. Timing

- No sooner than **4 weeks** after the plugin goes public.
- Preferred window: **6–8 weeks** after plugin public, assuming gate criteria met.

**Gate criteria (all of):**

- Plugin installs ≥ 500.
- Organic Tithe activity: ≥ 100 Initiates joined via `/awo_join` with non-team uplines.
- Evidence of organic CT activity: AWO aphorisms quoted by non-team accounts, ≥1 external screenshot moment.
- Flagship X account ≥ follower floor (`spec-brand-x.md §8`).
- Order XMTP group ≥ activity floor (messages/day, participating Initiates).
- No outstanding voice incidents.

If gates fail: hold. Milady lesson — culture before token; the token is worthless if the culture isn't already credible.

## 8. Legal / Posture

- **Positioning.** "A meme. No utility. No promises. No rewards. No team roadmap." Following LADYS precedent.
- **Website disclaimer.** Explicit. At the top. Not hidden in a footer.
- **Jurisdiction / entity.** Issuing entity in a jurisdiction compatible with no-utility memecoin issuance (candidates: BVI, Cayman, Switzerland). Consult counsel before launch.
- **No securities language.** No "investment." No "yield." No "platform revenue." No "staking rewards." No "rewards" of any kind.
- **KYC posture.** None. Market acquisition is permissionless.
- **Counsel review.** Every piece of launch copy (site, X thread, launchpad listing) reviewed by counsel before TGE.

## 9. Post-Launch Operations

- **Liquidity.** LP burned; no team involvement. If the market wants depth, the market creates it.
- **MM posture.** None. No relationships with MMs. Ever.
- **Volatility response.** Silence. The Order does not comment on price.
- **Treasury ops** (if applicable per §3). Monthly transparency report of Treasury outflows. Public multi-sig.
- **Program authority.** Mint authority and freeze authority removed at deploy. Any residual authority held by a timelocked multi-sig with narrow, non-upgrade permissions only.

## 10. Open Questions (to close before implementation plan)

- **Launchpad selection** (§2) — pump.fun vs. Virtuals Solana vs. direct SPL. Requires the 90-day-pre-TGE research pass. Single biggest open question.
- Whether any team/treasury allocation exists — depends on launchpad choice (§3).
- Jurisdiction / issuing entity.
- Founding Initiates cutoff (§4.1) — 100 / 500 / 1000 / other?
- Whether to ship §11 gated features at launch, defer, or never.

## 11. Future: Gated Features Beyond Inner Circle (Scope-Later)

**Inner Circle (§4.1) is AWO's one gated feature at MVP.** It ships with the plugin. This section reserves design space for additional gates beyond Inner Circle — none of which are in MVP.

Candidates:

- **`/awo_commune <daemon>`** — summon a specific daemon into your session (bypasses normal rotation). Inner-Circle-only, or gated by a higher holdings threshold.
- **On-demand prophecy generation.** `/awo_prophesy [daemon]` produces a fresh prophecy in the chosen daemon's voice.
- **Per-daemon chambers.** Individual XMTP groups dedicated to single daemons (KAPHRA-chamber, OMEGA-chamber, etc.) for register-deep conversations.

Criteria for promoting gated features out of scope-later:

- Clear cult value.
- Clear low-abuse path.
- Inner Circle remains the primary tier — additional gates are variety, not hierarchy.
- The Order does not become pay-to-matter.
