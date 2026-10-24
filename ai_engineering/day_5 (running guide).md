# Day 05 — Document Parsing and Chunking

**AI Engineering Program | Day 05: Common Chunk Quality Test Cases**

## 1. Project Overview

This project extracts text from documents, divides it into retrieval-friendly chunks, retains source metadata, and saves the chunks to a JSON file for inspection.

Supported input formats:

- PDF (`.pdf`)
- Microsoft Word (`.docx`)
- Plain text (`.txt`)
- Markdown (`.md`, `.markdown`)

The script is named `parse-and-chunk.py`. It uses structure-aware chunking by default and provides a basic quality report when `--quality-report` is supplied.

## 2. Project Folder Structure

Keep the sample documents in a folder named `Day5_document_Chunking_Samples` beside your Python script. The examples below assume your project folder is the folder containing `parse-and-chunk.py`.

```text
5_document_chunking/
├── parse-and-chunk.py
├── Day5_document_Chunking_Samples/
│   ├── employee_policy_pdf_sample.pdf
│   ├── employee_policy_docx_sample.docx
│   ├── employee_policy_text_sample.txt
│   └── employee_policy_markdown_sample.md
└── outputs/
    ├── employee_policy_pdf_chunked.json
    ├── employee_policy_docx_chunked.json
    ├── employee_policy_txt_chunked.json
    └── employee_policy_md_chunked.json
```

If you renamed the project folder to `Day5_document_Chunking`, that is fine. The important part is that `parse-and-chunk.py` and `Day5_document_Chunking_Samples` are in the locations shown relative to each other.

The `outputs` folder and its JSON files are created automatically by the commands below. You do not need to create them manually.

## 3. Prerequisites

Check your Python installation:

```bash
python --version
```

Install the packages needed for PDF and DOCX support:

```bash
python -m pip install pypdf python-docx
```

- `pypdf` extracts text from PDFs.
- `python-docx` extracts paragraphs, headings, and tables from Word documents.
- TXT and Markdown inputs use Python's standard library and do not require extra packages.

## 4. Open the Project Folder in CMD

1. Open the project folder containing `parse-and-chunk.py` in File Explorer.
2. Click the address bar.
3. Type `cmd` and press Enter.
4. Verify that the script and sample folder are present:

```cmd
dir
```

You should see `parse-and-chunk.py` and `Day5_document_Chunking_Samples` in the listing.

**Important:** The commands in the next section assume CMD is opened in the project folder, not inside `Day5_document_Chunking_Samples`.

## 5. Run the Four Sample Documents

Run each command separately from the project folder. Each command reads one sample document and saves its JSON result to `outputs`.

### A. PDF

```cmd
python parse-and-chunk.py "Day5_document_Chunking_Samples\employee_policy_pdf_sample.pdf" --quality-report --output "outputs\employee_policy_pdf_chunked.json"
```

### B. DOCX

```cmd
python parse-and-chunk.py "Day5_document_Chunking_Samples\employee_policy_docx_sample.docx" --quality-report --output "outputs\employee_policy_docx_chunked.json"
```

### C. TXT

```cmd
python parse-and-chunk.py "Day5_document_Chunking_Samples\employee_policy_text_sample.txt" --quality-report --output "outputs\employee_policy_txt_chunked.json"
```

### D. Markdown (MD)

```cmd
python parse-and-chunk.py "Day5_document_Chunking_Samples\employee_policy_markdown_sample.md" --quality-report --output "outputs\employee_policy_md_chunked.json"
```

After running each command, the script should print a message showing the number of chunks saved and the output path. Confirm the JSON files exist in `outputs`.

**Filename reminder:** The TXT sample ends in `.txt`: `employee_policy_text_sample.txt`. The Markdown sample ends in `.md`: `employee_policy_markdown_sample.md`. These are different files.

## 6. Configure Chunk Size and Overlap

You can change chunk size and overlap in characters. For example:

```cmd
python parse-and-chunk.py "Day5_document_Chunking_Samples\employee_policy_pdf_sample.pdf" --chunk-size 1000 --overlap 150 --quality-report --output "outputs\employee_policy_pdf_chunked.json"
```

| Option | Meaning | Default |
|---|---|---:|
| `--chunk-size` | Target maximum chunk body size in characters | `1000` |
| `--overlap` | Target overlap between chunks, in characters | `150` |
| `--quality-report` | Include basic diagnostics in the JSON output | Off |
| `--output` | Specify the JSON output path | `<input-name>-chunked.json` beside the input document |

Chunk size and overlap are measured in characters, not model tokens. Actual structure and boundary behavior can affect chunk lengths, so inspect the generated output.

## 7. Output Location and Overwriting

The `--output` option accepts a JSON **file path**, including the filename—not just a folder. For example:

```cmd
python parse-and-chunk.py "Day5_document_Chunking_Samples\employee_policy_docx_sample.docx" --quality-report --output "outputs\employee_policy_docx_chunked.json"
```

The script creates the output directory if it does not exist. Running the same command again will overwrite the file at that same output path. Use different filenames when you want to compare multiple chunking configurations.

## 8. Understand the Generated JSON

With `--quality-report`, the JSON has two top-level keys:

- `chunks`: the generated chunks and their metadata.
- `quality_report`: basic measurements and diagnostics.

A chunk typically contains `text` and `metadata`. Metadata may include the source path, chunk index, heading path, content type, overlap information, and page number where available. The actual metadata depends on the source format and content.

Example of the general output shape:

```json
{
  "chunks": [
    {
      "text": "Section context and the content of the chunk...",
      "metadata": {
        "source": "employee_policy_pdf_sample.pdf",
        "heading_path": "Expenses > Reimbursement Rules",
        "chunk_index": 0,
        "content_type": "paragraph",
        "overlap_chars": 0,
        "page": 1
      }
    }
  ],
  "quality_report": {
    "chunk_count": 1,
    "note": "Manual verification is still required."
  }
}
```

This is an illustrative example, not the exact output from every file. Actual values, metadata fields, and chunk counts vary by document. Without `--quality-report`, the JSON contains the chunk list without the `quality_report` wrapper.

## 9. Day 05 — Common Chunk Quality Test Cases

Inspect the generated JSON and record evidence for all six tests.

### Test 1 — Boundary Preservation

**Objective:** Check whether a rule that spans multiple sentences remains understandable.

1. Find a policy or rule in the source document.
2. Locate the corresponding chunk or neighboring chunks in the JSON.
3. Check whether conditions, exceptions, and related sentences remain together.
4. Record any important context that was lost.

### Test 2 — Heading Relationship

**Objective:** Verify that a chunk retains its section context.

1. Find a meaningful heading in the source document.
2. Locate the corresponding chunk.
3. Check the `heading_path` metadata, if available.
4. Verify whether the chunk text includes enough heading context to make sense on its own.

### Test 3 — Small Detail

**Objective:** Verify that short but important details are preserved.

1. Find a short rule, exception, date, threshold, or numeric limit.
2. Search for it in the JSON output.
3. Check whether it remains understandable without unrelated text.
4. Record whether the detail was preserved, isolated, or missed.

### Test 4 — Overlap Duplication

**Objective:** Evaluate repeated content between neighboring chunks.

1. Select two consecutive chunks from the same source.
2. Compare the end of the first chunk with the beginning of the second.
3. Identify repeated text.
4. Decide whether the repetition preserves useful context or introduces unnecessary duplication.

### Test 5 — Metadata

**Objective:** Confirm that each chunk can be traced back to its source and location.

1. Select a chunk from the JSON.
2. Inspect `source`, `chunk_index`, and `heading_path`, when available.
3. Check page information when supported by the input format.
4. Verify that you can locate the corresponding content in the original document.

### Test 6 — Mixed Structure

**Objective:** Check whether lists and tables retain enough meaning.

1. Find a list or table in the original document.
2. Locate its representation in the JSON.
3. Verify that list items stay associated with their content.
4. Check that table headers remain associated with the correct values.
5. Record any structural information that was lost.

## 10. Record Your Results

Use this table to document your observations after inspecting the actual chunks.

| Test | Status | Evidence / Observation |
|---|---|---|
| Boundary preservation | Pass / Fail / Partial | |
| Heading relationship | Pass / Fail / Partial | |
| Small detail | Pass / Fail / Partial | |
| Overlap duplication | Pass / Fail / Partial | |
| Metadata | Pass / Fail / Partial | |
| Mixed structure | Pass / Fail / Partial | |

Do not mark a test as passed just because the script completed successfully. Base each result on the actual JSON output.

## 11. Troubleshooting

### Error: `FileNotFoundError: Document not found`

- Confirm that CMD is open in the project folder containing `parse-and-chunk.py`.
- Run `dir "Day5_document_Chunking_Samples"` to check the sample filenames.
- Check the extension carefully: `.txt` is not the same file as `.md`.
- If your sample folder is elsewhere, provide the correct relative or absolute input path.

### Error: `No module named 'pypdf'`

```cmd
python -m pip install pypdf
```

### Error: `No module named 'docx'`

```cmd
python -m pip install python-docx
```

### Output contains very little text

Check whether the document contains extractable text. Scanned PDFs may require OCR; normal text-based PDFs usually do not.

### Headings or table relationships are not fully preserved

Review the source formatting and JSON output. Structure-aware parsing uses heuristics and cannot guarantee preservation of every layout. Record these limitations as findings in your Day 05 tests.

### Quality report does not prove all tests passed

This is expected. The report measures basic properties such as chunk sizes and metadata coverage. Semantic boundary preservation, useful overlap, and table correctness still require manual inspection.

## 12. OCR Notes

OCR is not normally required for text-based PDFs, DOCX, TXT, or Markdown documents. If a PDF contains scanned page images and text extraction returns little or no text, OCR can be added as a separate ingestion step.

```text
Input document
      ↓
Text extraction
      ↓
OCR if needed
      ↓
Structure-aware chunking
      ↓
Metadata generation
      ↓
JSON output
      ↓
Manual Day 05 quality verification
```

## 13. Expected Outcome

By completing this exercise, you should be able to:

- Run the document parsing and chunking script.
- Generate a separate JSON output for each document format.
- Understand chunk size, overlap, headings, and source metadata.
- Inspect how paragraphs, lists, and tables are represented.
- Evaluate all six Day 05 chunk-quality test cases.
- Identify limitations that should be addressed before using chunks in a production RAG pipeline.

The goal is not merely to split documents into chunks. The goal is to preserve enough meaning and context for reliable retrieval and answer generation.
