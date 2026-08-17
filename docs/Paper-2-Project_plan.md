# Paper-to-Project Agent — Final Build Plan

A local-first agentic system that converts a research paper into a feasibility-checked, staged implementation blueprint, delivered through a Windows desktop mascot. Validated against Varun's own VLCD → E-SGCD thesis work as ground truth.

28 days, 4 phases, zero overlapping work between phases.

---

## Architecture

```
LangGraph 6-agent core (Days 1–14)
   ↕ Pydantic structured schemas, Ollama structured output
Ollama local runtime — Qwen2.5-Coder-7B / Llama-3.1-8B (Q4_K_M)
   ↕
FastAPI bridge — /analyze /status /stream/{run_id} (SSE)
   ↕
Electron desktop app — mascot + docked sidebar (Days 15–21)
   ↕ active-win polling + Ctrl+Shift+P hotkey fallback
Windows Installer (NSIS via electron-builder) — Days 26–28
```

## Design decisions made explicit (don't relitigate these mid-build)

- **Agent core first, UI second.** The pipeline's correctness is the actual risk in this project — validate it against real VLCD → E-SGCD ground truth before investing in mascot polish.
- **Gap-Finding and Feasibility run sequentially, not in parallel**, for v1. Feasibility often needs Gap-Finding's confirmed hyperparameters (e.g. batch size) to estimate cost accurately — parallelizing risks judging against incomplete data. Revisit as an optimization once the sequential version is proven correct.
- **Model: Qwen2.5-Coder-7B**, not a generic instruct model — the output is implementation-plan/code-adjacent, so a code-tuned model is the better fit.
- **Structured output via Pydantic schemas + Ollama's structured decoding mode**, not free-text parsing — directly reduces hallucinated values slipping through as "confirmed."

---

## Phase 1 — Agentic core (Days 1–14)

**Day 1 — Environment + parsing pipeline**
- Ollama installed, pull Qwen2.5-Coder-7B (or Llama-3.1-8B Q4_K_M as fallback)
- Section-aware PDF parser (PyMuPDF/pdfplumber) with pruning of citations/acknowledgments/affiliations to save context budget
- *Test:* clean section tree extracted from the VLCD paper, no missing equations, no bloated irrelevant text

**Day 2 — Paper Ingestion Agent**
- LangGraph node wrapping the parser, Pydantic schema output via Ollama structured decoding
- *Test:* schema stays valid on malformed/partial input

**Day 3 — Method Decomposition Agent**
- Converts method section into a component graph (encoder, fusion, decoder, losses, training regime)
- *Test:* runs cleanly on VLCD's method section

**Day 4 — Validation checkpoint 1** 🔒
- Compare agent's VLCD component graph against your real thesis notes
- *Test:* correctly isolates Swin Transformer, RemoteCLIP, and the fusion module as core components

**Day 5 — Gap-Finding Agent**
- Tavily + GitHub API search for missing hyperparameters
- Confidence tagging: `CONFIRMED` / `INFERRED` / `ASSUMED`
- *Test:* tagging function correct on known-answer cases; searches return relevant results

**Day 6 — Integration checkpoint** 🔒
- Run Ingestion → Decomposition → Gap-Finding end-to-end on VLCD
- *Test:* zero unconfirmed values stated as fact — this is the critical failure mode

**Day 7 — Feasibility Agent**
- Constraint validator (GPU/VRAM, dataset size, timeline) against the component graph
- Substitute-suggestion engine for compute-heavy components
- *Test:* feed your real old constraints, check what it flags

**Day 8 — Validation checkpoint 2 (strongest evidence)** 🔒
- Does the agent independently propose something close to your real RemoteCLIP → lightweight segmentation head swap?
- *Test:* structured comparison, document agreement/divergence with reasoning

**Day 9 — Build Sequencing Agent**
- Converts feasibility-adjusted graph into dependency-ordered milestones
- *Test:* cheap/validating steps always precede compute-heavy ones

**Day 10 — Adaptation Report Agent**
- Synthesizes everything into one portfolio-grade markdown report
- *Test:* renders cleanly, no missing sections

**Day 11 — Full LangGraph orchestration**
- Assemble the graph: Ingestion → Decomposition → Gap-Finding → Feasibility → Sequencing → Report (sequential, per the design decision above)
- Loop-back edge for hyperparameter refinement when Feasibility needs a re-search
- *Test:* no agent silently drops fields from shared state

**Day 12 — End-to-end validation checkpoint** 🔒
- Full pipeline on VLCD, real constraints, start to finish
- *Test:* compare final report against your actual completed E-SGCD plan — your strongest portfolio artifact

**Day 13 — Generalization + edge cases**
- Run on 2–3 unfamiliar papers with different layouts (single-column, IEEE double-column, NeurIPS)
- Test malformed PDFs, missing sections, tool timeouts
- *Test:* graceful degradation with fallback tags, never a silent crash

**Day 14 — Local runtime benchmarking**
- Confirm full pipeline runs entirely on local Ollama model, per-node token budgets applied
- *Test:* document latency and structured-output adherence vs. any earlier API-based testing

---

## Phase 2 — Desktop UI (Days 15–21)

**Day 15 — Character rig + asset creation**
- One shared modular SVG rig (head, glasses, hair, torso, limbs, props) with standardized anchor points
- Reskin into 4 variants: nerdy man, nerdy woman, nerdy adult male, nerdy adult female
- *Test:* all 4 render in a static harness, no seam misalignment

**Day 16 — DPI-aware transparent Electron shell**
- Frameless, transparent, always-on-top window
- `setIgnoreMouseEvents` pass-through for non-character regions
- Multi-monitor/DPI handling via `screen.getDisplayNearestPoint()` and `scaleFactor` (125–150% Windows scaling)
- *Test:* drag across monitors with different DPI, confirm no clipping or black-border artifacts

**Day 17 — Win32 taskbar detection + state machine**
- `koffi`/`ffi-napi` query for taskbar bounds (`ABM_GETTASKBARPOS`)
- 4 CSS-transform animation states: Sleeping, Idle/Curious, Reading, Working — built once, works across all 4 characters via the shared rig
- Install-complete intro sequence: climbs from taskbar, dust-off, greeting line
- *Test:* taskbar top/bottom/side/auto-hide configs; animation correctness on at least 2 of 4 characters

**Day 18 — Active window detection + hotkey fallback**
- `active-win` polling, pattern-match PDF viewer processes + paper-site keywords in window titles
- Global hotkey `Ctrl+Shift+P` via `globalShortcut`; mascot click also opens the panel
- *Test:* detection accuracy on 5 real papers / 5 unrelated windows; hotkey works regardless of detection state, no shortcut collisions

**Day 19 — Docked sidebar panel**
- Slide-out window anchored to the active monitor's edge
- 3-tier option UI (brief / detailed / implement), agent activity stream placeholder, markdown renderer shell
- *Test:* no flicker or unexpected minimize on window focus shifts

**Day 20 — Onboarding + character selection**
- First-run prompt: "Do you want the mascot on your screen?" → yes shows the 4-character picker, then taskbar intro for the chosen character (mentions the hotkey); no leaves a headless system-tray mode
- Preference stored via `electron-store`
- *Test:* both accept/decline branches; switching characters mounts the correct SVG set with no leftover parts

**Day 21 — UI stress testing** 🔒
- Rapid resolution changes, sleep/wake cycles, full-screen app interruptions, multi-monitor disconnects
- *Test:* mascot never gets stuck, misplaced, or crashes the Electron process under these conditions

---

## Phase 3 — Integration & real-time streaming (Days 22–25)

**Day 22 — FastAPI bridge**
- Lightweight wrapper around the LangGraph engine with lifecycle hooks
- Endpoints: `/analyze`, `/status`, `/stream/{run_id}`
- *Test:* backend sub-process boots and terminates in tandem with the Electron main process

**Day 23 — SSE event stream**
- Server-Sent Events emitting granular node-transition updates ("Decomposing Swin backbone…", "Searching GitHub for batch size…")
- *Test:* frontend parses the stream without dropped events or UI lockup

**Day 24 — Mascot reactions + sidebar rendering**
- Bind mascot state directly to backend events: Ingestion/Decomposition → Reading; Gap-Finding → Investigating; complete → Ready
- Sidebar streams the final report as rendered markdown (syntax highlighting, expandable milestone checklist)
- *Test:* rapid state transitions trigger the correct animation every time, no lag/mismatch

**Day 25 — Full system integration checkpoint** 🔒
- Complete run: hotkey/detection triggers mascot → user picks depth → streaming progress in sidebar → structured report displays
- *Test:* mid-run cancel/abort cleanly resets the mascot to idle and releases resources, doesn't hang

---

## Phase 4 — Packaging (Days 26–28)

**Day 26 — Backend binary + Electron packaging**
- Bundle the Python backend (PyInstaller) into a standalone executable
- Configure `electron-builder` for Windows (NSIS `.exe`), package native bindings (`koffi`/`ffi-napi`/`active-win`)
- *Test:* standalone backend runs on a machine with no Python installed

**Day 27 — Ollama dependency health check**
- Installer pre-flight check for Ollama presence + target model weights
- Automated fallback prompt to pull the model if missing (`ollama pull qwen2.5-coder:7b`)
- *Test:* launch on a machine without Ollama, confirm the setup prompt guides the user correctly

**Day 28 — Clean-VM install + final polish** 🔒
- Full installer run in a fresh Windows 11 sandbox/VM, no dev tools present
- Validate taskbar placement, hotkey registration, backend auto-spawn, uninstall cleanup
- Record a short demo covering mascot reactions + plan generation; finalize the VLCD validation write-up for your portfolio

---

## Protected checkpoints (🔒 above) — do not skip under time pressure
Days 4, 6, 8, 12 (agent validation against your real thesis work), Day 21 (UI reliability), Day 25 (full system integration), Day 28 (clean-install proof).

These four agent-validation days are what separate this from "another RAG wrapper" — they're the evidence that the reasoning is actually grounded in something real, not just plausible-sounding output.

## Deferred for later (explicitly out of scope for v1)
- Parallelizing Gap-Finding/Feasibility branches (revisit once sequential version is proven)
- Cloud/API-key optional mode
- Chrome extension + native messaging bridge (needed for macOS/Linux)
- Text-scanning fallback for generic-titled PDFs (hotkey covers this for now)
- Export-to-Jira/Linear (nice-to-have, not core)