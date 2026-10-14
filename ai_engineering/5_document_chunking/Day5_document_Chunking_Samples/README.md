# Day 05 Sample Documents

These four files contain the same synthetic employee expense policy, represented as PDF, DOCX, TXT, and Markdown. The PDF is text-based (not a scan), so OCR should not be necessary. The DOCX has styled headings and a real Word table; the Markdown file has headings, a list, and a Markdown table; the TXT file contains plain-text headings and an ASCII-style table.

## Run from `Day5_document_Chunking`

Copy the four sample documents into your `Day5_document_Chunking` folder alongside `parse-and-chunk.py`, then run one command at a time:

```bash
python parse-and-chunk.py "Day5_document_Chunking_Samples\employee_policy_pdf_sample.pdf" --quality-report --output "outputs\employee_policy_pdf_chunked.json"

python parse-and-chunk.py "Day5_document_Chunking_Samples\employee_policy_docx_sample.docx" --quality-report --output "outputs\employee_policy_docx_chunked.json"

python parse-and-chunk.py "Day5_document_Chunking_Samples\employee_policy_text_sample.txt" --quality-report --output "outputs\employee_policy_txt_chunked.json"

python parse-and-chunk.py "Day5_document_Chunking_Samples\employee_policy_markdown_sample.md" --quality-report --output "outputs\employee_policy_md_chunked.json"
```

Each input has a distinct base filename, so the generated `*-chunked.json` files will not overwrite one another.

## Day 05 test focus

1. Boundary preservation: the 30-day deadline, receipt requirements, late-claim conditions, and manager/Finance responsibilities.
2. Heading relationship: `Expense Reimbursement Rules > Late claims and exceptions`, and other nested sections.
3. Small detail: the receipt exception for expenses under 500 currency units.
4. Overlap duplication: compare the end of one chunk with the beginning of the next.
5. Metadata: inspect source, section/heading, page where available, and chunk indexes.
6. Mixed structure: inspect numbered travel steps, checklist bullets, and the spending-limits table.

These are test fixtures, not a pre-filled pass result. Inspect each generated JSON and record what actually happens.
