# Day 06 setup on Windows

Open PowerShell in:

```text
C:\workspace\IDC-on-boarding-training\Lets_blend_360_days\ai_engineering\06_embedding_and_retrieval
```

Check Python and create an isolated environment:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt
```

Python 3.10+ is recommended for current Sentence Transformers releases. If
PowerShell blocks activation, run the environment interpreter directly as
`.\.venv\Scripts\python.exe` or adjust execution policy only according to your
local policy.

The shared requirements file is the canonical dependency list for the whole
`ai_engineering` workspace. The local `requirements.txt` contains the minimal
Day 06 dependency subset and can be used instead when this project is isolated:

```powershell
python -m pip install -r .\requirements.txt
```

## Build an index

Day 05 output paths are relative to this folder:

```powershell
$day05 = "..\05_document_chunking\outputs\employee_policy_md_chunked.json"
$index = ".\outputs\embeddings\employee_policy_md_structure"
python -m src.embeddings.build_embeddings $day05 --index-dir $index
```

The first execution downloads `BAAI/bge-small-en-v1.5` from Hugging Face and
may require internet access. The model is then used locally on CPU. The command
creates `vectors.npz`, `metadata.json`, and `manifest.json`. The manifest tells
you the actual dimension, tokenizer limit, indexed/skipped counts, and cache
reuse.

To build indexes for all four existing Day 05 outputs:

```powershell
$day05Files = @(
  "employee_policy_docx_chunked.json",
  "employee_policy_md_chunked.json",
  "employee_policy_pdf_chunked.json",
  "employee_policy_txt_chunked.json"
)
foreach ($file in $day05Files) {
  $name = [IO.Path]::GetFileNameWithoutExtension($file)
  python -m src.embeddings.build_embeddings `
    "..\05_document_chunking\outputs\$file" `
    --index-dir ".\outputs\embeddings\$name"
}
```

To compare Day 05 methods, use separate source and index names:

```powershell
python -m src.embeddings.build_embeddings ..\05_document_chunking\outputs\employee_policy_md_character_chunked.json --index-dir .\outputs\embeddings\employee_policy_md_character
```

If that character file is missing, regenerate it from Day 05 before continuing:

```powershell
python ..\05_document_chunking\parse-and-chunk.py ..\05_document_chunking\samples\employee_policy_markdown_sample.md --method character --output ..\05_document_chunking\outputs\employee_policy_md_character_chunked.json
```

## Search and evaluate

```powershell
python -m src.retrieval.search --index-dir .\outputs\embeddings\employee_policy_md_structure --query "When is a receipt required?" --top-k 5 --export .\outputs\retrieval_results\receipt.json
python -m src.evaluation.evaluate_retrieval --queries .\test_inputs\retrieval_queries.json --index-dir .\outputs\embeddings\employee_policy_md_structure --output .\outputs\reports\employee_policy_md_structure.json
```

Omit `--query` to enter repeated interactive searches. Use
`--no-query-instruction` only when the index was built with the same option.

## Tests

```powershell
python -m pytest .\tests -q
```

The unit tests use NumPy and a fake model; they do not download BGE. A real
model smoke test is the `build_embeddings` command above. The actual model
download and retrieval evaluation are separate from the unit tests.

## Troubleshooting

- `ModuleNotFoundError`: activate `.venv` or use `.\.venv\Scripts\python.exe`.
- Model download errors: check internet access, disk space, and Hugging Face
  availability; after download, inference itself is local.
- Token-limit skips: reduce Day 05 chunk size or split long tables/prose before
  embedding. The manifest lists every skipped `chunk_id` and reason.
- Dimension/configuration mismatch: search with the same model ID,
  normalization, and query-instruction setting used to build the index.
- Missing character baseline: run the Day 05 command above; do not label a
  structure-aware output as character-based.
- Shared dependency installation: from this folder use
  `python -m pip install -r ..\requirements.txt`.
