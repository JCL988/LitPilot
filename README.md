# LitPilot

Automate your PhD literature review using structured LLM agent prompts. Drop PDFs in a folder, get structured markdown notes, an Excel tracker, and cross-paper synthesis reports.

## What This Does

1. **Extracts text** from PDF and Word documents automatically
2. **Analyses each paper** using a customisable LLM agent prompt that maps findings to your specific literature review structure
3. **Tracks everything** in an Excel spreadsheet with methodology, relevance ratings, section mappings, and theoretical frameworks
4. **Synthesises across papers** to identify coverage gaps, thematic clusters, contradictions, and recommended actions

## What This Does NOT Do

- **Does not discover or retrieve papers** — you bring your own PDFs
- **Does not access paywalled content** — download papers yourself first
- **Does not produce a written literature review** — it produces structured notes and tracking to help you write one
- **Does not replace reading papers** — it accelerates triage and organisation
- **Quality depends on how well you customise the agent prompts** — generic prompts produce generic output

## Compared to Other Tools

There are many AI tools for academic research. This pipeline occupies a specific niche — here's how it relates to the landscape.

### Paper discovery tools (complementary — use alongside this pipeline)

| Tool | What it does | How it complements this pipeline |
|------|-------------|----------------------------------|
| [Semantic Scholar](https://www.semanticscholar.org) | Free AI-powered search across 214M+ papers with TLDR summaries | Find papers here, download PDFs, drop them into `incoming/` |
| [ResearchRabbit](https://www.researchrabbit.ai) | Citation network exploration — give it seed papers, get recommendations | Discover related work visually, then process the papers through this pipeline |
| [Connected Papers](https://www.connectedpapers.com) | Visual similarity graphs based on co-citation patterns | Identify clusters of related work to batch-process |
| [Litmaps](https://www.litmaps.com) | Literature mapping with temporal citation networks | Map your field, then use this pipeline to analyse what you find |
| [Inciteful](https://inciteful.xyz) | Citation network analysis and cross-domain literature bridging | Find interdisciplinary connections, then analyse the papers here |

These tools help you **find** papers. This pipeline helps you **analyse and organise** them.

### AI analysis tools (alternatives — this pipeline differs in key ways)

| Tool | Approach | Key difference from this pipeline |
|------|----------|-----------------------------------|
| [Elicit](https://elicit.com) | SaaS platform with structured extraction into tables | Closest commercial equivalent. Elicit searches for you and extracts into tables, but costs $12-79/month and you can't customise the extraction schema. This pipeline is free (beyond API costs), fully customisable, and you own all outputs locally. |
| [SciSpace](https://scispace.com) | All-in-one platform: search, chat with PDF, literature tables | Broader but shallower — summarisation is generic, not mapped to your specific thesis structure. |
| [Consensus](https://consensus.app) | Question-answering across 200M+ papers | Answers specific questions well, but doesn't produce structured per-paper notes or track coverage across your literature review sections. |
| [Google NotebookLM](https://notebooklm.google) | Upload documents, get AI insights grounded in your sources | Good for ad-hoc exploration, but no structured extraction, no Excel tracking, no cross-paper synthesis against your thesis architecture. |
| [Scite](https://scite.ai) | Classifies citations as supporting, contradicting, or mentioning | Useful for understanding citation context ($12/month), but doesn't summarise or map papers to your review structure. |

### Open-source projects (alternatives with different design goals)

| Project | What it does | Key difference |
|---------|-------------|----------------|
| [PaperQA2](https://github.com/Future-House/paper-qa) | RAG-based Q&A over your papers with citations | Optimised for answering specific questions, not producing structured per-paper notes. No thesis-aligned extraction or Excel tracking. |
| [LitLLM](https://github.com/LitLLM/LitLLM) | Generates "Related Work" sections from an abstract | Writes prose, not structured notes. Focused on a single output (related work text), not an ongoing review database. |
| [GPT-Researcher](https://github.com/assafelovic/gpt-researcher) | Autonomous agent that produces research reports from web sources | General-purpose, not academic-focused. Sources from the web, not your curated PDFs. |
| [STORM](https://github.com/stanford-oval/storm) | Generates Wikipedia-style articles from web research (Stanford) | Impressive for topic overviews, but web-sourced rather than working with your specific paper collection. |
| [OpenScholar](https://github.com/AkariAsai/OpenScholar) | Answers scientific queries from 45M open-access papers (Allen AI) | Published in Nature. Excellent citation accuracy, but Q&A-focused — doesn't produce structured notes mapped to your thesis. |

### Where this pipeline fits

Most tools either **discover papers** or **answer questions about them**. Few do what a PhD student actually needs day-to-day: process a batch of PDFs into **consistent, structured notes** mapped to your specific thesis architecture, track everything in a **filterable spreadsheet**, and **synthesise across papers** to find gaps.

This pipeline is designed to sit between discovery and writing:

```
Discovery (Semantic Scholar, ResearchRabbit, etc.)
    → Download PDFs
    → This pipeline (analyse, track, synthesise)
    → You write the literature review
```

**Key advantages over alternatives:**
- **Fully customisable** — your sections, your frameworks, your structure
- **Local and private** — your papers and notes stay on your machine
- **No subscription** — pay only for API calls (~$0.10-0.30 per paper)
- **Incremental synthesis** — add papers over months without re-processing
- **You own the output** — plain markdown and Excel, no vendor lock-in

## Why This Approach Works

Most researchers use ChatGPT or Claude ad-hoc — paste a paper, ask a question, get an answer, lose it. This pipeline uses **structured agent prompts** (the BMAD approach) that force the LLM to produce consistent, comparable output across every paper. The result is a literature database you can actually filter, sort, and build on.

The key differentiator is the **agent prompt design**. You define your literature review sections, theoretical frameworks, and empirical chapters once. Every paper gets analysed against that same structure, making cross-paper comparison trivial.

## Architecture

```
incoming/                     You drop PDFs here
    |
    v
[process_papers.py]           Extracts text, sends to Claude API
    |                         with your analyst agent prompt
    v
summaries/individual/         One structured markdown note per paper
summaries/literature_tracker.xlsx   One row per paper (filterable)
    |
    v
[synthesise_batch.py]         Reads all notes, sends to Claude API
    |                         with your synthesiser agent prompt
    v
summaries/synthesis/          Cross-paper synthesis report
```

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/JCL988/LitPilot.git
cd LitPilot
```

### 2. Set up a Python virtual environment

A virtual environment keeps this project's dependencies isolated from the rest of your system. This is recommended for all users.

```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt. Now install the dependencies:

```bash
pip install -r requirements.txt
```

> **Note:** You need to run `source venv/bin/activate` each time you open a new terminal window before using the pipeline. To deactivate the environment when you're done, run `deactivate`.

### 3. Set up your API key

```bash
cp .env.example .env
```

Open `.env` in any text editor and replace `sk-ant-your-key-here` with your actual Anthropic API key. Get one at [console.anthropic.com](https://console.anthropic.com/settings/keys).

### 4. Customise the agent prompts for your research

This is the most important step. Edit these two files:

- **`bmad/agents/analyst.md`** — Defines how each paper is analysed
- **`bmad/agents/synthesiser.md`** — Defines how papers are synthesised together

See the [Customisation Guide](#customisation-guide) below for detailed instructions.

> **Important — the pipeline will refuse to run if you skip this step.** The processing script checks for placeholder text and will exit with an error if it finds any. You must replace **all** of the following placeholders in `bmad/agents/analyst.md`:
>
> | Placeholder | Location | What to replace it with |
> |---|---|---|
> | `[YOUR TOPIC — e.g., "climate policy..."]` | Line 19 (Researcher Context) | Your actual research topic |
> | `[Section Title]` | Lines 44-48 (Section Map table) | Your literature review section names |
> | `[Section Title]` | Lines 151-152 (Section Mapping output) | Same section names, matching the table above |
>
> The script specifically checks for the strings `[YOUR TOPIC` and `[Section Title]`. Even if you customise the table, the pipeline will still fail if these strings remain anywhere else in the file. A quick way to verify:
>
> ```bash
> grep -n "\[YOUR TOPIC\|\[Section Title\]" bmad/agents/analyst.md
> ```
>
> If this returns no results, you're good to go.

### 5. Process papers

```bash
# Drop your PDFs into the incoming/ folder, then:
python3 scripts/process_papers.py

# Or preview what will be processed without spending money:
python3 scripts/process_papers.py --dry-run
```

The `--dry-run` flag extracts text and estimates cost for each paper without calling the API.

### 6. Synthesise

```bash
# After processing papers, generate a cross-paper synthesis:
python3 scripts/synthesise_batch.py

# Or force a full re-synthesis:
python3 scripts/synthesise_batch.py --full
```

## Customisation Guide

### Step 1: Define your literature review sections

Open `bmad/agents/analyst.md` and find the **Literature Review Section Map** table. Replace the placeholder rows with your actual sections:

```markdown
| Code | Section | Covers |
|------|---------|--------|
| 2.1  | Theoretical Background | Key theories: institutional theory, resource dependence |
| 2.2  | Policy Context | EU climate governance framework, Paris Agreement implementation |
| 2.3  | Implementation Literature | Street-level bureaucracy, multi-level governance |
| 2.4  | Comparative Studies | Cross-country policy comparisons, federal vs unitary systems |
| 2.5  | Empirical Evidence | Quantitative evaluations, case studies |
```

### Step 2: Define your empirical chapters

In the same file, find the **Researcher Context** section and describe your empirical chapters:

```markdown
- **Chapter 4 (Quantitative):** Panel data regression on policy adoption rates
  across 27 EU member states (2010-2023)
- **Chapter 5 (Qualitative):** Comparative case study of Germany and Poland
- **Chapter 6 (Text Analysis):** NLP analysis of national implementation plans
```

### Step 3: Define your theoretical frameworks

Find the **Theoretical Framework Engagement** section and list the frameworks central to your project:

```markdown
- **Kingdon (multiple streams):**
- **Sabatier (advocacy coalition):**
- **DiMaggio & Powell (institutional isomorphism):**
- **Other notable framework:**
```

### Step 4: Update the synthesiser prompt

Open `bmad/agents/synthesiser.md` and make the same changes:
- Same section codes and titles as in `analyst.md`
- Same empirical chapters
- Same theoretical frameworks

**Important:** The section codes must be identical in both files. The synthesiser aggregates data using the codes the analyst produces.

### Step 5: Update the workflow targets (optional)

Edit `bmad/workflows/literature-processing.md` to set paper count targets for each section.

## Configuration

Edit `config.py` to change:

| Setting | Default | Description |
|---------|---------|-------------|
| `ANALYSIS_MODEL` | `claude-sonnet-4-20250514` | Model for individual paper analysis |
| `SYNTHESIS_MODEL` | `claude-opus-4-6` | Model for cross-paper synthesis |
| `MAX_CONCURRENT` | `1` | Parallel API calls (increase for speed) |
| `MAX_PDF_PAGES` | `95` | Maximum pages to extract per PDF |
| `TRACKER_HEADERS` | [see file] | Excel column names — must match analyst prompt fields |

## Processing Papers

The processing script has two modes:

**Process (default):** Extracts text from each PDF/DOCX in `incoming/`, sends it to Claude with your analyst agent prompt, and saves a structured markdown note plus an Excel tracker row. Processed files are moved to `processed/` automatically.

```bash
python3 scripts/process_papers.py
```

**Dry run (`--dry-run`):** Extracts text and estimates the API cost for each paper without making any API calls. Use this to preview what will be processed and how much it will cost before committing.

```bash
python3 scripts/process_papers.py --dry-run
```

## Incremental vs Full Synthesis

The synthesis script has two modes:

**Incremental (default):** Only sends new papers plus the previous synthesis report to Claude. This is cheaper and faster — ideal for your daily workflow when you add a few papers at a time.

```bash
python3 scripts/synthesise_batch.py
```

**Full (`--full`):** Re-synthesises all papers from scratch. Use this when you want a clean baseline, after removing papers, or periodically (e.g., every 5th batch) to prevent drift.

```bash
python3 scripts/synthesise_batch.py --full
```

The pipeline tracks which papers were included in each synthesis via a manifest file (`summaries/synthesis/last_synthesis_manifest.json`). If it detects that papers have been removed since the last run, it automatically falls back to a full synthesis. For very large collections, it splits papers into batches that fit within the context window.

## Cost Estimates

| Operation | Model | Approximate Cost |
|-----------|-------|-----------------|
| Analyse one paper | Sonnet | $0.10 - $0.30 |
| Synthesise 20 papers | Opus | $1.50 - $3.00 |
| Synthesise 20 papers | Sonnet (cheaper) | $0.30 - $0.80 |

To use Sonnet for synthesis (cheaper but less nuanced), change `SYNTHESIS_MODEL` in `config.py`.

## Output Examples

### Individual note (summaries/individual/)

Each paper produces a structured markdown note with:
- Abstract summary, research gap, hypothesis
- Methodology and key techniques
- Key mechanisms and findings with magnitudes
- Critical analysis (strengths, limitations, open questions)
- Section-by-section relevance mapping
- Theoretical framework engagement
- Potential citations with section codes
- Action items
- Final assessment (innovation, evidence quality, relevance)

### Excel tracker (summaries/literature_tracker.xlsx)

One row per paper with columns for filtering:
- Title, Authors, Year, Journal
- Methodology, Relevance (HIGH/MEDIUM/LOW)
- Key Takeaway
- Primary and all relevant sections
- Empirical chapter relevance
- Theoretical frameworks engaged

### Synthesis report (summaries/synthesis/)

Cross-paper analysis including:
- Coverage map (which sections are well-covered vs under-covered)
- Thematic clusters with consensus and tensions
- Methodological landscape
- Theoretical framework audit
- Contradictions and debates
- Gap analysis with search term recommendations

## Folder Structure

```
.
├── config.py                  # All settings in one place
├── scripts/
│   ├── process_papers.py      # Processes PDFs → individual notes
│   └── synthesise_batch.py    # Synthesises notes → synthesis report
├── bmad/
│   ├── agents/
│   │   ├── analyst.md         # Agent prompt for individual analysis
│   │   └── synthesiser.md     # Agent prompt for synthesis
│   └── workflows/
│       └── literature-processing.md  # Workflow documentation
├── incoming/                  # Drop PDFs here
├── processed/                 # PDFs move here after processing
├── summaries/
│   ├── individual/            # One markdown note per paper
│   ├── synthesis/             # Cross-paper synthesis reports
│   └── literature_tracker.xlsx # Excel tracker
├── processing_log.csv         # Processing history
├── .env                       # Your API key (not committed)
├── .env.example               # Template for .env
└── requirements.txt           # Python dependencies
```

## Troubleshooting

**"ANTHROPIC_API_KEY not found"**
- Make sure you copied `.env.example` to `.env` and added your key
- The key should start with `sk-ant-`

**"No PDF or DOCX files found"**
- Files must be in the `incoming/` folder
- Check that they have `.pdf` or `.docx` extensions

**"Very little text extracted" or blank summaries**
- The PDF is likely scanned (image-based). You need OCR first
- Try Adobe Acrobat's "Recognize Text" or a tool like `ocrmypdf`

**Rate limit errors**
- The pipeline has built-in retry with exponential backoff
- If persistent, reduce `MAX_CONCURRENT` in `config.py` to `1`

**Paper too long**
- Papers exceeding the context window are automatically chunked
- Very long papers (e.g., book chapters) may produce less detailed summaries

**Excel tracker columns don't match**
- If you add or remove fields in `analyst.md`'s CSV section, update `TRACKER_HEADERS` in `config.py` to match

## Contributing

Contributions are welcome! If you have ideas for improving the agent prompts, adding new features, or supporting other LLM providers, please open an issue or pull request.

## License

MIT License — see [LICENSE](LICENSE) for details.
