import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  buildGraph,
  graphPath,
  loadContent,
  serializeGraph,
  validateContent
} from '../scripts/build-heart-graph.mjs';

const TODAY = '2026-10-28';
const clone = (value) => JSON.parse(JSON.stringify(value));
const content = loadContent();

function errorsFor(mutate, options = {}) {
  const copy = clone(content);
  mutate(copy);
  return validateContent(copy, { today: TODAY, ...options }).errors;
}

function cardById(copy, id) {
  return copy.cards.find((entry) => entry.card.id === id).card;
}

// The shipped pilot content is valid, and the committed graph matches it.
{
  const { errors, drafts } = validateContent(content, { today: TODAY });
  assert.deepEqual(errors, []);
  assert.equal(drafts.length, content.cards.length, 'pilot cards stay drafts until clinicians sign off');
  assert.equal(readFileSync(graphPath, 'utf8'), serializeGraph(buildGraph(content)), 'run npm run build:heart-graph');
}

// The three pilot topics and their key links are present.
{
  const graph = buildGraph(content);
  const ids = new Set(graph.nodes.map((node) => node.id));
  for (const id of ['aortic-stenosis', 'acute-mitral-regurgitation', 'cardiogenic-shock', 'iabp', 'impella', 'va-ecmo']) {
    assert.ok(ids.has(id), `missing pilot card ${id}`);
  }
  const edge = (source, rel, target) => graph.edges.some((e) => e.source === source && e.rel === rel && e.target === target);
  assert.ok(edge('aortic-stenosis', 'located_in', 'aortic-valve'));
  assert.ok(edge('aortic-stenosis', 'treated_by', 'tavr'));
  assert.ok(edge('furosemide', 'caution_in', 'aortic-stenosis'));
  assert.ok(edge('cardiogenic-shock', 'treated_by', 'va-ecmo'));
  const ecmo = graph.nodes.find((node) => node.id === 'va-ecmo');
  assert.deepEqual(ecmo.levers.map((l) => [l.lever, l.effect]), [['afterload', 'increase']]);
  assert.ok(graph.nodes.every((node) => !('relations' in node)), 'relations are flattened into edges');
}

// Strict mode is the launch gate: drafts fail it.
{
  const { errors } = validateContent(content, { today: TODAY, strict: true });
  assert.equal(errors.length, content.cards.length);
  assert.match(errors[0], /draft, pending clinical review/);
}

// Broken content is caught.
const cases = [
  ['unknown target', (c) => { cardById(c, 'aortic-stenosis').relations[0].target = 'no-such-card'; }, /target card does not exist/],
  ['wrong target type', (c) => { cardById(c, 'aortic-stenosis').relations[0].target = 'tavr'; }, /located_in cannot point at a intervention/],
  ['wrong source type', (c) => {
    cardById(c, 'tavr').relations.push({ rel: 'manifests_as', target: 'oliguria', why: 'Not a valid link for a procedure.', citations: ['acc-aha-vhd-2020'] });
  }, /a intervention cannot use manifests_as/],
  ['unknown citation', (c) => { cardById(c, 'iabp').levers[0].citations = ['made-up-2099']; }, /unknown citation "made-up-2099"/],
  ['missing why', (c) => { delete cardById(c, 'pci').relations[0].why; }, /must have required property 'why'/],
  ['therapy without levers', (c) => { delete cardById(c, 'milrinone').levers; }, /needs at least one physiologic lever/],
  ['condition without site', (c) => {
    const card = cardById(c, 'cardiogenic-shock');
    card.relations = card.relations.filter((r) => r.rel !== 'located_in');
  }, /needs at least one located_in structure/],
  ['orphan card', (c) => {
    c.cards.push({ file: 'heart-explorer/content/findings/lonely-sign.json', expectedType: 'finding', card: {
      ...clone(cardById(c, 'oliguria')), id: 'lonely-sign', label: 'Lonely sign'
    } });
  }, /orphan card/],
  ['id and file name differ', (c) => { c.cards[0].card.id = 'renamed-structure'; }, /must match the file name/],
  ['reviewed without both roles', (c) => {
    cardById(c, 'pci').review = {
      status: 'reviewed', draftedBy: 'Claude', nextReviewDue: '2027-06-01',
      reviewers: [
        { name: 'Reviewer A', credential: 'RN, CCRN', role: 'nurse-educator', date: '2026-10-01' },
        { name: 'Reviewer B', credential: 'RN', role: 'nurse-educator', date: '2026-10-02' }
      ]
    };
  }, /need a nurse-educator and a cardiology-clinician/],
  ['reviewed with one reviewer', (c) => {
    cardById(c, 'pci').review = {
      status: 'reviewed', draftedBy: 'Claude', nextReviewDue: '2027-06-01',
      reviewers: [{ name: 'Reviewer A', credential: 'RN, CCRN', role: 'nurse-educator', date: '2026-10-01' }]
    };
  }, /must NOT have fewer than 2 items/]
];
for (const [name, mutate, pattern] of cases) {
  const errors = errorsFor(mutate);
  assert.ok(errors.some((error) => pattern.test(error)), `${name}: expected ${pattern}, got ${JSON.stringify(errors)}`);
}

// An overdue review is a warning by default and an error under --strict.
{
  const overdue = (c) => {
    cardById(c, 'pci').review = {
      status: 'reviewed', draftedBy: 'Claude', nextReviewDue: '2026-01-01',
      reviewers: [
        { name: 'Reviewer A', credential: 'RN, CCRN', role: 'nurse-educator', date: '2025-01-01' },
        { name: 'Reviewer B', credential: 'MD', role: 'cardiology-clinician', date: '2025-01-02' }
      ]
    };
  };
  const copy = clone(content);
  overdue(copy);
  const relaxed = validateContent(copy, { today: TODAY });
  assert.deepEqual(relaxed.errors, []);
  assert.ok(relaxed.warnings.some((warning) => /review was due 2026-01-01/.test(warning)));
  assert.ok(errorsFor(overdue, { strict: true }).some((error) => /review was due 2026-01-01/.test(error)));
}

console.log(`heart graph tests passed (${cases.length} broken-content cases)`);
