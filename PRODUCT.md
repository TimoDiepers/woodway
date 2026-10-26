# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **In the room (primary):** the audience of the PhD defence talk at RWTH Aachen on 13.11.2026, a mix of the examination committee and the public (colleagues, family, friends). Most are engineers, not climate scientists. The talk has to be clear to non-specialists and still hold up under expert questions from the committee.
- **The speaker:** Timo Diepers, who clicks through the deck live with speaker notes on a second screen and opens backup slides during Q&A.
- **Afterwards:** people reading the deck online without the speaker (woodway.tidi.dev/slides and the shared artifact), and readers of a static PDF/print export.

## Product Purpose

A 45-minute defence talk, *Aufforstung als Klima-„Technologie“*. It asks how much afforestation actually cools the climate once you follow the carbon past the tree. It also asks how much direct air capture has to do on top. The talk widens the system boundary step by step: one tree, then the carbon cycle, then the Earth's energy balance, then every reforestable 0.5° cell, then DAC.

The talk succeeds when the mixed audience follows the chain from tree to temperature path. They should leave with the core findings: albedo can outweigh CO₂ removal, only part of the reforestable land actually cools, and trees alone are neither large enough nor fast enough. The committee should find the method sound.

## Positioning

It takes a simple, viral back-of-the-envelope calculation (Bastin et al.: plant enough trees and solve the climate) and redoes it with a year-by-year model. That model covers growth, the carbon-cycle response (FaIR), albedo and clouds, and the area really available. The result is a temperature path to 2100 rather than one number. The calculation is done at the start with UNEP 2026 numbers and done again at the end of the potential chapter with the model.

## Operating Context

- Projected 16:9 in a lecture hall, clicked step by step (`data-step`), with a speaker view and notes.
- Must run offline from a local file: no network dependence in the hall.
- Backup slides are opened on demand during questions.
- Also read online after the talk, and exported to PDF/print, where animations are absent and every slide's final state must stand on its own.
- Built from `deck/src` with `uv run python deck/build.py` into `deck/dist/index.html`. The model and data live in the same repository.

## Capabilities and Constraints

- Slide text is in German; code, comments and repository docs are in English.
- Talk length is 45 minutes, and the current deck fits it (tested by the speaker).
- No invented numbers: every figure comes from the model in this repository or a cited source, with the source on the slide.
- Terminology on the slides: Albedoänderung Δα_Baum and ΔQ̇_Albedo; "Reflexion" in the slide titles of the albedo chapter.
- The UNEP Emissions Gap Report 2026 scenarios are the reference frame: 2.8 °C under current policy, 1.7 °C best case with a 1.8 °C peak, and about 320 Gt CO₂ of removal to get back to 1.5 °C. The 320 Gt figure has not yet been checked against the primary report.

## Brand Commitments

- Speaker and author: Timo Diepers, RWTH Aachen (TTD).
- The interactive map Woodway (woodway.tidi.dev) is part of the talk and is live on its last slide.

## Evidence on Hand

- Model results and chart data: `deck/chart_data/`, `deck/assets/data/`, `results/`, and `data/` (raw inputs are not in git).
- Method notes with literature: `docs/methods/`.
- Cited sources include Bastin et al. 2019 and its Science comments, UNEP EGR 2026, Duveiller et al. 2018/2021, Walker et al. 2022, Poore & Nemecek 2018, Leach et al. 2021 (FaIR), Smith et al. 2024 and Joos et al. 2013.
- No testimonials, endorsements or results beyond the model and the cited literature exist; none may be fabricated.

## Product Principles

1. **Follow the carbon past the tree.** Each step widens the system boundary, and nothing is skipped that changes the answer.
2. **Clear to non-specialists, robust for the committee.** Lead with intuition and pictures; keep the formulas and assumptions within reach for questions.
3. **Every number is traceable.** It comes from the model or a cited source, and the source is visible on the slide.
4. **Honest about limits.** The assumptions are optimistic and stated as such, the uncertain parameters are named, and only the climate effect is assessed.
5. **Every final state stands alone.** A slide's last click must read correctly in the PDF and online, without the speaker.
