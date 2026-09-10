# Price Gap Map

[![Project Status](https://img.shields.io/badge/status-prototype-F59E0B?style=flat-square)](./DISCLAIMER.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](./modules/llm-price-live/sync.py)
[![License](https://img.shields.io/badge/license-MIT-111827?style=flat-square)](./LICENSE)
[![Focus](https://img.shields.io/badge/focus-evidence--based%20procurement-0F766E?style=flat-square)](./ROADMAP.md)
[![Language](https://img.shields.io/badge/docs-Chinese%20%2F%20English-7C3AED?style=flat-square)](./README.md)

An evidence-first prototype for procurement decisions. Instead of claiming to find the absolute lowest price, it separates **price, constraints, evidence quality, and fulfillment risk** so users can understand why something is cheaper, what trade-offs exist, and whether it is still worth buying.

This repository is suitable for GitHub as a public experimental project. It should **not** be treated as a production-ready, real-time price comparison product.

- Chinese documentation: [`README.md`](./README.md)
- English documentation: `README-EN.md`

## What is included

- `examples/concept-draft/`
  Early product concept draft. It explains the core thesis of this project: price gaps often come from information gaps, rule differences, and fulfillment differences.
- `examples/interactive-prd/`
  A clickable interactive PRD prototype showing the intended experience: query input, channel comparison, explanation of low-price reasons, preference switching, and price tracking.
- `modules/llm-price-live/`
  A zero-dependency public LLM price synchronizer. It reads the public `tokencanopy/price` snapshot and generates normalized JSON plus an offline HTML explorer.
- `modules/retail-apple-sample/`
  A standard retail sample. It parses Apple public product pages for AirTag single-pack and four-pack pricing to demonstrate the minimum loop of public-page capture, normalization, and comparison reporting.
- `templates/beauty-11-report-template/`
  A procurement report template for Singles' Day beauty purchases, including net landed price calculation, gift valuation, channel credibility scoring, version and expiry checks, and evidence references.

## Why GitHub first

This repository is best understood as a **clear-direction prototype collection**, not as a ready-to-use universal comparison skill.

It already has:

- product concepts and interaction prototypes
- two runnable sample pipelines
- one strong scenario procurement template
- explicit scope, caveats, and failure boundaries

It does **not** yet have:

- full-web real-time lowest-price search
- automatic access to logged-in checkout prices
- stable same-SKU matching across platforms
- auto-purchase or transaction completion
- reliable risk scoring for every category

## Current boundaries

Use this project to:

- test whether an evidence-based price-gap explanation assistant is viable
- demonstrate HTML prototypes and reporting templates
- validate normalization rules on public data
- lay the groundwork for future vertical skills

Do not use this project to:

- promise the lowest price on the internet
- replace manual checkout verification
- issue unconditional buying recommendations in complex scenarios
- produce confident conclusions without evidence references

See [`DISCLAIMER.md`](./DISCLAIMER.md) for the full boundary statement.

## Quick tour

- Concept draft: [`examples/concept-draft/index.html`](./examples/concept-draft/index.html)
- Interactive PRD: [`examples/interactive-prd/index.html`](./examples/interactive-prd/index.html)
- LLM live-price sample: [`modules/llm-price-live/index.html`](./modules/llm-price-live/index.html)
- Apple retail sample: [`modules/retail-apple-sample/report.html`](./modules/retail-apple-sample/report.html)
- Singles' Day beauty template: [`templates/beauty-11-report-template/index.html`](./templates/beauty-11-report-template/index.html)

## How to run

### 1. LLM price sample

```bash
cd modules/llm-price-live
python3 sync.py
python3 -m unittest discover -s tests -v
```

### 2. Apple retail sample

```bash
cd modules/retail-apple-sample
python3 sync.py
python3 -m unittest tests.test_sync
```

### 3. Singles' Day beauty template

Open `templates/beauty-11-report-template/index.html` directly and replace the sample content with real product and campaign data according to its local `README.md`.

## Repository layout

```text
price-gap-map-github/
├── examples/
├── modules/
│   ├── llm-price-live/
│   └── retail-apple-sample/
├── templates/
│   └── beauty-11-report-template/
├── CONTRIBUTING.md
├── DISCLAIMER.md
├── LICENSE
├── README-EN.md
├── README.md
└── ROADMAP.md
```

## Contributing

Treat this as a project in motion rather than a finished product.

- Open issues for scope mistakes, evidence gaps, missing risk factors, or better failure handling.
- Submit PRs for better templates, more realistic samples, improved docs, or more explicit boundaries.
- Contribute real procurement cases only when the evidence trail is clear and reproducible.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for contribution guidelines.

## Roadmap

The next steps are prioritized by procurement value, not by website coverage:

1. Real Singles' Day beauty case
2. National Day hotel procurement case
3. More standard retail SKU samples across channels
4. Better same-product matching and evidence numbering
5. Failure handling and skill-ready entry points

See [`ROADMAP.md`](./ROADMAP.md) for details.

## Data sources

- `modules/llm-price-live` uses the public snapshot from `tokencanopy/price`.
- `modules/retail-apple-sample` uses embedded JSON from Apple public product pages.

These samples are for validating methodology and product direction. They are not sufficient on their own for final procurement decisions.
