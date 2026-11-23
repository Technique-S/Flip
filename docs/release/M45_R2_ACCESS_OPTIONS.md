# M4.5-R2 — Safe judge-access options

Date: 2026-11-22. Baseline `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`.
**No hosting, tunnel, deployment, wallet connection or application submission was performed.**

## Current official-rule ledger

Primary source: [official X Layer TapeOut Accelerate page](https://web3.okx.com/xlayer/build-x-series).
Text was retrieved through the independently authorized web retrieval tool at
**2026-11-22 09:51:58–09:52:01 UTC**. The tool reports cached/crawled content; this is not a
signed organizer confirmation. A separate direct HTTPS fetch at 09:33:01 UTC failed with
WinError 10054; no HTTP-success code or saved fresh origin response is claimed.

Rule summary (source sections Requirements, FAQ and Terms):

| Rule | Observed requirement |
|---|---|
| H1 | Event dates shown are October 16–December 7, 2026; deadline 23:59 UTC is also called provisional. Recheck before the owner submits. |
| H2 | TapeOut/X Layer use and relevant addresses must be explained; developer tools are an eligible direction. |
| H3 | Apps/tools need an access link. The page does not define acceptance of source-only, static-only or downloadable access. |
| H4 | Existing projects must identify substantial event-window additions. |
| H5 | Describe users, acquisition, value and proposed revenue; prior revenue is not required. |
| H6 | Existing processors may be reused; offchain interfaces/computation are allowed. |
| H7 | Video recommendation is no more than three minutes. |
| H8 | Entrant eligibility, rights to included material, terms and owner declarations still need checking. |

The linked [submission form](https://forms.gle/EoDNbxQ65dev1wFd9) redirected to a Google
Forms page that the retrieval tool could not access. **Form fields, login requirements,
final attachment requirements and application-access acceptance: NOT VERIFIED.** No form
was submitted or browser protection retried. No Telegram message or organizer inquiry was sent.

There are about 15 calendar days from this audit date to the displayed deadline date.
The displayed instant converts to December 8 at 00:59 Africa/Lagos; use UTC for planning.
That conversion does not make the provisional deadline final.

## What is already reachable

[Public repository](https://github.com/Technique-S/Flip) visibility was confirmed through
GitHub's API. The tested [accepted revision](https://github.com/Technique-S/Flip/tree/b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b)
contains the supported checkout, not an installer. Source visibility is **not** evidence
that H3 is met or that the source is licensed for reuse. No actual deployed app/access URL
was supplied or verified in this audit.

## Option comparison

Costs below are planning categories, not quotes. No paid account or external service was
created. Existing internet access, judge time and dependency downloads are real dependencies.

| Option / current state | What judges can actually do | Live versus recorded / unavailable | Security and rights | Cost / dependencies | H3 acceptance |
|---|---|---|---|---|---|
| Public repository + docs — reachable | Read source, commands and reports; inspect accepted revisions; optionally reproduce locally. | Documentation is live on GitHub; screenshots/results are recorded. A GitHub page cannot itself execute Flip's native proof engine. | Low service-exposure risk; still needs owner source-license and material-rights decisions. Do not link private logs or credentials. | Existing public GitHub access; their network and development machine. | **UNCERTAIN**. Do not present it alone as compliant application access. |
| Reproducible local checkout launcher — technical PASS / onboarding PARTIAL | Install pinned tools/dependencies; run real compose, compare, diagnostics, packages, CLI/API/browser and replay on their machine. | Native proof is live locally. Archived sample is historical; current discovery depends on RPC. No signing/publication. Windows/Linux support evidence; no promised macOS support. | Keeps solver on loopback with existing host/origin/body/concurrency gates. No tunnel/reverse proxy. Project/browser storage is plaintext. Rights decision precedes advertised redistribution. | No new server bill; judge setup time; CPython 3.14.6, uv 0.9.11, Node 24.18.0, npm and dependency registries/wheels. | **UNCERTAIN** until organizers accept local-install access. |
| Hosted static recorded-evidence demonstration — proposed, not built/deployed | Follow a narrated/captioned walkthrough; inspect a curated project/receipt and recorded outputs; download artifacts if rights permit. | Only display/navigation is live. Comparison, connection diagnosis and proof results are precomputed; no fresh proof, arbitrary project import, RPC, auth or publication. | Separate inert viewer, escaped text, no executable reproduction strings, no credentials, no backend/worker, explicit HISTORICAL/RECORDED labels. Rights/privacy review and explicit hosting authorization required. | Static hosting may fit an existing free public-repository plan; optional domain/video hosting and quotas remain dependencies. | **UNCERTAIN**. Obtain explicit confirmation; display is not an interactive solver. |
| Downloadable supported local distribution — absent | Run a tested source-checkout release or supported installer offline after installation; reproduce with local native engine. | Real local execution, historical bundled sample. No paid/live publication; network needed initially and for current chain reads. | Source archive is not a supported installed wheel/app. Need first-party permission, complete third-party notices, per-OS verification, checksums, upgrade/uninstall and asset paths. Native binary identities differ per platform. | Packaging/QA/signing-policy/support effort; hosting downloads; optional OS signing services. No distribution was published. | **UNCERTAIN** even when technically ready. Currently BLOCKED. |
| Restricted authenticated interactive demo — not justified for minimum release | Potentially upload an allowed project and request bounded server proofs behind a real access gate. | Would perform live computation on a host, still no wallet/publication. Nothing in this row is an implemented hosted capability. | Requires explicit owner authorization, independent target-host isolation/load testing, auth, quotas, aggregate memory/CPU/process-tree containment, abuse limits, safe logs, retention/deletion, secrets management and operating responsibility. A password on the existing local launcher is insufficient. | Recurring compute/monitoring/auth costs plus security engineering; no measured budget or selected provider. | **UNCERTAIN**; access controls also need a judge onboarding plan. Defer. |

[GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
confirms static HTML/CSS/JavaScript hosting and availability for public repositories on
GitHub Free. This is a possible future infrastructure choice, not a deployed Flip URL,
price guarantee, rights clearance or hackathon-compliance confirmation. Hosting limits and
acceptable use must be reviewed for the selected account before activation.

## Important implementation distinction

The current `apps/web/dist` is a frontend for same-origin Python API routes. Its sample,
composition, comparison and replay actions call `/api/...`; the build does not contain a
JavaScript SAT engine. Uploading those files unchanged to static hosting would leave core
actions without their API. A static demonstration requires a separately reviewed display
mode/viewer; it must not return fabricated EQUIVALENT results from the normal live controls.

The supported [local launcher](../../packages/flip-api/src/flip_api/local.py) binds
127.0.0.1, rejects non-loopback/cross-origin access and disables framing/proxy-header trust.
Those checks are intentional. Do not change host bindings, forward a port, add a tunnel or
proxy the native worker to manufacture a judge URL. Child limits do not cover aggregate
service RSS; local CI is not a public-host security assessment.

## Recommended minimum release path

1. Owner resolves source licensing/material rights and obtains a human access/screen-reader
   check; adopt the reviewed quickstart draft without adding runtime features.
2. Record a captioned three-minute local demonstration with clear historical, synthetic and
   recorded labels; retain separate project/evidence/receipt files and their provenance.
3. Offer the pinned public repository plus supported local launcher and the video as the
   smallest reproducible package. Ask the organizer to confirm H3 **before relying on it**.
4. If a URL beyond those is necessary, propose a separately authorized static evidence
   viewer/video landing page. Build/review it only after the owner approves hosting and
   the organizer clarifies whether it suffices. Keep real proofs local.
5. Defer restricted hosted solver and all write-enabled work. These do not solve the current
   licensing/onboarding/access questions quickly enough to be the minimum safe path.

Draft organizer question for the owner to send, not sent by this audit:

> Would a developer-tool entry with a pinned Windows/Linux local launcher, public source,
> captioned walkthrough and reproducible project/evidence downloads meet the application
> access requirement? If a browser URL is mandatory, may it be an explicitly recorded,
> static evidence viewer while fresh native verification runs locally?

Until an answer and a usable tested access arrangement exist, judge access remains BLOCKED.
Use [the blocker register](M45_R2_RELEASE_BLOCKERS.md) for owners and acceptance evidence.
