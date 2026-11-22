# Heart Explorer

An educational heart for nurses: pick a structure, condition, drug, procedure or
device and see how it connects to symptoms, labs, mechanisms and the physiologic
levers each therapy moves. It is built as a **reviewed knowledge graph first**
and a 3D view second, so every card is cited and signed off before release.

This is milestone **M0**: ontology, schema, validation, and three pilot topics
(aortic stenosis, acute mitral regurgitation, cardiogenic shock) as draft cards,
plus a card browser that later becomes the accessible fallback for the 3D view.

> Education only (see `SAFETY.md`, section 1). No patient data. The page is
> `noindex` until every card passes clinical review.

## Layout

| Path | What it is |
| --- | --- |
| `content/<type>/<id>.json` | One card per file. The file name is the card id. |
| `content/citations.json` | Citation registry. Cards cite ids from here. |
| `schema/heart-card.schema.json` | JSON Schema for a card. |
| `schema/citations.schema.json` | JSON Schema for the citation registry. |
| `heart-graph.json` | **Generated.** Do not edit; run the build. |
| `index.html`, `explorer.js` | Static card browser served by GitHub Pages. |

Build and tests: `scripts/build-heart-graph.mjs`, `tests/test_heart_graph.mjs`,
`tests/test_heart_explorer_browser.mjs`, `.github/workflows/heart-explorer.yml`.

## Ontology

Card types: `structure`, `dysfunction`, `syndrome`, `finding`, `drug`,
`intervention`, `device`.

| Relation | From | To |
| --- | --- | --- |
| `located_in` | dysfunction, syndrome | structure |
| `part_of` | structure | structure |
| `flows_to` | structure | structure |
| `causes` | dysfunction, syndrome | dysfunction, syndrome |
| `manifests_as` | dysfunction, syndrome | finding |
| `treated_by` | dysfunction, syndrome | drug, intervention, device |
| `acts_on` | drug, intervention, device | structure |
| `caution_in` | drug, intervention, device | dysfunction, syndrome |
| `complication` | drug, intervention, device | finding, dysfunction, syndrome |

Every relation and every lever effect carries a one-sentence `why` for a bedside
nurse and at least one citation id.

Physiologic levers: `preload`, `afterload`, `contractility`, `heart-rate`,
`rhythm`, `o2-supply`, `o2-demand`. Every drug, intervention and device must
name at least one, with a direction (`increase` or `decrease`).

Structure ids double as mesh names in the M1 glTF model, so hovering a mesh
opens the card with the same id.

## Adding or changing a card

1. Copy a card of the same type, rename the file to the new id, and edit it.
2. Cite only sources in `content/citations.json` (add new ones there with a DOI
   or URL).
3. Run the build and tests:

   ```bash
   npm run build:heart-graph
   npm run test:heart-graph
   npm run test:heart-explorer-browser
   ```

4. Commit the card **and** the regenerated `heart-graph.json`. CI fails if the
   graph is stale.

## Clinical review

New cards are `"status": "draft"` and show a "Draft, pending clinical review"
badge. A card becomes `"reviewed"` only when both a `nurse-educator` and a
`cardiology-clinician` are listed in `review.reviewers` with dates, and
`nextReviewDue` is set (no more than 12 months out). The merged pull request is
the audit record.

`node scripts/build-heart-graph.mjs --strict` fails on any draft or overdue card.
It is the launch gate: when it passes, remove the `noindex` meta tag and add the
page to `sitemap.xml`.

## Roadmap

| Milestone | Deliverable |
| --- | --- |
| M0 (this) | Ontology, schema, validation, pilot cards, card browser |
| M1 | 3D heart (three.js + compressed glTF), hover and tap cards, layer toggles |
| M2 | Reverse lookup: a drug or lab lights up its structures; lever icons |
| M3 | Animated cardiac cycle, pathology states, pressure-volume loop simulation |
| M4 | Device overlays (IABP, Impella, ECMO), scenario mode, self-assessment |
