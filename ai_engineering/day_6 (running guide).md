# Day 06 — Local Vector Embedding and Retrieval

**AI Engineering Program | Day 06: Embeddings, similarity search, and retrieval evaluation**

## 1. Project overview

Day 06 takes the JSON chunks created by Day 05 and turns them into local vector
embeddings using `BAAI/bge-small-en-v1.5`. It then stores the vectors locally,
embeds a search query, ranks chunks with cosine similarity, and evaluates the
results with Recall@K and MRR.

This day intentionally stops before RAG. It does not generate answers with an
LLM, call an external embedding API, or use a production vector database.

Detailed documentation:

- [`6_embedding_and_retrival/README.md`](6_embedding_and_retrival/README.md)
- [`6_embedding_and_retrival/SETUP.md`](6_embedding_and_retrival/SETUP.md)

## 2. Project location and structure

The folder name is intentionally `retrival`, matching the existing project
requirement:

```text
ai_engineering/
├── 5_document_chunking/
├── 6_embedding_and_retrival/
│   ├── src/
│   │   ├── embeddings/
│   │   ├── retrieval/
│   │   └── evaluation/
│   ├── tests/
│   ├── test_inputs/retrieval_queries.json
│   └── outputs/
│       ├── embeddings/
│       ├── retrieval_results/
│       └── reports/
└── requirements.txt
```

Day 06 reads the existing files in:

```text
ai_engineering/5_document_chunking/outputs/
```

It does not copy or modify the Day 05 documents or chunked JSON files.

## 3. Prerequisites

Use the shared Python environment from the repository root when it is working.
The shared dependency file contains the Day 06 packages:

- `numpy`
- `sentence-transformers`
- `pytest` for tests

The first real embedding run downloads the BGE model and therefore needs
internet access. Later inference uses the locally cached model and does not
require an external embedding API.

Check Python from the repository root:

```powershell
cd C:\workspace\IDC-on-boarding-training\Lets_blend_360_days
python --version
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r .\ai_engineering\requirements.txt
```

If the existing `venv` points to a deleted Python installation, repair it with
a working Python interpreter before installing dependencies:

```powershell
python -m venv --upgrade venv
.\venv\Scripts\python.exe -m pip install -r .\ai_engineering\requirements.txt
```

## 4. Run the Day 06 tests

Move into the Day 06 folder and run the tests with the shared interpreter:

```powershell
cd .\ai_engineering\6_embedding_and_retrival
..\..\venv\Scripts\python.exe -m pytest .\tests -q
```

These tests use fake vectors and a fake embedding model. They do not download
the BGE model.

## 5. Build an embedding index

Start with the real Day 05 Markdown output:

```powershell
$python = "..\..\venv\Scripts\python.exe"
$day05 = "..\5_document_chunking\outputs\employee_policy_md_chunked.json"
$index = ".\outputs\embeddings\employee_policy_md_structure"

& $python -m src.embeddings.build_embeddings $day05 --index-dir $index
```

The command validates the chunks, generates normalized vectors in batches, and
creates:

```text
outputs/embeddings/employee_policy_md_structure/
├── vectors.npz
├── metadata.json
└── manifest.json
```

The manifest records the model ID, vector dimension, tokenizer limit, input
hash, query-instruction setting, cache counts, and skipped chunks.

Build indexes for all four existing Day 05 outputs:

```powershell
$python = "..\..\venv\Scripts\python.exe"
$day05Files = @(
  "employee_policy_docx_chunked.json",
  "employee_policy_md_chunked.json",
  "employee_policy_pdf_chunked.json",
  "employee_policy_txt_chunked.json"
)

foreach ($file in $day05Files) {
  $name = [IO.Path]::GetFileNameWithoutExtension($file)
  & $python -m src.embeddings.build_embeddings `
    "..\5_document_chunking\outputs\$file" `
    --index-dir ".\outputs\embeddings\$name"
}
```

Keep each chunking experiment in its own index directory. Do not mix vectors
from structure-aware and character-based chunking.

## 6. Run similarity retrieval

```powershell
$python = "..\..\venv\Scripts\python.exe"
$index = ".\outputs\embeddings\employee_policy_md_structure"

& $python -m src.retrieval.search `
  --index-dir $index `
  --query "When is a receipt required?" `
  --top-k 5
```

The result includes rank, similarity score, `chunk_id`, original text, source,
page information, heading path, content type, and chunk index.

Similarity is not a probability. A higher score means the query and chunk
vectors are more directionally similar; it does not prove that the result is
correct.

## 7. Save results under retrieval_results

Use `--export` to save ranked search results as JSON:

```powershell
& $python -m src.retrieval.search `
  --index-dir $index `
  --query "When is a receipt required?" `
  --top-k 5 `
  --export ".\outputs\retrieval_results\receipt_search.json"
```

`outputs/retrieval_results/` is an output folder, not a Python package and not
an entry in `requirements.txt`. The search command creates it when necessary.

For repeated searches, omit `--query`:

```powershell
& $python -m src.retrieval.search --index-dir $index --top-k 5
```

Press Enter on an empty query to exit interactive mode.

## 8. Evaluate retrieval quality

The editable query file is:

```text
6_embedding_and_retrival/test_inputs/retrieval_queries.json
```

Run evaluation:

```powershell
& $python -m src.evaluation.evaluate_retrieval `
  --queries .\test_inputs\retrieval_queries.json `
  --index-dir $index `
  --output .\outputs\reports\employee_policy_md_structure.json
```

The report contains:

- Recall@1
- Recall@3
- Recall@5
- MRR
- Queries with no relevant source passage
- Queries where no relevant chunk was retrieved
- Ranked result details for each evaluated query

The sample queries use phrases taken from the Day 05 policy text. Add explicit
`expected_chunk_ids` when creating a manually labeled evaluation set.

## 9. Compare structure-aware and character-based indexes

If the Day 05 character baseline does not exist, generate it first:

```powershell
$python = "..\..\venv\Scripts\python.exe"
& $python ..\5_document_chunking\parse-and-chunk.py `
  ..\5_document_chunking\Day5_document_Chunking_Samples\employee_policy_markdown_sample.md `
  --method character `
  --output ..\5_document_chunking\outputs\employee_policy_md_character_chunked.json
```

Build the separate character index:

```powershell
& $python -m src.embeddings.build_embeddings `
  ..\5_document_chunking\outputs\employee_policy_md_character_chunked.json `
  --index-dir .\outputs\embeddings\employee_policy_md_character
```

Evaluate it with the same query set:

```powershell
& $python -m src.evaluation.evaluate_retrieval `
  --queries .\test_inputs\retrieval_queries.json `
  --index-dir .\outputs\embeddings\employee_policy_md_character `
  --output .\outputs\reports\employee_policy_md_character.json
```

Compare the two report JSON files. Do not claim one method is better until the
commands have actually been run and the retrieved examples inspected.

## 10. Query instruction setting

The BGE query instruction is enabled by default for short queries. It is added
to query text only, never document text. Keep the setting unchanged within one
experiment.

To build and search without it, use the flag consistently:

```powershell
& $python -m src.embeddings.build_embeddings $day05 `
  --index-dir .\outputs\embeddings\employee_policy_md_no_instruction `
  --no-query-instruction

& $python -m src.retrieval.search `
  --index-dir .\outputs\embeddings\employee_policy_md_no_instruction `
  --query "When is a receipt required?" `
  --no-query-instruction
```

## 11. Troubleshooting

- If `python` is not recognized, install Python or use the repository's working
  `.\venv\Scripts\python.exe` path.
- If the virtual environment points to a missing interpreter, repair it with
  `python -m venv --upgrade venv`.
- If the model cannot download, check internet access, disk space, and the
  Hugging Face connection. Model inference itself is local after download.
- If chunks are skipped, inspect `manifest.json` for tokenizer-limit reasons.
- If search rejects the index, use the same model, vector dimension,
  normalization, and query-instruction setting used to build it.
- If the character baseline is missing, generate it from Day 05 first. Do not
  call a structure-aware output a character baseline.

## 12. Scope boundary

Day 06 ends at ranked retrieval and evaluation. A future day may add hybrid
BM25+dense retrieval, reranking, access-control filtering, update/deletion
strategies, and RAG answer generation with citations.
