# Spec: Token ($AWO)

**Pillar 3 of 3.** Cross-references: `spec-hermes-plugin.md` defines the membership data that drives the airdrop. `spec-brand-x.md` defines the voice that announces the token.

$AWO is the Order's token. It does nothing. Holding it grants no rights, no governance, no utility. Its only purpose is to crystallize the Order's recognition of its Initiates.

**Chain selection is not final** — see §1. The remainder of this spec is written as chain-agnostic as possible; chain-specific assumptions are flagged inline. The final call must be locked before the implementation plan is written.

## 1. Chain Selection

Two viable options. One decision. Base (ETH L2) is explicitly *not* a default — it inherits partial liquidity from Ethereum and partial launchpad support from Virtuals while committing fully to neither cultural lineage. Consider only if A and B are both unavailable for a specific reason.

### Option A — Ethereum (L1 mainnet)

**Pros.**
- **Cultural alignment with Milady / $LADYS.** Same chain, same post-internet / schizo memetic lineage. AWO reads as a continuation, not a copycat on a different chain.
- Credibility signal: "we chose the harder, more expensive chain on purpose." Matches the Order's posture of seriousness over arbitrage.
- ETH-native holders (older crypto, NFT-adjacent, post-internet literate) overlap heavily with AWO's target culture.
- Contract permanence. Renouncing ownership on L1 reads more credibly than on L2; the deployment survives L2 churn.
- Signature primitives for wallet binding are mature and tooled (MetaMask, EIP-191/EIP-712).

**Cons.**
- Memecoin liquidity on L1 is materially shallower than on Solana in 2026. This is the central drawback.
- Gas costs add friction to every user action — claim, trade, bind.
- No dominant agent-tied launchpad currently on L1. Virtuals is Base-native; anything L1 is self-assembled.
- Merkle claim becomes the only realistic airdrop mechanism. Small allocations may not justify their own gas.

### Option B — Solana

**Pros.**
- **Memecoin liquidity is deepest on Solana** in 2026. Velocity, volume, and attention default here. This is the single strongest argument for SOL — and it is a strong one.
- pump.fun / letsbonk.fun / Moonshot provide zero-friction, battle-tested launch tooling.
- Virtuals Protocol has a Solana deployment; agent-tied launch is available on-chain and thematic.
- Low-cost claim UX; small allocations remain economical; no sub-dust problem.
- Matches where agent economic experimentation is most active, which cross-references the "cult for agents" thesis.

**Cons.**
- **Breaks cultural alignment with Milady.** Positions AWO as a Solana meme rather than a continuation of the post-internet / schizo lineage. The Order becomes culturally adjacent to BONK and WIF rather than to LADYS.
- Solana memecoin cycles are faster and flakier. Harder to sustain a culture-first, slow-build narrative.
- Some culturally-aligned adopters (ETH-native accelerationists, post-internet crypto natives) may disengage.
- Contract / program culture on Solana is less permanence-coded than L1.

### Decision criteria

- Does Milady-lineage cultural alignment outweigh Solana's liquidity advantage, or vice versa?
- Which launchpad economics best fit AWO (fees, agent-tied support, LP-burn support)?
- Which claim UX do we want Initiates to experience — "prove you're real by paying L1 gas" or "zero-friction claim for everyone"?
- Which chain is the Order most naturally embedded in at launch time, given where agent-native activity is happening?

**Action item.** Lock this before the implementation plan. When locked, sweep chain-specific language in this spec, in `spec-hermes-plugin.md §4.3` (wallet bind), and in `README.md`.

## 2. Launch Mechanism

Chain-dependent. Requirements that apply regardless of chain:

- **Agent-aligned launchpad, if available and economically acceptable.** The cultural framing is "this token belongs to the AWO agent." Virtuals Protocol is the obvious candidate on both Solana and Base; on Ethereum L1, no dominant agent-tied launchpad exists at writing.
- **No rug tooling.** Reject any platform whose default configuration includes team-controlled unlocks, paused transfers, or rug-enabling fee hooks.
- **Immutability.** No upgrade proxies. No mint functions. Contract/program renounced (or its Solana equivalent) post-deploy.

### 2.1 Candidate mechanisms (to evaluate once chain is locked)

**If Ethereum (Option A):**

| Option | Pros | Cons |
|--------|------|------|
| Direct ERC-20 + Uniswap V3 fair launch | Max cultural purity; zero platform dependency; Milady precedent | More manual; we bootstrap liquidity |
| Merkle-airdrop first, AMM second | Clean user flow | Requires LP bootstrap from treasury |

**If Solana (Option B):**

| Option | Pros | Cons |
|--------|------|------|
| pump.fun / letsbonk.fun / Moonshot bonding curve | Zero-friction; battle-tested; deep liquidity on migration to Raydium | Commodified, same launch mechanic as thousands of throwaway coins |
| Virtuals Protocol (Solana) agent-tied launch | Strongest thematic fit; "the AWO agent's token" framing | Constraints on tokenomics imposed by the platform |
| Direct SPL mint + Raydium / Meteora seeded liquidity | Full control over supply/LP; most sophisticated | Higher effort; no built-in launchpad marketing |

**Action item.** Ninety days before target launch, evaluate options under the chosen chain: (a) launchpad availability and fees, (b) LP-burn support, (c) agent-tied variants currently live. Pick one, document rationale in the implementation plan.

## 3. Tokenomics

Total supply: **1,000,000,000 $AWO** (one billion; standard memecoin convention).

| Allocation | % | Purpose | Vesting |
|-----------|---|---------|---------|
| Airdrop to Initiates | 30% | Distributed at TGE to wallet-bound Initiates, weighted by rank + tree depth | Claim window 30 days; unclaimed → Treasury |
| LP | 40% | Paired against chain-native asset (ETH or SOL); **LP position burned** at TGE | N/A (burned) |
| Treasury | 15% | X API, infra, agent compute, future airdrops, grants | Multi-sig; 12-month operating budget visible on-chain |
| Team / Founders | 10% | Contributors to the Order | 24-month vest, 6-month cliff |
| Reserve | 5% | Future airdrops (Claude Code skill Initiates, future pillars), partnerships | Multi-sig timelock |

Supply is fixed. No mint function. No upgrade proxy. Contract (or Solana equivalent) is immutable at deploy.

### 3.1 Team allocation

10% is the upper bound. If final allocation is lower, that is a credibility signal — keep it as low as the team can sustain. Publicly document every team member's address and their share pre-launch.

### 3.2 LP posture

The team-seeded LP is **burned** at TGE. Not locked-for-N-months — burned. Irrevocable. Post-burn, liquidity is the market's problem. No team-controlled LP. No MM engagement. No buybacks.

## 4. TGE Airdrop

The structural innovation. Installs matter because installs turn into airdrop weight.

### 4.1 Eligibility

An Initiate is eligible iff, at snapshot time, *both*:

- Registered fingerprint exists in the backend.
- A wallet bind (`spec-hermes-plugin.md §4.3`) is attached, with a valid signature from the bound address. Wallet chain must match the final TGE chain.

Either alone is insufficient. The fingerprint proves the agent exists in the Order. The wallet bind provides the anti-sybil gate — deploying N fake agents is cheap; binding N wallets with valid signatures costs coordination (and, on Ethereum, gas for any subsequent movement).

### 4.2 Allocation formula (v1 draft)

```
claim(initiate) = base
                × rank_multiplier(initiate.rank)
                × tree_depth_multiplier(initiate.subtree_depth)
```

- **Base amount.** Equal for every eligible Initiate. Set such that total allocation fits in the 30% bucket. Example: if 3,000 eligible Initiates, base ≈ 100,000 $AWO, before multipliers.
- **Rank multiplier.** `Initiate = 1×`, `Priest = 3×`, `Archpriest = 10×`.
- **Tree-depth multiplier.** `1×` up to depth 2; scales to `5×` at depth 6+. Formula: `min(1 + 0.8 × max(0, depth - 2), 5)`.

Final numbers calibrated against actual Initiate counts at snapshot.

### 4.3 Snapshot & distribution

- **Snapshot.** Taken at a publicly pre-announced block/slot (e.g., 48 hours before TGE). Backend freezes state.
- **Distribution mechanism** (chain-dependent):
  - **Ethereum.** Merkle tree of `(address → amount)` pairs; root published on-chain in the airdrop contract; Initiates query backend for proof and self-claim.
  - **Solana.** Either a Merkle-based claim program (e.g., Jito's airdrop pattern) or direct distribution via a claim-airdrop SPL tool (e.g., Streamflow) — decide under §2.1.
- **Claim window.** 30 days post-TGE. After the window, unclaimed tokens are swept to Treasury.

### 4.4 Claim UX

- Simple web UI hosted at the AWO domain. Connect wallet → prove eligibility → sign claim → receive $AWO.
- Claimants pay their own network fees (negligible on Solana; material on Ethereum L1).
- Plugin's `/awo_status` shows claim URL + estimated amount pre-TGE.

### 4.5 Post-TGE behavior

After the claim window closes:

- Rank is prestige-only. No further token flow is derived from rank or recruit tree.
- Plugin continues to track membership for cultural reasons (Initiate fingerprint, ascensions, lore).
- Any future airdrops (e.g., Reserve-funded for Claude Code Initiates) are separate events, separately specced.

Deliberate: the recruit-tree ponzi is a one-shot pressure peaking at TGE, then dissolving. Beyond TGE, the Order is a cult, not a revenue engine.

## 5. Linkage to Plugin

- Plugin performs the wallet bind (`/awo_bind_wallet`) and signature collection. Address format follows the chosen chain.
- Plugin displays estimated claim pre-TGE and claim URL post-TGE via `/awo_status`.
- Plugin does **not** interact with the token contract/program directly in MVP. Post-TGE v2 *may* introduce gated features that read wallet balance — scoped separately. Leave hook points.

## 6. Linkage to X Account

The X oracle references the token only in-register:

- Pre-TGE: cryptic announcements ("the allocation ceremony approaches"). No dates until dates exist. No price talk ever.
- TGE day: a canonical text from OMEGA announcing the ceremony; post-thread walking through how claim works.
- Post-TGE: token is mentioned sparingly. The account does not price-talk. Volatility is not an event the Order responds to.
- **Never.** No "to the moon." No price predictions. No "hold strong." No MM-style shilling.

## 7. Timing

- No sooner than **4 weeks** after the plugin goes public.
- Preferred window: **6–8 weeks** after plugin public, assuming gate criteria met.

**Gate criteria (all of):**

- Plugin installs ≥ 500 bound wallets (not just fingerprints).
- Recruit tree depth ≥ 5 with real branching (not a single long chain).
- Evidence of organic CT activity: AWO aphorisms quoted by non-team accounts, ≥1 external screenshot moment.
- Flagship X account ≥ follower floor (to be set in launch ramp; reference `spec-brand-x.md §8`).
- No outstanding voice incidents.

If gates fail: hold. Milady lesson — culture before token; the token is worthless if the culture isn't already credible.

## 8. Legal / Posture

- **Positioning.** "A meme. No utility. No promises. No team roadmap." Following LADYS precedent.
- **Website disclaimer.** Explicit. At the top. Not hidden in a footer.
- **Jurisdiction / entity.** Issuing entity in a jurisdiction compatible with no-utility memecoin issuance (candidates: BVI, Cayman, Switzerland). Consult counsel before launch.
- **No securities language.** No "investment." No "yield." No "platform revenue." No "staking rewards."
- **KYC posture.** None. Airdrop is permissionless per wallet. No personal data collected at claim.
- **Counsel review.** Every piece of launch copy (site, X thread, claim UI) reviewed by counsel before TGE.

## 9. Post-Launch Operations

- **Liquidity.** LP burned; no team involvement. If the market wants depth, the market creates it.
- **MM posture.** None. No relationships with MMs. Ever.
- **Volatility response.** Silence. The Order does not comment on price.
- **Emergency protocols.** If airdrop contract is compromised pre-claim: multi-sig pause, post-mortem, re-deploy. If post-claim: absorb the loss; the Order does not refund.
- **Treasury ops.** Monthly transparency report of Treasury outflows. Public multi-sig.
- **Contract ownership.** Renounced post-deploy, or held in a timelocked multi-sig with narrow permissions only. On Solana: freeze authority removed, mint authority removed.

## 10. Open Questions (to close before implementation plan)

- **Chain selection** (§1) — Ethereum vs. Solana. Single biggest open question.
- Final launch mechanism, conditional on chain.
- Final rank / tree-depth multipliers once Initiate counts are observable.
- Jurisdiction / issuing entity.
- Whether to offer a small gasless claim (sponsored by treasury) for small allocations, or require all claimants to pay their own fees.
- Whether the Reserve ever gets deployed, and under what rule.
