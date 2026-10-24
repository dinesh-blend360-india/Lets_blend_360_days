# Day 05 Test Guide

## Goal

Run the document parser on PDF, DOCX, TXT, and Markdown inputs; export parsed source text; compare two splitting approaches; and inspect all six chunk-quality dimensions.

## Requirements

From the project folder, install the optional document readers:

```bash
python -m pip install pypdf python-docx
```

TXT and Markdown parsing use the Python standard library. The supplied PDF contains extractable text; OCR is not required for this sample.

## 1. Regenerate parsed source output

```bash
python export-parsed-source.py
```

Outputs are written to `test_outputs/parsed_source/`. Each JSON contains the source text units and available source metadata. This is extracted/normalized parser output, not a guarantee of perfect OCR or layout recovery.

## 2. Compare two chunking approaches

Use the same Markdown input and keep the same chunk-size and overlap settings to make the comparison fair.

**Structure-aware splitting**

```bash
python parse-and-chunk.py "test_inputs\employee_policy_markdown_sample.md" --method structure --chunk-size 250 --overlap 50 --quality-report --output "test_outputs\chunks\markdown_structure_250_50.json"
```

**Character-based splitting for oversized prose**

```bash
python parse-and-chunk.py "test_inputs\employee_policy_markdown_sample.md" --method character --chunk-size 250 --overlap 50 --quality-report --output "test_outputs\chunks\markdown_character_250_50.json"
```

In this implementation, both methods use the shared parser to recognize headings, lists, and tables. The selected method changes how oversized prose blocks are split. This distinction should be kept in mind when interpreting results.

## 3. Run all four input formats

```bash
python parse-and-chunk.py "test_inputs\employee_policy_pdf_sample.pdf" --method structure --chunk-size 250 --overlap 50 --quality-report --output "test_outputs\chunks\pdf_structure_250_50.json"
python parse-and-chunk.py "test_inputs\employee_policy_docx_sample.docx" --method structure --chunk-size 250 --overlap 50 --quality-report --output "test_outputs\chunks\docx_structure_250_50.json"
python parse-and-chunk.py "test_inputs\employee_policy_text_sample.txt" --method structure --chunk-size 250 --overlap 50 --quality-report --output "test_outputs\chunks\txt_structure_250_50.json"
python parse-and-chunk.py "test_inputs\employee_policy_markdown_sample.md" --method structure --chunk-size 250 --overlap 50 --quality-report --output "test_outputs\chunks\markdown_structure_250_50.json"
```

## 4. Inspect the six test cases

1. **Boundary preservation:** search for the deadline, receipt rule, and missing-receipt explanation. Does each chunk keep a complete sentence or condition?
2. **Heading relationship:** inspect `heading_path` and the `Section:` prefix. Compare Markdown/DOCX headings with PDF output.
3. **Small detail:** search for the exception for claims below 500 currency units and for the seven-year retention period.
4. **Overlap duplication:** compare the end of one chunk with the start of the next. Check whether the repeat contributes context.
5. **Metadata:** inspect `source`, `chunk_index`, `global_chunk_index`, `heading_path`, `content_type`, `overlap_chars`, and `page`/`page_start`/`page_end` where present.
6. **Mixed structure:** inspect table chunks. Verify that every split table chunk repeats the header and keeps values next to the right row labels.

## 5. Evidence and reporting

- Parsed source evidence: `test_outputs/parsed_source/`
- Chunk outputs and measurable quality reports: `test_outputs/chunks/`
- Written analysis: `Day05_Assignment_Response.md`

The quality report measures sizes, basic metadata coverage, content types, and recorded overlap. It cannot automatically verify semantic correctness, heading relevance, or all table relationships; those require manual inspection.
