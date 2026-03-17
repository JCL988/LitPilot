# Workflow: Literature Processing Pipeline

## Overview

This pipeline processes academic papers (PDF and DOCX) through structured
LLM agent prompts to produce consistent literature notes and a trackable
spreadsheet database. All outputs are aligned to your literature review
architecture.

## Phases

### Phase 1: Intake
- **Input:** PDF and DOCX files in `incoming/`
- **Action:** Extract text from each file (PyMuPDF for PDFs, python-docx for Word)
- **Output:** Raw text per paper

### Phase 2: Individual Analysis
- **Input:** Raw text per paper
- **Agent:** Literature Analyst (`bmad/agents/analyst.md`)
- **Action:** Generate structured note with section mapping + tracker row
- **Output:** One markdown file per paper in `summaries/individual/`
- **Output:** One row appended to `summaries/literature_tracker.xlsx`

### Phase 3: Batch Synthesis (run manually, after every 10-15 papers)
- **Input:** All individual summaries from `summaries/individual/`
- **Agent:** Literature Synthesiser (`bmad/agents/synthesiser.md`)
- **Action:** Coverage map, thematic clusters, theoretical audit, gap analysis
- **Output:** One synthesis report in `summaries/synthesis/`

### Phase 4: Cleanup (automatic)
- Move processed files from `incoming/` to `processed/`
- Log what was processed and when to `processing_log.csv`

## Setting Coverage Targets

Use the synthesis report's Coverage Map to track your progress. Define
minimum paper counts for each section of your literature review:

<!-- CUSTOMIZE: Replace with your own sections and targets -->

| Section | Minimum papers needed | Notes |
|---|---|---|
| [2.1 Section Title] | [5-8] | [Any notes on what to prioritise] |
| [2.2 Section Title] | [8-12] | [Any notes] |
| [2.3 Section Title] | [5-8] | [Any notes] |
| [2.4 Section Title] | [5-10] | [Any notes] |
| [2.5 Section Title] | [3-5] | [Any notes] |

## Typical Daily Workflow

```
# 1. Drop new PDFs into incoming/
# 2. Process them
python3 scripts/process_papers.py

# 3. Incrementally update the synthesis
python3 scripts/synthesise_batch.py

# 4. Periodically do a full re-synthesis (e.g., every 5th batch)
python3 scripts/synthesise_batch.py --full
```
