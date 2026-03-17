#!/usr/bin/env python3
"""
Batch Synthesis Script
Reads all individual summaries and produces a cross-paper synthesis report.

Usage:
  python3 scripts/synthesise_batch.py          # incremental (default)
  python3 scripts/synthesise_batch.py --full   # full re-synthesis

Features:
  - Smart batching: splits large sets into rounds instead of hard truncation
  - Retry with exponential backoff
  - Cost estimation before calling the API
  - Incremental mode: only sends new papers + previous synthesis
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Allow importing config from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import anthropic

from config import (
    PROJECT_ROOT, SUMMARIES_DIR, SYNTHESIS_DIR, AGENT_DIR,
    SYNTHESIS_MODEL, SYNTHESIS_MAX_TOKENS, MAX_RETRIES,
    CHARS_PER_TOKEN, MAX_SYNTHESIS_INPUT_TOKENS,
    SYNTHESIS_INPUT_COST, SYNTHESIS_OUTPUT_COST,
)

MAX_CHARS_PER_BATCH = MAX_SYNTHESIS_INPUT_TOKENS * CHARS_PER_TOKEN
MANIFEST_FILE = SYNTHESIS_DIR / "last_synthesis_manifest.json"


# ══════════════════════════════════════════════
# MANIFEST (tracks which papers were in the last synthesis)
# ══════════════════════════════════════════════

def load_manifest() -> dict:
    """Load the manifest from the last synthesis run."""
    if not MANIFEST_FILE.exists():
        return {}
    try:
        return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_manifest(summaries: list, report_file: Path):
    """Save a manifest recording which papers were included."""
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "report": str(report_file),
        "papers": [s.name for s in summaries],
    }
    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def find_latest_synthesis() -> Path | None:
    """Find the most recent synthesis report."""
    reports = sorted(
        SYNTHESIS_DIR.glob("synthesis_*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    for r in reports:
        if "batch" not in r.name:
            return r
    return None


# ══════════════════════════════════════════════
# RETRY LOGIC
# ══════════════════════════════════════════════

def call_claude_with_retry(client, model, max_tokens, system, messages) -> tuple:
    """
    Call Claude API with exponential backoff.
    Returns (response_text, input_tokens, output_tokens).
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            result = ""
            for block in response.content:
                if block.type == "text":
                    result += block.text

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            return result, input_tokens, output_tokens

        except anthropic.RateLimitError:
            wait = 2 ** attempt
            print(f"  Rate limited. Waiting {wait}s (attempt {attempt}/{MAX_RETRIES})...")
            time.sleep(wait)

        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                wait = 2 ** attempt
                print(f"  Server error ({e.status_code}). Waiting {wait}s "
                      f"(attempt {attempt}/{MAX_RETRIES})...")
                time.sleep(wait)
            else:
                raise

        except anthropic.APIConnectionError:
            wait = 2 ** attempt
            print(f"  Connection error. Waiting {wait}s "
                  f"(attempt {attempt}/{MAX_RETRIES})...")
            time.sleep(wait)

    print("ERROR: API request failed after all retries.")
    sys.exit(1)


# ══════════════════════════════════════════════
# COST ESTIMATION
# ══════════════════════════════════════════════

def estimate_cost(text: str, agent_prompt: str) -> tuple:
    """Estimate token count and cost before calling the API."""
    input_chars = len(text) + len(agent_prompt)
    est_input_tokens = input_chars // CHARS_PER_TOKEN
    est_output_tokens = SYNTHESIS_MAX_TOKENS

    input_cost = (est_input_tokens / 1_000_000) * SYNTHESIS_INPUT_COST
    output_cost = (est_output_tokens / 1_000_000) * SYNTHESIS_OUTPUT_COST
    total_cost = input_cost + output_cost

    return est_input_tokens, est_output_tokens, total_cost


# ══════════════════════════════════════════════
# BATCHING
# ══════════════════════════════════════════════

def split_into_batches(summaries: list) -> list:
    """
    Split summaries into batches that fit within the context window.
    Each batch is a list of (filepath, content) tuples.
    """
    batches = []
    current_batch = []
    current_chars = 0

    for s in summaries:
        content = s.read_text(encoding="utf-8")
        entry = f"\n\n{'='*60}\n{content}"
        entry_chars = len(entry)

        if current_chars + entry_chars > MAX_CHARS_PER_BATCH and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_chars = 0

        current_batch.append((s.name, entry))
        current_chars += entry_chars

    if current_batch:
        batches.append(current_batch)

    return batches


# ══════════════════════════════════════════════
# INCREMENTAL SYNTHESIS
# ══════════════════════════════════════════════

def run_incremental(summaries, agent_prompt):
    """
    Send only new papers + the previous synthesis report to Claude.
    Falls back to full synthesis if needed.
    """
    manifest = load_manifest()
    prev_papers = set(manifest.get("papers", []))
    all_papers = {s.name for s in summaries}
    new_papers = all_papers - prev_papers
    removed_papers = prev_papers - all_papers

    if removed_papers:
        print(f"Detected {len(removed_papers)} removed paper(s).")
        print("  Running full synthesis to reflect removals.\n")
        return run_full(summaries, agent_prompt)

    if not new_papers:
        print("No new papers since last synthesis. Nothing to do.")
        print("  Use --full to force a complete re-synthesis.")
        return

    prev_report_path = Path(manifest.get("report", ""))
    if not prev_report_path.exists():
        prev_report_path = find_latest_synthesis()
    if not prev_report_path or not prev_report_path.exists():
        print("No previous synthesis report found. Running full synthesis instead.\n")
        return run_full(summaries, agent_prompt)

    prev_report = prev_report_path.read_text(encoding="utf-8")
    if "\n---\n" in prev_report:
        prev_report = prev_report.split("\n---\n", 1)[1]

    new_summaries = [s for s in summaries if s.name in new_papers]
    new_text = ""
    for s in sorted(new_summaries):
        content = s.read_text(encoding="utf-8")
        new_text += f"\n\n{'='*60}\n{content}"

    print(f"Incremental mode:")
    print(f"  Previous synthesis: {prev_report_path.name} ({len(prev_papers)} papers)")
    print(f"  New papers: {len(new_papers)}")
    for s in sorted(new_summaries):
        print(f"    + {s.name}")
    print(f"  Total after update: {len(all_papers)}")
    print()

    client = anthropic.Anthropic()

    user_content = (
        f"Below is your previous synthesis report covering {len(prev_papers)} papers. "
        f"I have {len(new_papers)} new papers to add. Please produce an UPDATED "
        f"synthesis that fully integrates the new papers into the existing analysis. "
        f"Update all sections: coverage map, thematic clusters, methodological "
        f"landscape, theoretical audit, contradictions, and gaps.\n\n"
        f"PREVIOUS SYNTHESIS:\n\n{prev_report}\n\n"
        f"NEW PAPER SUMMARIES:\n\n{new_text}"
    )

    est_input, est_output, est_cost = estimate_cost(user_content, agent_prompt)
    print(f"  Estimated: ~{est_input:,} input tokens, up to {est_output:,} output tokens")
    print(f"  Estimated cost: ~${est_cost:.2f} USD")

    if len(user_content) > MAX_CHARS_PER_BATCH:
        print("\n  Incremental payload too large for context window.")
        print("  Falling back to full synthesis.\n")
        return run_full(summaries, agent_prompt)

    print(f"\n  Sending to Claude ({SYNTHESIS_MODEL})...")
    result, in_tokens, out_tokens = call_claude_with_retry(
        client=client,
        model=SYNTHESIS_MODEL,
        max_tokens=SYNTHESIS_MAX_TOKENS,
        system=agent_prompt,
        messages=[{"role": "user", "content": user_content}],
    )

    actual_cost = (
        (in_tokens / 1_000_000) * SYNTHESIS_INPUT_COST
        + (out_tokens / 1_000_000) * SYNTHESIS_OUTPUT_COST
    )

    print(f"  Actual: {in_tokens:,} input + {out_tokens:,} output tokens")
    print(f"  Actual cost: ${actual_cost:.2f} USD")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_file = SYNTHESIS_DIR / f"synthesis_{timestamp}.md"

    paper_list = "\n".join(f"  - {s.stem.replace('_note', '')}" for s in summaries)
    new_list = "\n".join(f"  - {s.stem.replace('_note', '')}" for s in sorted(new_summaries))

    header = (
        f"# Literature Synthesis Report (incremental update)\n\n"
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"**Papers synthesised:** {len(all_papers)}\n"
        f"**New papers in this update:** {len(new_papers)}\n"
        f"**Based on:** {prev_report_path.name}\n"
        f"**Model:** {SYNTHESIS_MODEL}\n"
        f"**Total tokens:** {in_tokens:,} input + {out_tokens:,} output\n"
        f"**Cost:** ${actual_cost:.2f} USD\n\n"
        f"**New papers added:**\n{new_list}\n\n"
        f"**All papers included:**\n{paper_list}\n\n---\n\n"
    )

    output_file.write_text(header + result, encoding="utf-8")
    save_manifest(summaries, output_file)

    print()
    print("=" * 60)
    print(f"Incremental synthesis complete.")
    print(f"  Report:     {output_file}")
    print(f"  New papers: {len(new_papers)}")
    print(f"  Total:      {len(all_papers)}")
    print(f"  Cost:       ${actual_cost:.2f} USD")


# ══════════════════════════════════════════════
# FULL SYNTHESIS
# ══════════════════════════════════════════════

def run_full(summaries, agent_prompt):
    """Full synthesis of all summaries."""
    print(f"Full synthesis mode: {len(summaries)} papers.\n")

    batches = split_into_batches(summaries)
    total_batches = len(batches)

    if total_batches > 1:
        print(f"Splitting into {total_batches} batches to fit context window.\n")

    client = anthropic.Anthropic()
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0
    batch_results = []

    for batch_idx, batch in enumerate(batches, 1):
        paper_names = [name for name, _ in batch]
        combined_text = "".join(entry for _, entry in batch)
        paper_count = len(batch)

        if total_batches > 1:
            print(f"-- Batch {batch_idx}/{total_batches} ({paper_count} papers) --")
            for name in paper_names:
                print(f"  + {name}")

        est_input, est_output, est_cost = estimate_cost(combined_text, agent_prompt)
        print(f"  Estimated: ~{est_input:,} input tokens, "
              f"up to {est_output:,} output tokens")
        print(f"  Estimated cost: ~${est_cost:.2f} USD")

        if total_batches == 1:
            user_content = (
                f"Here are {paper_count} individual paper summaries "
                f"from my literature review. Please synthesise them "
                f"according to your instructions.\n\n{combined_text}"
            )
        elif batch_idx < total_batches:
            user_content = (
                f"This is batch {batch_idx} of {total_batches}. "
                f"Here are {paper_count} paper summaries. "
                f"Please synthesise them according to your instructions. "
                f"I will send more batches after this.\n\n{combined_text}"
            )
        else:
            prev_results = "\n\n---\n\nPREVIOUS BATCH SYNTHESES:\n\n"
            prev_results += "\n\n---\n\n".join(batch_results)

            final_chars = len(combined_text) + len(prev_results)
            if final_chars > MAX_CHARS_PER_BATCH:
                user_content = (
                    f"Here are synthesis reports from {total_batches} batches "
                    f"covering {len(summaries)} papers total. Please produce "
                    f"a FINAL comprehensive synthesis that integrates "
                    f"everything.\n\n{prev_results}\n\n"
                    f"And here is the final batch of {paper_count} paper "
                    f"summaries:\n\n{combined_text}"
                )
                if len(user_content) > MAX_CHARS_PER_BATCH:
                    user_content = (
                        f"Here are synthesis reports from {total_batches} "
                        f"batches covering {len(summaries)} papers total. "
                        f"Please produce a FINAL comprehensive synthesis "
                        f"that integrates everything.\n\n{prev_results}"
                    )
            else:
                user_content = (
                    f"This is the final batch ({batch_idx} of {total_batches}). "
                    f"Here are {paper_count} paper summaries, plus the synthesis "
                    f"reports from previous batches. Please produce a FINAL "
                    f"comprehensive synthesis that integrates everything — "
                    f"all papers across all batches.\n\n"
                    f"{combined_text}\n\n{prev_results}"
                )

        print(f"\n  Sending to Claude ({SYNTHESIS_MODEL})...")
        result, in_tokens, out_tokens = call_claude_with_retry(
            client=client,
            model=SYNTHESIS_MODEL,
            max_tokens=SYNTHESIS_MAX_TOKENS,
            system=agent_prompt,
            messages=[{"role": "user", "content": user_content}],
        )

        actual_input_cost = (in_tokens / 1_000_000) * SYNTHESIS_INPUT_COST
        actual_output_cost = (out_tokens / 1_000_000) * SYNTHESIS_OUTPUT_COST
        actual_cost = actual_input_cost + actual_output_cost

        total_input_tokens += in_tokens
        total_output_tokens += out_tokens
        total_cost += actual_cost

        print(f"  Actual: {in_tokens:,} input + {out_tokens:,} output tokens")
        print(f"  Actual cost: ${actual_cost:.2f} USD")

        batch_results.append(result)

        if total_batches > 1:
            batch_file = SYNTHESIS_DIR / f"synthesis_batch{batch_idx}_{datetime.now().strftime('%Y-%m-%d_%H%M')}.md"
            batch_header = (
                f"# Synthesis — Batch {batch_idx}/{total_batches}\n\n"
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"**Papers in this batch:** {paper_count}\n"
                f"**Model:** {SYNTHESIS_MODEL}\n"
                f"**Cost:** ${actual_cost:.2f}\n\n---\n\n"
            )
            batch_file.write_text(batch_header + result, encoding="utf-8")
            print(f"  Saved: {batch_file.name}")

        print()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_file = SYNTHESIS_DIR / f"synthesis_{timestamp}.md"

    paper_list = "\n".join(f"  - {s.stem.replace('_note', '')}" for s in summaries)

    header = (
        f"# Literature Synthesis Report\n\n"
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"**Papers synthesised:** {len(summaries)}\n"
        f"**Mode:** full\n"
        f"**Model:** {SYNTHESIS_MODEL}\n"
        f"**Batches:** {total_batches}\n"
        f"**Total tokens:** {total_input_tokens:,} input + {total_output_tokens:,} output\n"
        f"**Total cost:** ${total_cost:.2f} USD\n\n"
        f"**Papers included:**\n{paper_list}\n\n---\n\n"
    )

    output_file.write_text(header + batch_results[-1], encoding="utf-8")
    save_manifest(summaries, output_file)

    print("=" * 60)
    print(f"Synthesis complete.")
    print(f"  Report:       {output_file}")
    print(f"  Papers:       {len(summaries)}")
    print(f"  Batches:      {total_batches}")
    print(f"  Total tokens: {total_input_tokens:,} in + {total_output_tokens:,} out")
    print(f"  Total cost:   ${total_cost:.2f} USD")


# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════

def run_synthesis(full_mode: bool = False):
    """Entry point — decides between incremental and full synthesis."""
    summaries = sorted(SUMMARIES_DIR.glob("*_note.md"))

    if not summaries:
        print("No summaries found. Run process_papers.py first.")
        print(f"Expected location: {SUMMARIES_DIR}")
        return

    print(f"Found {len(summaries)} summaries.\n")

    agent_file = AGENT_DIR / "synthesiser.md"
    if not agent_file.exists():
        print(f"ERROR: {agent_file} not found.")
        sys.exit(1)
    agent_prompt = agent_file.read_text(encoding="utf-8")

    if full_mode:
        run_full(summaries, agent_prompt)
    else:
        manifest = load_manifest()
        if not manifest.get("papers"):
            print("No previous synthesis found. Running full synthesis.\n")
            run_full(summaries, agent_prompt)
        else:
            run_incremental(summaries, agent_prompt)


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not found.")
        print(f"Check .env at: {PROJECT_ROOT / '.env'}")
        print("Copy .env.example to .env and add your key.")
        sys.exit(1)

    full_mode = "--full" in sys.argv

    print(f"Project: {PROJECT_ROOT}")
    print(f"Model:   {SYNTHESIS_MODEL}")
    print(f"Mode:    {'full' if full_mode else 'incremental'}")
    print()
    run_synthesis(full_mode=full_mode)
