#!/usr/bin/env python3
"""
RMTK VN — Batch Translation via OpenAI Batch API
Step 1: Create batch JSONL and submit to OpenAI.
Step 2: Poll for completion.
Step 3: Download results and apply to markdown files.

Usage:
  # Create and submit batch:
  python translate_batch.py create

  # Check batch status:
  python translate_batch.py status

  # Download results and apply translations:
  python translate_batch.py apply
"""

import os
import sys
import json
import glob
import re
import time
from pathlib import Path

# ── Setup paths ──────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
BATCH_DIR = SCRIPT_DIR / "batch"

# Load .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4.1-mini"
BATCH_JSONL = BATCH_DIR / "batch_input.jsonl"
BATCH_ID_FILE = BATCH_DIR / "batch_id.txt"
BATCH_RESULTS_FILE = BATCH_DIR / "batch_results.jsonl"

SYSTEM_PROMPT = """You are a professional translator for a Japanese Kanji learning dictionary (Remembering the Kanji / RTK).
Translate the given English content to Vietnamese.

RULES:
1. Translate naturally and fluently into Vietnamese.
2. PRESERVE all HTML tags exactly as-is (<strong>, <em>, <a href="...">, etc.)
3. PRESERVE all Kanji characters, Japanese readings (on-yomi, kun-yomi), and Unicode escapes (&#039; &quot; etc.)
4. PRESERVE usernames in square brackets like [<a href="...">username</a>]
5. PRESERVE dates and vote counts in parentheses like 29-6-2006(263)
6. PRESERVE numbering format like "1) ", "2) " at the start of stories
7. PRESERVE all URLs and href attributes unchanged
8. The "keyword" should be translated to a concise Vietnamese equivalent
9. The "elements" should be translated — these are primitive component names used in the Heisig method
10. For stories: translate the narrative but keep the mnemonic associations clear

OUTPUT FORMAT — Return valid JSON:
{
  "keyword_vi": "Vietnamese translation of keyword",
  "elements_vi": "Vietnamese translation of elements",
  "stories_vi": "Full Vietnamese translation of all stories, with HTML preserved"
}"""


def parse_markdown(filepath):
    """Parse a kanji markdown file into frontmatter dict and body string."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split frontmatter and body
    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, None

    frontmatter_str = parts[1].strip()
    body = parts[2].strip()

    # Parse frontmatter (simple key: value)
    frontmatter = {}
    current_key = None
    for line in frontmatter_str.split('\n'):
        if line.startswith(' ') and current_key:
            # continuation (like redirect_from list items)
            if current_key not in frontmatter:
                frontmatter[current_key] = []
            if isinstance(frontmatter[current_key], list):
                frontmatter[current_key].append(line.strip().lstrip('- '))
            continue
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip()
            # Remove surrounding quotes
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            frontmatter[key] = val
            current_key = key

    return frontmatter, body


def create_batch():
    """Create JSONL batch file and submit to OpenAI Batch API."""
    BATCH_DIR.mkdir(exist_ok=True)

    # Collect all kanji markdown files
    md_files = sorted(
        glob.glob(str(PROJECT_ROOT / "rtk1-v6" / "*.md")) +
        glob.glob(str(PROJECT_ROOT / "rtk3-remain" / "*.md"))
    )

    print(f"📂 Found {len(md_files)} markdown files")

    # Build JSONL
    requests = []
    skipped = 0

    for filepath in md_files:
        fm, body = parse_markdown(filepath)
        if fm is None:
            skipped += 1
            continue

        keyword = fm.get('keyword', '')
        elements = fm.get('elements', '')
        kanji = fm.get('kanji', '')
        v4 = fm.get('v4', '')

        # Skip if no translatable content
        if not keyword and not body:
            skipped += 1
            continue

        # Build the user prompt
        user_content = f"""Kanji: {kanji} (Frame #{v4})
Keyword: {keyword}
Elements: {elements}

Stories:
{body}"""

        # Use relative path as custom_id for matching later
        rel_path = os.path.relpath(filepath, PROJECT_ROOT)
        custom_id = rel_path.replace('/', '__')  # e.g., rtk1-v6__0001.md

        request = {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "max_tokens": 2048
            }
        }
        requests.append(request)

    print(f"✅ Built {len(requests)} translation requests (skipped {skipped})")

    # Write JSONL
    with open(BATCH_JSONL, 'w', encoding='utf-8') as f:
        for req in requests:
            f.write(json.dumps(req, ensure_ascii=False) + '\n')

    jsonl_size_mb = os.path.getsize(BATCH_JSONL) / (1024 * 1024)
    print(f"📄 Batch JSONL: {BATCH_JSONL} ({jsonl_size_mb:.1f} MB)")

    # Upload file to OpenAI
    print("⬆️  Uploading batch file to OpenAI...")
    with open(BATCH_JSONL, 'rb') as f:
        batch_file = client.files.create(file=f, purpose="batch")

    print(f"📎 File uploaded: {batch_file.id}")

    # Create batch
    print("🚀 Submitting batch...")
    batch = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "RMTK VN kanji translation EN→VI"}
    )

    # Save batch ID
    with open(BATCH_ID_FILE, 'w') as f:
        f.write(batch.id)

    print(f"✅ Batch submitted: {batch.id}")
    print(f"   Status: {batch.status}")
    print(f"   Batch ID saved to: {BATCH_ID_FILE}")
    print(f"\n💡 Run 'python translate_batch.py status' to check progress")


def check_status():
    """Check the status of the submitted batch."""
    if not BATCH_ID_FILE.exists():
        print("❌ No batch ID found. Run 'create' first.")
        return None

    batch_id = BATCH_ID_FILE.read_text().strip()
    batch = client.batches.retrieve(batch_id)

    total = batch.request_counts.total if batch.request_counts else '?'
    completed = batch.request_counts.completed if batch.request_counts else '?'
    failed = batch.request_counts.failed if batch.request_counts else '?'

    print(f"📊 Batch: {batch_id}")
    print(f"   Status: {batch.status}")
    print(f"   Progress: {completed}/{total} completed, {failed} failed")

    if batch.status == 'completed':
        print(f"   Output file: {batch.output_file_id}")
        print(f"\n💡 Run 'python translate_batch.py apply' to download and apply translations")
    elif batch.status == 'failed':
        print(f"   ❌ Batch failed!")
        if batch.errors:
            for err in batch.errors.data:
                print(f"      Error: {err.message}")
    elif batch.status in ('validating', 'in_progress', 'finalizing'):
        print(f"\n⏳ Still processing. Check again later.")

    return batch


def apply_translations():
    """Download batch results and apply translations to markdown files."""
    if not BATCH_ID_FILE.exists():
        print("❌ No batch ID found. Run 'create' first.")
        return

    batch_id = BATCH_ID_FILE.read_text().strip()
    batch = client.batches.retrieve(batch_id)

    if batch.status != 'completed':
        print(f"⏳ Batch not yet complete. Status: {batch.status}")
        return

    # Download results
    print("⬇️  Downloading results...")
    output_file_id = batch.output_file_id
    result_content = client.files.content(output_file_id)

    with open(BATCH_RESULTS_FILE, 'wb') as f:
        f.write(result_content.content)

    print(f"📄 Results saved to: {BATCH_RESULTS_FILE}")

    # Parse results
    results = {}
    with open(BATCH_RESULTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            custom_id = data['custom_id']
            response = data.get('response', {})
            if response.get('status_code') == 200:
                body = response['body']
                choices = body.get('choices', [])
                if choices:
                    content = choices[0]['message']['content']
                    try:
                        translation = json.loads(content)
                        results[custom_id] = translation
                    except json.JSONDecodeError:
                        print(f"  ⚠️  JSON parse error for {custom_id}")
            else:
                print(f"  ⚠️  API error for {custom_id}: {response.get('status_code')}")

    print(f"📊 Parsed {len(results)} translations")

    # Apply translations
    applied = 0
    errors = 0

    for custom_id, translation in results.items():
        # Convert custom_id back to filepath
        rel_path = custom_id.replace('__', '/')
        filepath = PROJECT_ROOT / rel_path

        if not filepath.exists():
            print(f"  ⚠️  File not found: {filepath}")
            errors += 1
            continue

        try:
            apply_to_file(filepath, translation)
            applied += 1
        except Exception as e:
            print(f"  ⚠️  Error applying to {rel_path}: {e}")
            errors += 1

    print(f"\n✅ Applied {applied} translations ({errors} errors)")


def apply_to_file(filepath, translation):
    """Apply a translation dict to a single markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---', 2)
    if len(parts) < 3:
        return

    frontmatter_str = parts[1]
    body = parts[2]

    # Add keyword_vi and elements_vi to frontmatter
    keyword_vi = translation.get('keyword_vi', '')
    elements_vi = translation.get('elements_vi', '')
    stories_vi = translation.get('stories_vi', '')

    # Remove existing Vietnamese fields if present
    fm_lines = frontmatter_str.strip().split('\n')
    fm_lines = [l for l in fm_lines if not l.startswith('keyword_vi:') and not l.startswith('elements_vi:')]

    # Add new Vietnamese fields
    if keyword_vi:
        fm_lines.append(f'keyword_vi: "{keyword_vi}"')
    if elements_vi:
        fm_lines.append(f'elements_vi: "{elements_vi}"')

    new_frontmatter = '\n'.join(fm_lines)

    # Replace body with Vietnamese stories (keep original as comment)
    if stories_vi:
        new_body = f"\n{stories_vi}\n"
    else:
        new_body = body

    new_content = f"---\n{new_frontmatter}\n---\n{new_body}\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)


# ── CLI ──────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python translate_batch.py <create|status|apply>")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'create':
        create_batch()
    elif command == 'status':
        check_status()
    elif command == 'apply':
        apply_translations()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python translate_batch.py <create|status|apply>")
        sys.exit(1)
