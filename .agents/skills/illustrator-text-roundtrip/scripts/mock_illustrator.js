/*
  mock_illustrator.js — a stand-in for Illustrator's text DOM so the
  ExtendScript importer can be exercised without launching Illustrator.

  It is deliberately faithful on the one behaviour the importer depends on:
  assigning to a TextRange's `contents` splices the character range and the
  replacement inherits the character attributes at the range start. That is
  what makes run-level replacement preserve formatting, and what a
  frame-level assignment destroys.

  Usage (driven by verify_importer.py):
    node mock_illustrator.js <fixture.json> <input.csv> <report.csv> \
         <overrides.json> <Illustrator_Text_Importer.jsx>

  Writes <report.csv> (the importer's own report) plus
  <report.csv>.doc.json — the resulting document text and run profile per
  frame, which is what the assertions are made against.
*/

const fs = require('fs');
const path = require('path');

/* ----------------------------------------------------- document mock */

function makeFrame(spec, idx) {
  const chars = [];
  spec.paragraphs.forEach((runs, pi) => {
    if (pi > 0) {
      chars.push({ ch: '\r', font: 'Gilroy-Regular', size: 7, baseline: 0 });
    }
    runs.forEach((r) => {
      for (const ch of r.text) {
        chars.push({ ch, font: r.font, size: r.size, baseline: r.baseline || 0 });
      }
    });
  });

  const frame = {
    typename: 'TextFrame',
    name: spec.name || '',
    note: '',
    kind: spec.kind || 'POINTTEXT',
    overflows: false,
    hidden: !!spec.hidden,
    locked: !!spec.locked,
    zOrderPosition: idx,
    position: [0, 0],
    visibleBounds: [0, 100, 100, 0],
    _chars: chars,
  };
  frame.parent = {
    typename: 'Layer', name: spec.layer || 'Layer 1',
    hidden: false, locked: false, parent: { typename: 'Document' },
  };

  Object.defineProperty(frame, 'contents', {
    get() { return frame._chars.map((c) => c.ch).join(''); },
    set(v) {
      const a = frame._chars[0] || { font: 'Gilroy-Regular', size: 7, baseline: 0 };
      frame._chars = [...v].map((ch) => ({ ch, font: a.font, size: a.size, baseline: a.baseline }));
    },
  });

  Object.defineProperty(frame, 'characters', {
    get() {
      const view = { length: frame._chars.length };
      for (let i = 0; i < frame._chars.length; i++) {
        const c = frame._chars[i];
        view[i] = {
          contents: c.ch,
          characterAttributes: {
            textFont: { name: c.font },
            size: c.size,
            baselineShift: c.baseline,
            baselinePosition: 'normal',
            fillColor: { typename: 'GrayColor', gray: 60 },
          },
        };
      }
      return view;
    },
  });

  Object.defineProperty(frame, 'textRange', {
    get() {
      const tr = { _s: 0, _e: frame._chars.length };
      Object.defineProperty(tr, 'start', {
        get: () => tr._s,
        set(v) {
          if (v < 0 || v > tr._e) throw new Error('start out of range');
          tr._s = v;
        },
      });
      Object.defineProperty(tr, 'end', {
        get: () => tr._e,
        set(v) {
          if (v < tr._s || v > frame._chars.length) throw new Error('end out of range');
          tr._e = v;
        },
      });
      Object.defineProperty(tr, 'contents', {
        get() { return frame._chars.slice(tr._s, tr._e).map((c) => c.ch).join(''); },
        set(v) {
          const a = frame._chars[tr._s]
            || frame._chars[tr._s - 1]
            || { font: 'Gilroy-Regular', size: 7, baseline: 0 };
          const repl = [...v].map((ch) => ({ ch, font: a.font, size: a.size, baseline: a.baseline }));
          frame._chars.splice(tr._s, tr._e - tr._s, ...repl);
        },
      });
      return tr;
    },
  });

  return frame;
}

const [fixturePath, csvIn, reportOut, overridesJson, scriptPath] = process.argv.slice(2);

const fixture = JSON.parse(fs.readFileSync(fixturePath, 'utf8'));
const frames = fixture.map(makeFrame);

global.app = {
  documents: { length: 1 },
  activeDocument: {
    name: 'fixture.ai',
    textFrames: frames,
    selection: [],
    artboards: {
      length: 1,
      0: { artboardRect: [0, 5000, 7000, 0], name: 'Artboard 1' },
      getActiveArtboardIndex: () => 0,
    },
  },
};
global.TextType = { AREATEXT: 'AREATEXT', POINTTEXT: 'POINTTEXT', PATHTEXT: 'PATHTEXT' };
global.$ = { os: 'Macintosh' };

/* -------------------------------------------------- ScriptUI + File mock */

const OVERRIDES = JSON.parse(overridesJson || '{}');
const alerts = [];
global.alert = (msg) => alerts.push(String(msg));

function mockControl(type, text) {
  const c = {
    __type: type,
    __text: text == null ? '' : String(text),
    __children: [],
    value: false,
    enabled: true,
    items: [],
    _sel: null,
  };
  c.add = (t, bounds, tx) => {
    const k = mockControl(t, tx);
    if (t === 'dropdownlist') k.items = Array.isArray(tx) ? tx : [];
    c.__children.push(k);
    return k;
  };
  Object.defineProperty(c, 'selection', {
    get: () => c._sel,
    set(v) { c._sel = (typeof v === 'number') ? { index: v, text: c.items[v] } : v; },
  });
  return c;
}

function walk(c, fn) { fn(c); c.__children.forEach((k) => walk(k, fn)); }

global.Window = function () {
  const dlg = mockControl('dialog', 'dialog');
  dlg.show = () => {
    // Overrides are matched on the control's own label prefix, so the test
    // states intent ("Dry run": false) instead of control coordinates.
    walk(dlg, (c) => {
      for (const key in OVERRIDES) {
        if (c.__text && c.__text.indexOf(key) === 0) c.value = OVERRIDES[key];
      }
    });
    return 1;
  };
  return dlg;
};

function MockFile(p) {
  this.fsName = p;
  this.name = path.basename(p);
  this.path = path.dirname(p);
  this.error = 0;
  this._buf = '';
  this.open = (mode) => {
    this._mode = mode;
    if (mode === 'r') {
      try { this._buf = fs.readFileSync(p, 'utf8'); } catch (e) { return false; }
    } else {
      this._buf = '';
    }
    return true;
  };
  this.read = () => this._buf;
  this.write = (s) => { this._buf += s; };
  this.close = () => {
    if (this._mode === 'w') fs.writeFileSync(p, this._buf);
    return true;
  };
  this.saveDlg = () => new MockFile(reportOut);
}
global.File = MockFile;
global.File.openDialog = () => new MockFile(csvIn);
global.Folder = function () {};

/* ------------------------------------------------------------ run it */

// Drop the leading `#target illustrator` directive, which is ExtendScript-only.
const source = fs.readFileSync(scriptPath, 'utf8').split('\n').slice(1).join('\n');
eval(source);

const runProfile = (frame) => {
  const out = [];
  frame._chars.forEach((c) => {
    if (c.ch === '\r') return;
    const tag = `${c.font}@${c.size}`;
    if (out.length === 0 || out[out.length - 1] !== tag) out.push(tag);
  });
  return out;
};

fs.writeFileSync(reportOut + '.doc.json', JSON.stringify({
  alerts,
  frames: frames.map((f, i) => ({
    label: 'T' + String(i + 1).padStart(3, '0'),
    contents: f.contents,
    runs: runProfile(f),
  })),
}, null, 1));
