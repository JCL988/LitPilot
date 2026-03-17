"""
Central configuration for the Literature Review Pipeline.

Edit this file to customise models, costs, and processing settings.
All paths are automatically resolved relative to this file's location,
so the pipeline works on any machine without path changes.
"""

from pathlib import Path

# ══════════════════════════════════════════════════════════════
#  PROJECT PATHS (auto-resolved — no need to edit)
# ══════════════════════════════════════════════════════════════

PROJECT_ROOT = Path(__file__).resolve().parent

INCOMING_DIR = PROJECT_ROOT / "incoming"
PROCESSED_DIR = PROJECT_ROOT / "processed"
SUMMARIES_DIR = PROJECT_ROOT / "summaries" / "individual"
SYNTHESIS_DIR = PROJECT_ROOT / "summaries" / "synthesis"
AGENT_DIR = PROJECT_ROOT / "bmad" / "agents"
LOG_FILE = PROJECT_ROOT / "processing_log.csv"
EXCEL_TRACKER = PROJECT_ROOT / "summaries" / "literature_tracker.xlsx"

# ══════════════════════════════════════════════════════════════
#  CLAUDE API SETTINGS
# ══════════════════════════════════════════════════════════════

# Model for individual paper analysis (Sonnet is fast and cheap)
ANALYSIS_MODEL = "claude-sonnet-4-20250514"
ANALYSIS_MAX_TOKENS = 8192

# Model for batch synthesis (Opus is more capable for cross-paper reasoning)
SYNTHESIS_MODEL = "claude-opus-4-6"
SYNTHESIS_MAX_TOKENS = 16384

# ══════════════════════════════════════════════════════════════
#  COST ESTIMATION (USD per million tokens — update if pricing changes)
# ══════════════════════════════════════════════════════════════

ANALYSIS_INPUT_COST = 3.00      # Sonnet input
ANALYSIS_OUTPUT_COST = 15.00    # Sonnet output
SYNTHESIS_INPUT_COST = 15.00    # Opus input
SYNTHESIS_OUTPUT_COST = 75.00   # Opus output

# ══════════════════════════════════════════════════════════════
#  PROCESSING SETTINGS
# ══════════════════════════════════════════════════════════════

MAX_PDF_PAGES = 95              # Skip pages beyond this limit
MAX_RETRIES = 3                 # Retry failed API calls
MAX_CONCURRENT = 1              # Parallel API calls (increase once stable)
CHARS_PER_TOKEN = 4             # Conservative estimate for English text
CONTEXT_LIMIT = 200000          # Token context window

# Maximum input tokens per synthesis batch (leave room for prompt + output)
MAX_SYNTHESIS_INPUT_TOKENS = 150000

# Supported file types for processing
SUPPORTED_EXTENSIONS = [".pdf", ".docx"]

# ══════════════════════════════════════════════════════════════
#  EXCEL TRACKER COLUMNS
# ══════════════════════════════════════════════════════════════
#  These must match the pipe-separated fields in your analyst
#  agent prompt (bmad/agents/analyst.md). If you add or remove
#  fields in the prompt, update this list to match.

TRACKER_HEADERS = [
    "Title",
    "Authors",
    "Year",
    "Journal",
    "Methodology",
    "Relevance",
    "Key Takeaway",
    "Primary Section",
    "All Relevant Sections",
    "Relevant Empirical Chapters",
    "Theoretical Frameworks",
    "Date Processed",
    "Source File",
]

# ══════════════════════════════════════════════════════════════
#  AUTO-CREATE FOLDERS
# ══════════════════════════════════════════════════════════════

for _folder in [INCOMING_DIR, PROCESSED_DIR, SUMMARIES_DIR, SYNTHESIS_DIR]:
    _folder.mkdir(parents=True, exist_ok=True)
