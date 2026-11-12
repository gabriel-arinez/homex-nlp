'use strict';
(() => {
  const review = JSON.parse(document.getElementById('review-data').textContent);
  const decisions = [...review.annotations.decisions];
  const byId = new Map(review.cases.map(c => [c.id, c]));
  const $ = id => document.getElementById(id);
  let dirty = false;
  function node(tag, text, parent) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (parent) parent.append(element);
    return element;
  }
  function details(title, value, parent) {
    const block = node('details', undefined, parent);
    node('summary', title, block);
    node('pre', JSON.stringify(value, null, 2), block);
  }
  function input(label, parent, value = '') {
    const wrapper = node('label', label, parent);
    const element = node('input', undefined, wrapper);
    element.value = value;
    return element;
  }
  function select(label, choices, parent) {
    const wrapper = node('label', label, parent);
    const element = node('select', undefined, wrapper);
    for (const choice of choices) {
      const option = node('option', choice, element);
      option.value = choice;
    }
    return element;
  }
  function validate(payload) {
    if (payload.schema_version !== 'commercial-human-review/1' || payload.corpus_fingerprint !== review.corpus_fingerprint || !Array.isArray(payload.decisions)) throw Error('Esquema o corpus incompatible');
    const identities = new Map();
    for (const d of payload.decisions) {
      const c = byId.get(d.case_id);
      if (!c || d.source_sha256 !== c.source_sha256) throw Error('Caso o fuente incompatible');
      const known = c.fields.some(f => f.field_key === d.field_key && f.field === d.field);
      const added = typeof d.field_key === 'string' && new RegExp('^new:' + d.field + ':[A-Za-z0-9_-]+$').test(d.field_key);
      if (!review.field_types.includes(d.field) || !(known || added)) throw Error('Campo inválido');
      if (!['PENDIENTE', 'CONFIRMADO', 'CORREGIDO', 'INCIERTO', 'NO_VERIFICABLE'].includes(d.status) || !['SCRIPT_TEXT', 'DOCUMENT_TEXT', 'AUTO_PROPOSAL', 'HUMAN_AUDIO'].includes(d.provenance)) throw Error('Estado o procedencia inválida');
      for (const key of ['decision_id', 'reviewer', 'created_at', 'note', 'reason', 'uncertainty']) if (typeof d[key] !== 'string' || !d[key].trim()) throw Error('Falta ' + key);
      if (!/^[A-Za-z0-9_-]{1,160}$/.test(d.decision_id) || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(d.created_at)) throw Error('Identidad o fecha inválida');
      for (const key of ['unit', 'axis', 'component', 'modality']) if (d[key] !== null && d[key] !== undefined && typeof d[key] !== 'string') throw Error('Tipo inválido: ' + key);
      if ((typeof d.value === 'object' && d.value !== null) || (typeof d.value === 'number' && !Number.isFinite(d.value))) throw Error('Valor no escalar');
      if (d.provenance === 'HUMAN_AUDIO' && d.listening_attested !== true) throw Error('Falta declaración explícita de escucha');
      if (d.provenance === 'HUMAN_AUDIO' && !(Number.isFinite(d.start_seconds) && Number.isFinite(d.end_seconds) && 0 <= d.start_seconds && d.start_seconds < d.end_seconds && d.end_seconds <= c.duration_seconds)) throw Error('Intervalo de escucha inválido');
      const encoded = JSON.stringify(d);
      if (identities.has(d.decision_id) && identities.get(d.decision_id) !== encoded) throw Error('Conflicto de identidad; conservar decisiones separadas');
      identities.set(d.decision_id, encoded);
    }
  }
  function envelope() {
    return {schema_version: 'commercial-human-review/1', corpus_fingerprint: review.corpus_fingerprint, decisions};
  }
  function render() {
    const c = byId.get($('cases').value);
    const root = $('case');
    root.replaceChildren();
    if (!c) return;
    node('h2', c.id + ' — ' + c.category + ' — PENDIENTE', root);
    node('p', c.priority_flags.join(' | '), root);
    const format = select('Audio original ', ['wav', 'original'], root);
    const player = node('audio', undefined, root);
    player.controls = true;
    player.preload = 'metadata';
    player.src = c.audio.wav.url;
    format.onchange = () => { player.src = c.audio[format.value].url; };
    details('Archivos originales y SHA-256 (sin copias)', c.audio, root);
    node('h3', 'Guion — SCRIPT_TEXT (no verdad acústica)', root);
    node('pre', c.reference.script_text, root);
    node('h3', 'Documento — DOCUMENT_TEXT', root);
    node('pre', c.reference.document_text, root);
    details('Procedencia completa del guion y documento', c.reference, root);
    node('h3', 'ASR original — segmentos no alineados al guion', root);
    node('pre', c.original_asr.text_original, root);
    for (const segment of c.original_asr.segments || []) {
      const button = node('button', `${segment.start_seconds}–${segment.end_seconds}s: ${segment.text}`, root);
      button.onclick = () => { player.currentTime = Number(segment.start_seconds); player.play().catch(e => { $('message').textContent = e.message; }); };
    }
    node('h3', 'Comparación comercial — AUTO_PROPOSAL', root);
    const table = node('table', undefined, root);
    const header = node('tr', undefined, table);
    for (const title of ['Campo', 'Guion/documento + procedencia', ...Object.keys(c.nlp), 'Estado humano']) node('th', title, header);
    for (const field of review.field_types) {
      const row = node('tr', undefined, table);
      node('td', field, row);
      node('td', JSON.stringify(c.field_types[field]), row);
      for (const result of Object.values(c.nlp)) {
        const predicted = (result.predicted_fields || []).filter(f => f.field === field);
        node('td', JSON.stringify(predicted.length ? predicted : {value: null, status: 'SIN_PROPUESTA_O_NO_SOPORTADO'}), row);
      }
      node('td', 'PENDIENTE — revisar historial explícito', row);
    }
    for (const [identity, result] of Object.entries(c.nlp)) details('NLP completo: ' + identity + ' (identidad y advertencias)', result, root);
    node('h3', 'Decisión humana explícita — no certificada por máquina', root);
    node('p', 'Cada decisión agrega historial; discrepancias se conservan, nunca se resuelven automáticamente. Escuchar no modifica estados. HUMAN_AUDIO es una declaración personal del revisor.', root);
    const form = node('form', undefined, root);
    const field = select('Campo ', review.field_types, form);
    const fieldKey = select('Dato existente o nuevo ', ['NUEVO', ...c.fields.map(f => f.field_key)], form);
    fieldKey.onchange = () => { const existing = c.fields.find(f => f.field_key === fieldKey.value); if (existing) field.value = existing.field; };
    const value = input('Valor (JSON escalar; texto entre comillas) ', form, 'null');
    const unit = input('Unidad ', form);
    const axis = input('Eje ', form);
    const component = input('Componente/asociación ', form);
    const modality = input('Modalidad ', form);
    const provenance = select('Procedencia ', ['SCRIPT_TEXT', 'DOCUMENT_TEXT', 'AUTO_PROPOSAL', 'HUMAN_AUDIO'], form);
    const status = select('Estado ', ['PENDIENTE', 'CONFIRMADO', 'CORREGIDO', 'INCIERTO', 'NO_VERIFICABLE'], form);
    const reviewer = input('Nombre del revisor ', form);
    const start = input('Inicio de escucha (segundos) ', form);
    const end = input('Fin de escucha (segundos) ', form);
    const note = input('Nota/fuente de evidencia ', form);
    const reason = input('Motivo de confirmación/corrección ', form);
    const uncertainty = input('Incertidumbre explícita ', form);
    const attest = input('Declaro haber escuchado el intervalo indicado (solo HUMAN_AUDIO) ', form);
    attest.type = 'checkbox';
    const save = node('button', 'Agregar decisión al historial', form);
    save.type = 'submit';
    form.addEventListener('input', () => { dirty = true; });
    form.onsubmit = event => {
      event.preventDefault();
      try {
        if (provenance.value === 'HUMAN_AUDIO' && !attest.checked) throw Error('Se requiere declaración explícita de escucha');
        const identity = 'd_' + Date.now() + '_' + Math.random().toString(36).slice(2);
        const decision = {decision_id: identity, case_id: c.id, field_key: fieldKey.value === 'NUEVO' ? 'new:' + field.value + ':' + identity : fieldKey.value, field: field.value, source_sha256: c.source_sha256, status: status.value, provenance: provenance.value, listening_attested: provenance.value === 'HUMAN_AUDIO' && attest.checked, reviewer: reviewer.value, start_seconds: start.value === '' ? null : Number(start.value), end_seconds: end.value === '' ? null : Number(end.value), note: note.value, reason: reason.value, uncertainty: uncertainty.value, value: JSON.parse(value.value), unit: unit.value || null, axis: axis.value || null, component: component.value || null, modality: modality.value || null, created_at: new Date().toISOString()};
        validate({...envelope(), decisions: [...decisions, decision]});
        decisions.push(decision);
        dirty = true;
        $('message').textContent = 'Decisión agregada. Exporte el historial para conservarla.';
        render();
      } catch (error) { $('message').textContent = error.message; }
    };
    details('Historial completo; decisiones coexistentes pueden estar en conflicto', decisions.filter(d => d.case_id === c.id), root);
  }
  function filter() {
    const current = $('cases').value;
    $('cases').replaceChildren();
    const search = $('filter').value.toLowerCase();
    for (const c of review.cases.filter(c => (c.id + ' ' + c.category + ' ' + c.priority_flags.join(' ')).toLowerCase().includes(search))) {
      const option = node('option', c.id + ' — ' + c.category, $('cases'));
      option.value = c.id;
    }
    if ([...$('cases').options].some(o => o.value === current)) $('cases').value = current;
    render();
  }
  $('filter').oninput = filter;
  $('cases').onchange = render;
  $('export').onclick = () => {
    const blob = new Blob([JSON.stringify(envelope(), null, 2) + '\n'], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const anchor = node('a');
    anchor.href = url;
    anchor.download = 'commercial-human-review.json';
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    dirty = false;
    $('message').textContent = 'Exportación solicitada; verifique el archivo descargado.';
  };
  $('import').onchange = async () => {
    try {
      const payload = JSON.parse(await $('import').files[0].text());
      validate(payload);
      // Validate the whole merge before mutation. Identical identities deduplicate;
      // independent conflicting decisions remain visible in the history.
      validate({...envelope(), decisions: [...decisions, ...payload.decisions]});
      const existing = new Set(decisions.map(d => d.decision_id));
      for (const d of payload.decisions) if (!existing.has(d.decision_id)) { decisions.push(d); existing.add(d.decision_id); }
      dirty = true;
      $('message').textContent = 'Historial importado sin sobrescribir decisiones. Revise posibles conflictos.';
      render();
    } catch (error) { $('message').textContent = 'Importación rechazada: ' + error.message; }
  };
  window.addEventListener('beforeunload', event => { if (dirty) { event.preventDefault(); event.returnValue = ''; } });
  filter();
})();
