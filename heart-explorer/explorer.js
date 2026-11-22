/* Heart Explorer card browser. Reads heart-graph.json (built from
   heart-explorer/content by scripts/build-heart-graph.mjs) and renders a
   searchable list plus one card at a time. This is also the accessible
   fallback for the 3D view planned in milestone M1. */
(function () {
  'use strict';

  var TYPE_LABELS = {
    structure: 'Structures',
    dysfunction: 'Valve and muscle dysfunctions',
    syndrome: 'Syndromes',
    finding: 'Findings: symptoms, signs, labs',
    drug: 'Drugs',
    intervention: 'Procedures and surgery',
    device: 'Mechanical devices'
  };
  var TYPE_SINGULAR = {
    structure: 'Structure', dysfunction: 'Dysfunction', syndrome: 'Syndrome', finding: 'Finding',
    drug: 'Drug', intervention: 'Procedure', device: 'Device'
  };
  /* Outgoing label, then the label shown on the target's card. */
  var REL_LABELS = {
    located_in: ['Located in', 'Site of'],
    part_of: ['Part of', 'Includes'],
    flows_to: ['Blood flows to', 'Receives blood from'],
    causes: ['Can cause', 'Can result from'],
    manifests_as: ['Shows up as', 'Seen in'],
    treated_by: ['Treated by', 'Used to treat'],
    acts_on: ['Acts on', 'Targeted by'],
    caution_in: ['Use with caution in', 'Use caution with'],
    complication: ['Can cause', 'Can be caused by']
  };

  var listEl = document.getElementById('hx-list');
  var cardEl = document.getElementById('hx-card');
  var searchEl = document.getElementById('hx-search');
  var leverEl = document.getElementById('hx-lever');
  var countEl = document.getElementById('hx-count');
  var graph;
  var nodesById = {};
  var citationsById = {};
  var leverLabels = {};

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      if (key === 'text') node.textContent = attrs[key];
      else node.setAttribute(key, attrs[key]);
    });
    (children || []).forEach(function (child) { if (child) node.appendChild(child); });
    return node;
  }

  function haystack(node) {
    return [node.label, node.summary].concat(node.aliases || []).join(' ').toLowerCase();
  }

  function matches(node, query, lever) {
    if (lever && !(node.levers || []).some(function (entry) { return entry.lever === lever; })) return false;
    if (!query) return true;
    var text = haystack(node);
    return query.split(/\s+/).every(function (word) { return text.indexOf(word) !== -1; });
  }

  function currentId() {
    var id = decodeURIComponent(location.hash.replace(/^#/, ''));
    return nodesById[id] ? id : null;
  }

  function renderList() {
    var query = searchEl.value.trim().toLowerCase();
    var lever = leverEl.value;
    var selected = currentId();
    var shown = 0;
    listEl.textContent = '';
    Object.keys(TYPE_LABELS).forEach(function (type) {
      var items = graph.nodes.filter(function (node) { return node.type === type && matches(node, query, lever); });
      if (!items.length) return;
      shown += items.length;
      listEl.appendChild(el('h3', { text: TYPE_LABELS[type] }));
      var ul = el('ul');
      items.forEach(function (node) {
        var button = el('button', { type: 'button', 'data-id': node.id, text: node.label });
        if (node.id === selected) button.setAttribute('aria-current', 'true');
        button.addEventListener('click', function () { select(node.id, true); });
        ul.appendChild(el('li', {}, [button]));
      });
      listEl.appendChild(ul);
    });
    countEl.textContent = shown + ' of ' + graph.nodes.length + ' cards';
    if (!shown) listEl.appendChild(el('p', { text: 'No cards match. Try a broader word.' }));
  }

  function cardLink(id) {
    var target = nodesById[id];
    return el('a', { href: '#' + encodeURIComponent(id), text: target ? target.label : id });
  }

  function citationList(ids) {
    var ul = el('ul', { class: 'hx-cites' });
    ids.forEach(function (id) {
      var citation = citationsById[id];
      if (!citation) return;
      var href = citation.doi ? 'https://doi.org/' + citation.doi : citation.url;
      var text = citation.authors + ' ' + citation.title + '. ' + citation.source + (citation.year ? ', ' + citation.year : '') + '.';
      ul.appendChild(el('li', {}, [el('a', { href: href, rel: 'noopener', target: '_blank', text: text })]));
    });
    return ul;
  }

  function relationSection(title, groups) {
    var keys = Object.keys(groups);
    if (!keys.length) return null;
    var section = el('section', { class: 'hx-rel' }, [el('h4', { text: title })]);
    keys.forEach(function (label) {
      section.appendChild(el('p', {}, [el('strong', { text: label })]));
      var ul = el('ul');
      groups[label].forEach(function (entry) {
        ul.appendChild(el('li', {}, [cardLink(entry.id), el('span', { class: 'hx-why', text: ' — ' + entry.why })]));
      });
      section.appendChild(ul);
    });
    return section;
  }

  function renderCard(id, focus) {
    var node = nodesById[id];
    cardEl.textContent = '';
    if (!node) {
      cardEl.appendChild(el('h2', { text: 'Choose a card' }));
      cardEl.appendChild(el('p', { text: 'Start with Aortic stenosis, Acute mitral regurgitation or Cardiogenic shock to follow a full pilot topic.' }));
      return;
    }
    var heading = el('h2', { tabindex: '-1', text: node.label });
    var chips = el('div', { class: 'hx-chips' }, [el('span', { class: 'hx-chip', text: TYPE_SINGULAR[node.type] })]);
    if (node.review.status === 'draft') chips.appendChild(el('span', { class: 'hx-chip hx-draft', text: 'Draft, pending clinical review' }));
    cardEl.appendChild(chips);
    cardEl.appendChild(heading);
    if (node.aliases && node.aliases.length) cardEl.appendChild(el('p', { class: 'hx-aliases', text: 'Also called: ' + node.aliases.join(', ') }));
    cardEl.appendChild(el('p', { text: node.summary }));

    if (node.levers && node.levers.length) {
      cardEl.appendChild(el('h4', { text: 'Physiologic levers' }));
      var levers = el('ul', { class: 'hx-levers' });
      node.levers.forEach(function (entry) {
        var verb = entry.effect === 'increase' ? '↑ Raises ' : '↓ Lowers ';
        var label = leverLabels[entry.lever];
        levers.appendChild(el('li', {}, [el('strong', { text: verb + label.charAt(0).toLowerCase() + label.slice(1) }), el('span', { text: ': ' + entry.why })]));
      });
      cardEl.appendChild(levers);
    }

    if (node.nursingPriorities && node.nursingPriorities.length) {
      cardEl.appendChild(el('h4', { text: 'Nursing priorities' }));
      var priorities = el('ul');
      node.nursingPriorities.forEach(function (text) { priorities.appendChild(el('li', { text: text })); });
      cardEl.appendChild(priorities);
    }

    var outgoing = {};
    var incoming = {};
    var cited = (node.citations || []).slice();
    graph.edges.forEach(function (edge) {
      if (edge.source === id) {
        (outgoing[REL_LABELS[edge.rel][0]] = outgoing[REL_LABELS[edge.rel][0]] || []).push({ id: edge.target, why: edge.why });
        cited = cited.concat(edge.citations);
      } else if (edge.target === id) {
        (incoming[REL_LABELS[edge.rel][1]] = incoming[REL_LABELS[edge.rel][1]] || []).push({ id: edge.source, why: edge.why });
      }
    });
    (node.levers || []).forEach(function (entry) { cited = cited.concat(entry.citations); });
    var relations = relationSection('Connections', outgoing);
    if (relations) cardEl.appendChild(relations);
    var backlinks = relationSection('Linked from', incoming);
    if (backlinks) cardEl.appendChild(backlinks);

    cardEl.appendChild(el('h4', { text: 'Sources' }));
    cardEl.appendChild(citationList(cited.filter(function (value, index) { return cited.indexOf(value) === index; })));
    if (focus) heading.focus();
  }

  function select(id, focus) {
    if (location.hash !== '#' + encodeURIComponent(id)) history.pushState(null, '', '#' + encodeURIComponent(id));
    renderList();
    renderCard(id, focus);
  }

  function init(data) {
    graph = data;
    graph.nodes.forEach(function (node) { nodesById[node.id] = node; });
    graph.citations.forEach(function (citation) { citationsById[citation.id] = citation; });
    graph.levers.forEach(function (lever) {
      leverLabels[lever.id] = lever.label;
      leverEl.appendChild(el('option', { value: lever.id, text: lever.label }));
    });
    searchEl.addEventListener('input', renderList);
    leverEl.addEventListener('change', renderList);
    window.addEventListener('hashchange', function () {
      /* Ignore in-page anchors such as the skip link. */
      if (!currentId()) return;
      renderList();
      renderCard(currentId(), true);
    });
    renderList();
    renderCard(currentId(), false);
  }

  fetch('heart-graph.json')
    .then(function (response) {
      if (!response.ok) throw new Error('HTTP ' + response.status);
      return response.json();
    })
    .then(init)
    .catch(function () {
      cardEl.textContent = '';
      cardEl.appendChild(el('p', { text: 'The card data could not load. Refresh the page, or open it from the published site rather than a local file.' }));
    });
}());
