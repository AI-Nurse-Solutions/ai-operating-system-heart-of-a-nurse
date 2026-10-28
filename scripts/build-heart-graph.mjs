#!/usr/bin/env node
/* Heart Explorer graph build.
   Validates every card in heart-explorer/content against the JSON Schema and
   the graph rules below, then writes heart-explorer/heart-graph.json for the
   static explorer page.

   node scripts/build-heart-graph.mjs            validate + write
   node scripts/build-heart-graph.mjs --check    validate + fail if the committed graph is stale
   node scripts/build-heart-graph.mjs --strict   also fail on draft or overdue cards (launch gate) */

import { readFileSync, readdirSync, writeFileSync, existsSync } from 'node:fs';
import { basename, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import Ajv from 'ajv';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
export const explorerDir = join(root, 'heart-explorer');
export const contentDir = join(explorerDir, 'content');
export const graphPath = join(explorerDir, 'heart-graph.json');

export const TYPE_DIRS = {
  structure: 'structures',
  dysfunction: 'dysfunctions',
  syndrome: 'syndromes',
  finding: 'findings',
  drug: 'drugs',
  intervention: 'interventions',
  device: 'devices'
};
const TYPE_ORDER = Object.keys(TYPE_DIRS);
const CONDITIONS = ['dysfunction', 'syndrome'];
const THERAPIES = ['drug', 'intervention', 'device'];

/* Which card types each relationship may connect. */
export const RELATION_RULES = {
  located_in: { from: CONDITIONS, to: ['structure'] },
  part_of: { from: ['structure'], to: ['structure'] },
  flows_to: { from: ['structure'], to: ['structure'] },
  causes: { from: CONDITIONS, to: CONDITIONS },
  manifests_as: { from: CONDITIONS, to: ['finding'] },
  treated_by: { from: CONDITIONS, to: THERAPIES },
  acts_on: { from: THERAPIES, to: ['structure'] },
  caution_in: { from: THERAPIES, to: CONDITIONS },
  complication: { from: THERAPIES, to: ['finding', ...CONDITIONS] }
};

export const LEVERS = [
  { id: 'preload', label: 'Preload' },
  { id: 'afterload', label: 'Afterload' },
  { id: 'contractility', label: 'Contractility' },
  { id: 'heart-rate', label: 'Heart rate' },
  { id: 'rhythm', label: 'Rhythm' },
  { id: 'o2-supply', label: 'Myocardial O₂ supply' },
  { id: 'o2-demand', label: 'Myocardial O₂ demand' }
];

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

export function loadContent(dir = contentDir) {
  const cards = [];
  for (const [type, folder] of Object.entries(TYPE_DIRS)) {
    const folderPath = join(dir, folder);
    if (!existsSync(folderPath)) continue;
    for (const name of readdirSync(folderPath).filter((file) => file.endsWith('.json')).sort()) {
      const file = join(folderPath, name);
      cards.push({ file: relative(root, file), expectedType: type, card: readJson(file) });
    }
  }
  return { cards, citations: readJson(join(dir, 'citations.json')) };
}

function compileSchemas() {
  const ajv = new Ajv({ allErrors: true });
  return {
    card: ajv.compile(readJson(join(explorerDir, 'schema', 'heart-card.schema.json'))),
    citations: ajv.compile(readJson(join(explorerDir, 'schema', 'citations.schema.json')))
  };
}

function schemaErrors(validate, where) {
  return (validate.errors || []).map((error) => `${where}: ${error.instancePath || '/'} ${error.message}`);
}

/* Returns { errors, warnings, drafts }. `today` is YYYY-MM-DD so tests stay deterministic. */
export function validateContent({ cards, citations }, { strict = false, today = new Date().toISOString().slice(0, 10) } = {}) {
  const errors = [];
  const warnings = [];
  const drafts = [];
  const schemas = compileSchemas();

  if (!schemas.citations(citations)) errors.push(...schemaErrors(schemas.citations, 'content/citations.json'));
  const citationIds = new Set();
  for (const citation of Array.isArray(citations) ? citations : []) {
    if (citationIds.has(citation.id)) errors.push(`content/citations.json: duplicate citation id "${citation.id}"`);
    citationIds.add(citation.id);
  }

  const byId = new Map();
  for (const { file, expectedType, card } of cards) {
    if (!schemas.card(card)) {
      errors.push(...schemaErrors(schemas.card, file));
      continue;
    }
    if (basename(file, '.json') !== card.id) errors.push(`${file}: id "${card.id}" must match the file name`);
    if (card.type !== expectedType) errors.push(`${file}: type "${card.type}" belongs in ${TYPE_DIRS[card.type]}/`);
    if (byId.has(card.id)) errors.push(`${file}: duplicate id "${card.id}" (also in ${byId.get(card.id).file})`);
    byId.set(card.id, { file, card });
  }

  const linked = new Set();
  const citedBy = (ids, where) => {
    for (const id of ids || []) {
      if (!citationIds.has(id)) errors.push(`${where}: unknown citation "${id}"`);
    }
  };

  for (const { file, card } of byId.values()) {
    citedBy(card.citations, file);
    for (const lever of card.levers || []) citedBy(lever.citations, `${file} lever ${lever.lever}`);

    const seen = new Set();
    for (const relation of card.relations) {
      const where = `${file} ${relation.rel} -> ${relation.target}`;
      citedBy(relation.citations, where);
      const key = `${relation.rel}:${relation.target}`;
      if (seen.has(key)) errors.push(`${where}: duplicate relation`);
      seen.add(key);
      if (relation.target === card.id) errors.push(`${where}: a card cannot relate to itself`);
      const target = byId.get(relation.target);
      if (!target) {
        errors.push(`${where}: target card does not exist`);
        continue;
      }
      const rule = RELATION_RULES[relation.rel];
      if (!rule.from.includes(card.type)) errors.push(`${where}: a ${card.type} cannot use ${relation.rel}`);
      if (!rule.to.includes(target.card.type)) errors.push(`${where}: ${relation.rel} cannot point at a ${target.card.type}`);
      linked.add(card.id);
      linked.add(relation.target);
    }

    if (CONDITIONS.includes(card.type) && !card.relations.some((relation) => relation.rel === 'located_in')) {
      errors.push(`${file}: a ${card.type} needs at least one located_in structure`);
    }
    if (THERAPIES.includes(card.type) && !(card.levers || []).length) {
      errors.push(`${file}: a ${card.type} needs at least one physiologic lever`);
    }

    const { review } = card;
    if (review.status === 'draft') {
      drafts.push(file);
      if (strict) errors.push(`${file}: draft, pending clinical review`);
    } else {
      const roles = new Set(review.reviewers.map((reviewer) => reviewer.role));
      if (!roles.has('nurse-educator') || !roles.has('cardiology-clinician')) {
        errors.push(`${file}: reviewed cards need a nurse-educator and a cardiology-clinician reviewer`);
      }
      if (review.nextReviewDue < today) {
        (strict ? errors : warnings).push(`${file}: review was due ${review.nextReviewDue}`);
      }
    }
  }

  for (const { file, card } of byId.values()) {
    if (!linked.has(card.id)) errors.push(`${file}: orphan card, nothing links to or from it`);
  }

  return { errors, warnings, drafts };
}

export function buildGraph({ cards, citations }) {
  const nodes = cards
    .map(({ card }) => card)
    .sort((a, b) => TYPE_ORDER.indexOf(a.type) - TYPE_ORDER.indexOf(b.type) || a.id.localeCompare(b.id))
    .map(({ relations, ...card }) => card);
  const edges = cards
    .flatMap(({ card }) => card.relations.map((relation) => ({ source: card.id, ...relation })))
    .sort((a, b) => a.source.localeCompare(b.source) || a.rel.localeCompare(b.rel) || a.target.localeCompare(b.target));
  const counts = Object.fromEntries(TYPE_ORDER.map((type) => [type, nodes.filter((node) => node.type === type).length]));
  return {
    notice: 'Generated by scripts/build-heart-graph.mjs from heart-explorer/content. Edit the cards, not this file. Educational content only: not clinical guidance.',
    levers: LEVERS,
    stats: {
      nodes: nodes.length,
      edges: edges.length,
      drafts: nodes.filter((node) => node.review.status === 'draft').length,
      byType: counts
    },
    nodes,
    edges,
    citations: [...citations].sort((a, b) => a.id.localeCompare(b.id))
  };
}

export function serializeGraph(graph) {
  return `${JSON.stringify(graph, null, 2)}\n`;
}

function main(argv) {
  const strict = argv.includes('--strict');
  const check = argv.includes('--check');
  const content = loadContent();
  const { errors, warnings, drafts } = validateContent(content, { strict });

  if (warnings.length) {
    console.warn(`${warnings.length} warning(s):`);
    for (const warning of warnings) console.warn(`  - ${warning}`);
  }
  if (drafts.length && !strict) {
    console.warn(`${drafts.length} of ${content.cards.length} cards are drafts pending clinical review (--strict lists them and fails).`);
  }
  if (errors.length) {
    console.error(`Heart graph is invalid, ${errors.length} error(s):`);
    for (const error of errors) console.error(`  - ${error}`);
    return 1;
  }

  const graph = buildGraph(content);
  const output = serializeGraph(graph);
  if (check) {
    const committed = existsSync(graphPath) ? readFileSync(graphPath, 'utf8') : '';
    if (committed !== output) {
      console.error('heart-explorer/heart-graph.json is stale. Run: npm run build:heart-graph');
      return 1;
    }
    console.log(`Heart graph is valid and current: ${graph.stats.nodes} cards, ${graph.stats.edges} links.`);
    return 0;
  }
  writeFileSync(graphPath, output);
  console.log(`Wrote heart-explorer/heart-graph.json: ${graph.stats.nodes} cards, ${graph.stats.edges} links, ${graph.stats.drafts} drafts.`);
  return 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = main(process.argv.slice(2));
}
