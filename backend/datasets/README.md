# Cybersecurity Datasets

Place source files in the corresponding `raw/` subdirectory:

- `intrusion/`: cybersecurity and network intrusion records
- `phishing/`: phishing URL records
- `email/`: phishing email records
- `threat_reports/`: NLP threat reports (`.txt`, `.json`, or `.csv`)
- `global_threats/`: global cybersecurity threat records

The pipeline stores normalized records in `processed/` and imports explainable nodes and relationships into the unified cyber graph. Source dataset and record identifiers are retained as lineage metadata.
