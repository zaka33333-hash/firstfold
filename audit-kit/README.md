# FirstFold fulfillment kit

Generate a polished, self-contained HTML conversion audit from structured JSON. It uses only Python's standard library and makes no network calls or paid-API requests.

## Quick start

From the repository root:

```sh
python3 audit-kit/generate_audit.py audit-kit/example-input.json sample-report.html
```

Open `sample-report.html` in a browser or send it as a standalone attachment. All styling is embedded in the final file.

## Input

Use [`example-input.json`](example-input.json) as the starting point and consult [`schema.json`](schema.json) for the field shape. The generator enforces the practical requirements that make a report complete:

- at least one issue, each with severity, impact, effort, evidence, finding, and recommendation;
- exactly five test hypotheses;
- a seven-day plan containing days 1–7 once each;
- a complete hero-copy rewrite.

The allowed issue severities are `critical`, `high`, `medium`, and `low`; allowed effort sizes are `small`, `medium`, and `large`.

Add `"fictional": true` under `meta` whenever an input is demonstrative. The report will then display an unmissable fictional-report label.

## Generate your report

```sh
python3 audit-kit/generate_audit.py path/to/client-audit.json path/to/client-audit.html
```

Optional paths are available if you deliberately customize the presentation layer:

```sh
python3 audit-kit/generate_audit.py input.json output.html \
  --template audit-kit/templates/report.html --css audit-kit/styles/report.css
```

## Validation

Validation runs before an output file is written. Errors identify the JSON path and expected value, for example:

```text
Audit generation failed: test_hypotheses: must contain exactly 5 hypotheses
```

Use the sample report only as a sales/demo asset: it is explicitly fictional and makes no performance claim. All generated reports include a caveat that recommendations are hypotheses until verified through analytics, research, and controlled testing.

## Files

- `generate_audit.py` — command-line generator and dependency-free validator.
- `example-input.json` — fully populated fictional example.
- `schema.json` — portable schema reference for integrations and form builders.
- `templates/report.html` — semantic report layout.
- `styles/report.css` — report presentation, inlined at generation time.
