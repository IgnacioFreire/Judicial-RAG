# Notebooks

Local harness for one pipeline stage at a time. Launch from the repo root:

```bash
uv sync --group dev
uv run jupyter lab notebooks
```

Put PDFs in `notebooks/inputs/`, or point `NOTEBOOK_PDF_DIR` at another directory. Each notebook that embeds creates its own in-memory Chroma collection and deletes it in the last cell. Do not commit notebook outputs. PDFs stay out of git.

`SHOW_TEXT` defaults to false. Turn it on in a notebook to print chunk text, answers, or citations on this machine.
