# Day 06 — Embeddings and retrieval: searching by meaning

| | |
|---|---|
| **Folder** | `06_embedding_and_retrieval/` — `src/`, `tests/`, `test_inputs/`, `SETUP.md`, `README.md` |
| **Commands** | build → `src.embeddings.build_embeddings`; search → `src.retrieval.search`; measure → `src.evaluation.evaluate_retrieval` |
| **Needs** | Internet **once** (downloads a ~130 MB embedding model). No Ollama. |
| **Time** | 1.5–2 hours |
| **Depends on** | Day 05 chunk files. **Days 07 and 08 depend on the index you build here.** |

Longer walkthrough: `day_6 (running guide).md` in this folder.

---

## 1. What you are learning

Keyword search finds the words you typed. **Embedding search finds the meaning
you meant.** "How long do I have to claim expenses?" matches a sentence about a
"30 calendar day submission deadline" even though they share almost no words.

How it works, step by step:

1. An **embedding model** (`BAAI/bge-small-en-v1.5`, running locally on CPU)
   turns any text into a list of **384 numbers**. Similar meaning → similar numbers.
2. You embed every chunk **once** and save the vectors — that is the *index*
   (`vectors.npz` + `metadata.json` + `manifest.json`).
3. At question time you embed the *question* the same way and find the stored
   vectors that point in the most similar direction (**cosine similarity**).
4. You return the **top-k** best chunks.

You also learn the habits that make this trustworthy:

- **The manifest.** It records the model, dimension, normalisation and the
  query-instruction setting used to build the index. Searching with different
  settings gives wrong results *silently*, so the code checks them.
- **The query instruction.** BGE is *asymmetric*: questions get a prefix
  (`Represent this sentence for searching relevant passages:`), passages do not.
- **Caching and skipping.** Unchanged chunks are reused; over-length chunks are
  skipped and listed with a reason.
- **Measuring retrieval** with **Recall@k** ("was the right chunk in the top k?")
  and **MRR** ("how high up was it?").

## 2. Setup

Nothing beyond the shared environment (it already contains
`sentence-transformers` and PyTorch, which is why the install is large).

The first build downloads the model into your Hugging Face cache
(`C:\Users\<you>\.cache\huggingface\hub`, about 130 MB). It needs internet once.
Hugging Face prints `Warning: You are sending unauthenticated requests` — that is
only a speed warning; you do not need a token.

Optional variables (defaults shown in the shared `.env`):

```ini
EMBEDDING_MODEL_ID=BAAI/bge-small-en-v1.5
EMBEDDING_BATCH_SIZE=32
EMBEDDING_NORMALIZE=true
EMBEDDING_USE_QUERY_INSTRUCTION=true
```

## 3. Run

```powershell
Set-Location "$ai\06_embedding_and_retrieval"
```

**3.1 Tests (no model download — they use a fake model)**

```powershell
& $py -m pytest -q          # 8 passed
```

**3.2 Build the index** — this is the step Days 07 and 08 need:

```powershell
& $py -m src.embeddings.build_embeddings `
      ..\05_document_chunking\outputs\employee_policy_md_chunked.json `
      --index-dir .\outputs\embeddings\employee_policy_md_structure
```

It prints the manifest as JSON and creates three files in the index folder. Run
it again and it reuses cached vectors for unchanged chunks.

**3.3 Search**

```powershell
& $py -m src.retrieval.search `
      --index-dir .\outputs\embeddings\employee_policy_md_structure `
      --query "When is a receipt required?" --top-k 5
```

Leave `--query` off for an interactive loop. Add `--export .\outputs\retrieval_results\receipt.json`
to save results. Add `--no-query-instruction` **only** if the index was built the
same way.

**3.4 Measure**

```powershell
& $py -m src.evaluation.evaluate_retrieval `
      --queries .\test_inputs\retrieval_queries.json `
      --index-dir .\outputs\embeddings\employee_policy_md_structure `
      --output .\outputs\reports\employee_policy_md_structure.json
```

**3.5 Optional: compare chunking methods** (needs a character-chunked file that is
not committed — create it from Day 05 first):

```powershell
& $py ..\05_document_chunking\parse-and-chunk.py `
      ..\05_document_chunking\samples\employee_policy_markdown_sample.md `
      --method character --output ..\05_document_chunking\outputs\employee_policy_md_character_chunked.json
& $py -m src.embeddings.build_embeddings `
      ..\05_document_chunking\outputs\employee_policy_md_character_chunked.json `
      --index-dir .\outputs\embeddings\employee_policy_md_character
```

Then run 3.4 against each index and compare the numbers.

## 4. What to test

- [ ] **A question that is in the document** ("When is a receipt required?"). Is the
  right chunk rank 1?
- [ ] **A paraphrase** ("Do I need proof of purchase?"). Does meaning-matching work
  without the same words?
- [ ] **A question the document cannot answer** ("How many days of parental
  leave do I get?"). Look at the *scores*, not just the text.
- [ ] **A totally unrelated question** ("What is the capital of France?").
- [ ] **A question in another language or in Hinglish** ("Expense claim kab submit
  karna hai?"). Does the English-only model cope?
- [ ] **Change `--top-k`** to 1, 3, 10 — the ranking is the same; only the cut changes.
- [ ] **Turn off the query instruction** for search only (`--no-query-instruction`) on
  an index built with it. What changes? (The code should object or scores shift.)
- [ ] **Edit the sample policy**, rebuild: which chunks were re-embedded and which
  reused? (Read `reused_from_cache` / `newly_embedded` in the manifest.)
- [ ] **Add your own query** to `test_inputs\retrieval_queries.json` — one the
  document cannot answer. What does the evaluator do with it?
- [ ] **Compare indexes** (3.5): does structure-aware chunking beat character
  chunking on this tiny set?

## 5. What to expect

**Build** (first time: model download, then seconds). The manifest contains:

```json
{ "vector_dimension": 384, "max_seq_length": 512, "normalized": true,
  "query_instruction_enabled": true,
  "chunk_count_input": 11, "chunk_count_indexed": 11,
  "newly_embedded": 11, "skipped_count": 0 }
```

You will also see noisy `Loading weights` progress bars and a `FutureWarning`
about `get_sentence_embedding_dimension`. Both are harmless.

**Search** — real similarity scores (cosine, 0–1) for the top result:

| Question | Top similarity | Top chunk |
|---|---|---|
| "When is a receipt required?" | **0.802** | 2.1 Submission deadline and required context ✔ the right one |
| "How long do employees have to submit an expense claim?" | **0.876** | 2.1 Submission deadline… ✔ |
| "Do I need proof of purchase?" *(paraphrase, no shared keywords)* | **0.677** | 2.1 … ✔ right section |
| "Expense claim kab submit karna hai?" *(Hinglish)* | **0.678** | 2.1 … ✔ right section, but rank 2 is only 0.648 behind |
| "How many days of parental leave do I get?" | **0.605** | 5. Quick Review Checklist (irrelevant) |
| "What is the capital of France?" | **0.413** | 3.3 Spending limits (irrelevant) |

Two things to notice. Meaning-matching genuinely works: the paraphrase and even
the Hinglish question found the right section, though with a **lower score and a
thinner lead** than the plain English question. And look at what the bottom two
rows show: **the search returned a full list of top-k results for every question,
including the two it cannot answer.** The *score* is the only hint, and nothing
in the code turns a low score into "no answer".

**Evaluate:**

```json
{ "recall_at_1": 1.0, "recall_at_3": 1.0, "recall_at_5": 1.0, "mrr": 1.0 }
```

for `queries_total: 4`, `queries_evaluated: 4`.

**Tests:** `8 passed` in under a second.

Files created: `outputs\embeddings\employee_policy_md_structure\{vectors.npz, metadata.json, manifest.json}`
(≈ 30 KB total). They are **git-ignored**.

## 6. If something goes wrong

| You see | Cause | Fix |
|---|---|---|
| `FileNotFoundError … employee_policy_md_chunked.json` | Wrong relative path | Run from `06_embedding_and_retrieval`; the file is in `..\05_document_chunking\outputs\` |
| Search says index / vectors not found | You have not built the index (it is not in git) | Run step 3.2 |
| `ValueError: Query-instruction setting does not match the index` (or a dimension/normalisation mismatch) | You searched with a different model, normalisation or query-instruction setting than the build | Search with the same settings, or rebuild. This guard is deliberate |
| Model download fails / hangs | No internet, disk full, proxy | Check network and space; retry. After download it is offline |
| Chunks listed under `skipped_chunks` | Longer than the model's 512-token limit | Re-chunk smaller (Day 05) |
| `ModuleNotFoundError: sentence_transformers` | Wrong Python | `& $py -m pip install -r "$ai\requirements.txt"` |
| Slow first run | Loading PyTorch + the model | Normal; later runs are quicker |

## 7. Learn more

- **Sentence-Transformers documentation** — <https://sbert.net> — models, pooling,
  similarity functions.
- **The model card** for BGE — <https://huggingface.co/BAAI/bge-small-en-v1.5>.
- **MTEB leaderboard** — how embedding models are compared (search "MTEB").
- **Cosine similarity vs dot product vs Euclidean distance**, and why normalised
  vectors make cosine = dot product.
- **Vector databases and ANN indexes** — FAISS, HNSW, Qdrant, Chroma, pgvector.
  Read about *why* they exist (scale) before adopting one.
- **Hybrid search:** combine keyword search (BM25) with embeddings.
- **Rerankers** (cross-encoders): re-score the top 20 with a heavier model.
- **Multilingual embeddings** (e.g. BGE-M3) for Hindi/Hinglish.
- **Information-retrieval metrics:** Recall@k, MRR, nDCG, precision@k.

## 8. What you might be missing

- **A perfect score here is not impressive.** Recall = MRR = 1.0 comes from **four
  queries** whose expected phrases were written *from the document itself*
  (`expected_text_contains`). It proves the pipeline works, not that retrieval is
  good. Add harder, messier questions before trusting any number.
- **Similarity is a hint, not a verdict.** There is no threshold in the code. A
  production system would choose one *using measured data* (e.g. "below 0.6 →
  say I don't know"). The three scores above show why: 0.80 vs 0.61 vs 0.41 is a
  gradient, not a cliff. This gap is the root of Day 07's most important failure.
- **The index must be rebuilt when anything upstream changes** — the chunk file,
  the model, normalisation, or the instruction setting. It does not update itself.
- **The index is not in git on purpose** (`outputs/embeddings/` is ignored). A
  fresh clone has none; Days 07/08/10 live runs will fail until you build it.
- **The model is English-only** (`bge-small-en`), so multilingual input is out of
  its design. It still found the right section for the Hinglish question
  (`Expense claim kab submit karna hai?`), but with a lower score (0.68 vs 0.88)
  and only a thin lead over the next chunk. With a bigger corpus that thin margin
  is where wrong answers come from. A multilingual model is the proper fix.
- **Brute-force search.** With 11 vectors, comparing against all of them is
  instant. That is fine here and the reason no vector database is used; it would
  not scale to millions.
- **No reranking, no hybrid search, no query rewriting.** Retrieval quality has
  headroom; those are the standard next levers.
- **The embedding model is loaded again for each query** in the evaluation (you
  see four `Loading weights` bars). Fine for a lesson; wasteful for real use.
- **512-token limit.** Long chunks are skipped, not shortened — check
  `skipped_count` in the manifest every time you rebuild.
- **Only part of the heading is embedded.** The structure-aware chunker writes the
  nearest section title into the chunk text (`Section: 2.1 Submission deadline…`),
  so that title is embedded. The *full* `heading_path` (the parent headings) is
  metadata only and is not part of the vector. Prepending the whole path to the
  text is a known improvement to try.
- **The stale source path** (`Day5_document_Chunking_Samples\…`) in the metadata
  comes from Day 05's committed outputs; see that guide.
- **Your evaluation numbers belong to one corpus.** Do not quote them as a
  property of "BGE" — quote them as "BGE on this 11-chunk document".

## 9. Where this leads

Day 07 takes the top-k chunks from exactly this index, builds a prompt from them
and asks a model to answer with citations. Whether it *should* answer is the
question Day 06's scores raise and Day 07 and 08 test.
