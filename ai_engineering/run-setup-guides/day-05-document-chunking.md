# Day 05 — Parsing and chunking documents

| | |
|---|---|
| **Folder** | `05_document_chunking/` — `parse-and-chunk.py`, `samples/`, `outputs/` |
| **Command** | `& $py .\parse-and-chunk.py .\samples\employee_policy_markdown_sample.md --method structure` |
| **Needs** | Nothing but the shared environment. **No model, no network.** |
| **Time** | 1–1.5 hours |
| **Depends on** | Nothing. **Day 06 depends on this day's output.** |

Longer, screenshot-style walkthrough: `day_5 (running guide).md` in this folder.

---

## 1. What you are learning

A model cannot read a 50-page handbook at once, and a search system cannot
return "the handbook". Both need the document cut into **chunks**: pieces small
enough to search and to fit in a prompt, whole enough to make sense alone.

This is the least glamorous step in RAG and the one that most often decides
whether it works. You learn:

- **Parsing.** Getting text out of PDF (`pypdf`), Word (`python-docx`), plain text
  and Markdown, and keeping the useful structure — headings, lists, tables,
  PDF page numbers.
- **Chunking strategies.** `structure` (respects headings, paragraphs, lists and
  tables) versus raw baselines: `character`, `paragraph`, `sentence`, `word`,
  `recursive`.
- **Chunk size and overlap.** Size is a trade-off: small chunks are precise but
  lose context; big chunks carry context but dilute the match. Overlap repeats a
  little text across the cut so a fact split in half is not lost.
- **Metadata.** Every chunk carries `chunk_id`, `source`, position, content type,
  `heading_path` and (for PDFs) page. That metadata is what later lets an answer
  *cite* where it came from.
- **Validation.** The script checks every chunk is non-empty, has a unique ID and
  respects the size limit.
- **Baselines.** The `character` method is deliberately dumb. You run it so you
  have something to compare the clever method against.

## 2. Setup

Nothing extra. The readers `pypdf` and `python-docx` are already in
`requirements.txt`. Check:

```powershell
& $py -c "import pypdf, docx; print('readers OK')"
```

## 3. Run

Always `Set-Location` into the folder first so the relative paths below work.

```powershell
Set-Location "$ai\05_document_chunking"

# One document, structure-aware, with diagnostics
& $py .\parse-and-chunk.py .\samples\employee_policy_markdown_sample.md `
      --method structure --chunk-size 1000 --overlap 150 --quality-report `
      --output .\outputs\employee_policy_md_structure_demo.json

# The raw baseline, for comparison
& $py .\parse-and-chunk.py .\samples\employee_policy_markdown_sample.md `
      --method character --chunk-size 1000 --overlap 150 `
      --output .\outputs\employee_policy_md_character_demo.json
```

Options: `--method` (`structure` default, `character`, `paragraph`, `sentence`,
`word`, `recursive`), `--chunk-size` (default 1000 characters), `--overlap`
(default 150), `--quality-report`, `--output`.

The four samples (same policy, four formats):

| File | Format |
|---|---|
| `employee_policy_markdown_sample.md` | Markdown |
| `employee_policy_text_sample.txt` | Plain text |
| `employee_policy_docx_sample.docx` | Word |
| `employee_policy_pdf_sample.pdf` | PDF |

**Where the output goes.** If you **omit `--output`**, the file is written *next
to the source document* (in `samples\`), named
`<name>-<method>-chunked.json` — not into `outputs\`. Use `--output` to control
it. Delete stray files from `samples\` if you create them.

**Day 06 needs four specific files** in `outputs\` (already committed):
`employee_policy_md_chunked.json`, `…_txt_…`, `…_docx_…`, `…_pdf_…`. Do not
overwrite them casually; if you regenerate them, Day 06's index must be rebuilt.

## 4. What to test

- [ ] **All four formats** with `--method structure`. Open each JSON. Can you find
  the headings, a table, and (PDF) the page numbers?
- [ ] **`structure` vs `character`** on the Markdown file. Compare chunk counts and
  read the first characters of each chunk. Where does each one *begin*?
- [ ] **Compare the same policy across formats.** Why are the counts different?
- [ ] **Chunk size.** Try `--chunk-size 300`, `600`, `1500`. What happens to the
  count and to the longest chunk? Does the validation line ever fail?
- [ ] **Overlap.** Set `--overlap 0`, then `300`. Look at the *end* of one chunk
  and the *start* of the next.
- [ ] **A long table row.** The README suggests testing that every chunk stays
  within `--chunk-size` even when a single table row is huge.
- [ ] **Your own document.** Chunk a policy PDF or Word file you have (fake or
  public data only). Does it behave?
- [ ] **A bad overlap** (`--overlap` larger than `--chunk-size`) — what error do you get?
- [ ] Run **`samples\what is rag.txt`** — a longer explanatory text about RAG,
  useful as extra reading and as a bigger test input.

## 5. What to expect

Console output ends with two lines:

```text
Validation: 11 unique chunk IDs; max size 761 characters
Quality report: 11 chunks; max chunk size 761 characters
```

Observed with `--method structure --chunk-size 1000 --overlap 150`:

| Format | Chunks | Largest chunk (chars) |
|---|---|---|
| Markdown | **11** | 761 |
| Plain text | **29** | 908 |
| Word (docx) | **10** | 724 |
| PDF | **16** | 904 |

(These match the counts in the committed `outputs\` files.)

The same Markdown file with `--method character` gives **5** chunks of up to 998
characters, with **no `heading_path`**, and chunk 2 begins mid-sentence:
`'total cost, and the manager who approved it. If plans change, the empl…'`.
Compare with the structure-aware chunk 2, which starts with its section title
and carries
`heading_path: "Employee Expense and Travel Policy > 2. Expense Reimbursement Rules > 2.1 Submission deadline and required context"`.

Each chunk looks like:

```json
{ "text": "Section: 2.1 Submission deadline and required context\n\nEmployees must …",
  "metadata": { "chunk_id": "chunk_5762afc8dde2640e56dd", "source": "…", "chunk_index": 2,
                "global_chunk_index": 2, "content_type": "paragraph",
                "heading_path": "…> 2.1 Submission deadline…", "overlap_chars": 0 } }
```

**Effect of chunk size** (Markdown, structure method, overlap 150 unless noted):

| `--chunk-size` | Chunks | Largest |
|---|---|---|
| 300 (overlap 50) | 25 | 298 |
| 1000 | 11 | 761 |
| 1500 | 11 | 761 |

Going from 1000 to 1500 changes nothing: the document's sections are already
shorter than 1000 characters, so the limit never bites. Size only matters when
it is *smaller* than your natural units.

**Why the plain-text version has 29 chunks.** In `.txt`, a heading such as
`1. PURPOSE` is just a short line — there is no markup saying "this is a
heading". So each heading becomes its **own tiny chunk** (that one is 10
characters) and the median chunk is only ~80 characters. A search engine would
treat "1. PURPOSE" as a document. The Markdown version recognises `#` headings
and folds them into their sections. **Format changes chunk quality**, and
structure-aware chunking can only use structure that exists.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| `can't open file '…parse-and-chunk.py'` | Wrong folder | `Set-Location "$ai\05_document_chunking"` |
| `FileNotFoundError … Day5_document_Chunking_Samples` | Following an old command | The folder is **`samples\`** now (the README and guides were corrected) |
| `ModuleNotFoundError: pypdf` / `docx` | Wrong Python | `& $py -m pip install -r "$ai\requirements.txt"` |
| A new `*-chunked.json` appears in `samples\` | You omitted `--output` | Move/delete it, or pass `--output` |
| An empty or tiny PDF result | The PDF is scanned images | The script has no OCR — see section 8 |
| `ValueError: overlap must be at least zero and smaller than chunk_size` | `--overlap` ≥ `--chunk-size` (equal also fails) | Reduce `--overlap` |
| `FileNotFoundError: Document not found: samples\nope.md` | Typo in the path | Check the file name |

## 7. Learn more

- **RAG chunking guidance:** search "chunking strategies for RAG" — fixed-size,
  recursive, semantic, document-structure, and "parent-document" retrieval.
- **Token-based vs character-based sizing.** Models count *tokens*, not
  characters (see section 8).
- **PDF extraction is hard:** layout, columns, tables, headers/footers.
  Libraries to read about: `pdfplumber`, `PyMuPDF`, `unstructured`.
- **OCR** for scanned documents (Tesseract; cloud document-AI services).
- **Markdown as a target format:** many pipelines convert everything to Markdown
  first precisely because it preserves headings and tables.
- **Late chunking / contextual retrieval:** methods that add document-level
  context to each chunk.
- Read `samples\what is rag.txt` and `samples\README.md`.

## 8. What you might be missing

- **Sizes are in characters, not tokens.** The embedding model in Day 06 has a
  limit of 512 *tokens* and will truncate (or Day 06 will skip) anything longer.
  A 1,000-character chunk is usually well under that for English, but tables and
  code are token-hungry. The README itself says to measure with the model's
  tokenizer before embedding.
- **The committed `outputs\*.json` are an older format.** They contain only
  `chunks` and `quality_report`. Files you generate now also contain `experiment`
  and `validation` blocks (the README describes the new shape). Day 06 reads the
  `chunks` list either way. Don't be surprised that your fresh output has more
  keys than the committed one.
- **The source path inside the chunks is baked in.** The committed outputs record
  `source: "Day5_document_Chunking_Samples\employee_policy_markdown_sample.md"` —
  the folder's earlier name. That string flows into the Day 06 index and then
  appears in **Day 07 and Day 08 citations**. It is harmless (just metadata) but
  looks stale; regenerating Day 05 → rebuilding Day 06 would update it.
- **No OCR.** A scanned PDF yields little or no text.
- **No language handling.** Sentence splitting assumes English-style punctuation.
- **Chunking is a hyperparameter you tune, not a fact.** `1000/150` is a starting
  point. Day 06's retrieval scores and Day 08's evaluation are how you would
  *measure* a better choice; today you only inspect by eye.
- **Overlap duplicates text**, which raises storage and can return near-duplicate
  results.
- **Format fidelity differs**: DOCX tables become Markdown-like text; PDF page
  numbers survive; text and Markdown have no pages.
- **Heading detection in `.txt` is absent** (see section 5). If your own corpus
  is plain text, consider converting it to Markdown first.
- **This day does not need AI — and the quality of everything after depends on
  it.** If Day 07 answers badly, check the chunks before blaming the model.

## 9. Where this leads

Day 06 turns these chunks into vectors and searches them. The `chunk_id`
and `heading_path` you saw here are exactly what Day 07's citations point at.
