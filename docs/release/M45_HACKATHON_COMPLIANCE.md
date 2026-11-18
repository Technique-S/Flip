# M4.5-R — hackathon compliance verification

**Retrieval date:** 2026-11-19 (UTC). **Research channel:** agent-reach search/web
backend (Exa search) plus direct retrieval of the official page through the
configured web reader. No submission was made.

**Primary official source:** <https://web3.okx.com/xlayer/build-x-series>
("Build X Series — X Layer TapeOut Accelerate").
**Secondary source (exactly the same official page, alternate locale):**
<https://web3.okx.com/fr/xlayer/build-x-series>.
**Supporting unofficial aggregators (not used as authority):** Hack123
(<https://hack123.henryht.sh/en/h/x-layer-tapeout-accelerate-2026>) and TapeOut
news items (<https://tapeout.link/news/2121998480394555466>).

## Classification

| ID | Requirement | Classification | Exact rule / evidence |
| --- | --- | --- | --- |
| H-01 | Official deadline and timezone | **OFFICIALLY VERIFIED** | Official page: "Submit through the submission form before December 7, 2026, at 23:59 UTC." Header: "Oct 16 2026 – Dec 7, 2026, 23:59 UTC". Terms §2: "The official Event page governs the schedule. The provisional submission deadline is December 7, 2026, at 23:59 UTC." The deadline is explicitly called **provisional** and may change; re-check before submission. |
| H-02 | Eligibility | **OFFICIALLY VERIFIED** | Terms §3: participants "must be at least 18 or the legal age of majority in their jurisdiction, whichever is higher, or be legally established entities"; "Restricted Persons under the X Layer Terms of Service are ineligible"; the Organizer may verify eligibility and require identity checks. |
| H-03 | Submission requirements | **OFFICIALLY VERIFIED** | "Circuit projects must submit the processor contract address and circuit ID. Websites, apps and tools must provide an access link and explain which TapeOut ecosystem projects or features they use." Descriptions must explain product/service, target users and how to reach them, proposed revenue model and why users would pay and keep using it. Submit via the designated form; existing projects must identify substantial new development during the event and only that work is judged. |
| H-04 | Public repository requirement | **UNCONFIRMED** | The official page does not state that a public GitHub repository is required. It requires an access link for websites/apps/tools and relevant addresses for circuit projects. A targeted search for "public repository GitHub requirement" on the official page returned no such rule. Do not assert a public-repo requirement as official. |
| H-05 | Demo requirements | **OFFICIALLY VERIFIED** | Judging criteria: "Demo Video: The recommended length is no more than three minutes. It should cover the problem being solved, a demonstration of the core features, the target users and business model, and how the project uses TapeOut or related ecosystem tools." "The hackathon takes place online, with shortlisted teams attending offline Demo Day." The ≤3 min length is a recommendation, not a hard rule. |
| H-06 | Track relevance | **OFFICIALLY VERIFIED** | Eligible directions "include, but are not limited to, apps, games, online services, developer tools, circuit design and projects exploring mechanisms such as PoD." Flip fits "developer tools" and/or "circuit design"; "Building on existing ecosystem tools and applications is welcome." |
| H-07 | Required X Layer contract/circuit references | **OFFICIALLY VERIFIED** | "Projects must build within the TapeOut ecosystem and either use TapeOut circuits, contracts, or onchain data on X Layer, or run on X Layer DeWEB." FAQ: "Must my project use X Layer? Yes. Your project must use TapeOut circuits, contracts or onchain data on X Layer and provide the relevant addresses. Interfaces and other components do not need to be deployed onchain." |
| H-08 | Is a newly published circuit mandatory? | **OFFICIALLY VERIFIED — NO** | FAQ: "Do I need to deploy my own processor? No. You may build using existing TapeOut processors, circuits and developer tools." The official text does not require minting or publishing a new circuit. (Any separate onchain publication remains an external, explicitly authorized operation, not a Flip product feature.) |
| H-09 | Is a publicly deployed application required? | **UNCONFIRMED (partial official guidance)** | Official text requires websites/apps/tools to "provide an access link", and says "Interfaces and other components do not need to be deployed onchain." It does not say whether a loopback-only local application satisfies "access link". Treat a publicly reachable URL as a likely practical expectation, but do not present it as an official rule. Flip's supported launcher is loopback-only, so this is a potential submission gap, not an verified disqualification. |
| H-10 | Deadline stability | **OFFICIALLY VERIFIED** | Both the participation section and Terms §2/§13 call the date provisional and allow the Organizer to amend the schedule with notice on the event page. Re-check on the submission date. |
| H-11 | Prize pool / judging | **OFFICIALLY VERIFIED** | 100,000 USDT prize pool; first 20,000 (1), second 10,000 (5), third 6,000 (5). Joint X Layer and TapeOut judging on user value/commercial potential, innovation, ecosystem integration, product readiness/UX and demo video. |

## Practical implications for Flip

1. **Reference evidence is available.** The historical sample uses processor
   `0x839bdd6fa7a66416a609a735e11de5411b98574e`, circuits #1 (XOR) and #2
   (NAND) at block 76206482 — genuine X Layer chain-196 captures. These can be
   cited as the "relevant addresses" for a developer-tool submission without
   claiming a newly published circuit.
2. **No write transaction is required by the official rules.** H-08 removes the
   assumption that a new circuit must be minted; Flip must not add signing or
   broadcast to satisfy a non-existent requirement.
3. **Open item is access.** The official page asks for an access link for tools.
   Flip's local-only launcher does not provide a public URL. This is a release
   decision for the founder, not a technical feature to be silently added.
4. **Re-check the deadline before submission** because the official page labels
   it provisional.
5. **Do not submit.** This document is compliance evidence only.

## Evidence provenance

- Official rules quoted verbatim from the page retrieved on 2026-11-19 via the
  agent-reach web reader and independently surfaced by Exa search on the same
  date.
- PRD-era statements (for example the hackathon deadline found in
  `docs/product/CircuitForge_PRD_v1.md`) are **HISTORICAL GUIDANCE** and are not
  used as authority here; the official page supersedes them.
- No official statement was found on public repository requirement (H-04) or
  loopback-only demo acceptability (H-09). Both are recorded as UNCONFIRMED.
