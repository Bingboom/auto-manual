# Build guide: Web components on public ManualIR

Part of the [build guide](../build_doc_guide.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

Web specification IR: declared `h2.hb-spec-section` / governed table pairs now
pass through the public ManualSource assembler and ManualIR validator before
Web rendering. Web-profile builds bypass Word specification text extraction,
preserving authored links, emphasis, line breaks and trailer content. Document
profile behavior stays with its existing Word reader. All declared sections
must pass before any section is replaced. The adapter is a scoped prepared-HTML
projection, not a whole-book IR; other Web components and neutral rich-text
parsing remain pending in the [shared-source plan](../dev/latex_indesign_same_source_plan.md).


Web LCD and troubleshooting tables also consume public ManualIR. Both prepared
Web bundles and standalone `{lcd-icons}` / `{troubleshooting}` directives share
one source decoder and consumer, retaining the assembly planner's explicit page
identity or authored table class. Filenames and translated header vocabulary
never select a table. A later invalid table rejects the complete transformation
before changing the caller DOM. Rich lists, links, icon alt text, figure captions
and authored headers survive IR serialization/replay. A governed figure containing
multiple tables is ambiguous and fails closed rather than duplicating content.
Standalone staging includes the bounded IR runtime, language registry and existing
table stylesheet contract; it does not import the source checkout or legacy IDML
extractor. `web_source` is the shared provenance constructor, including the active
specification adapter. Remaining whole-manual and HTML-parser boundaries are
tracked in the [shared-source plan](../dev/latex_indesign_same_source_plan.md).


Standalone `{spec-table}` now uses the same public specification IR adapter and
consumer as prepared Web builds. The directive keeps its inline escaping and
row tokenization, supplies the authored section argument to IR, and emits only
the figure (no extra heading). Its private grouping/rowspan/final-table renderer
is retired. Empty, extra-column or orphan-continuation rows fail through the
shared source contract; corrupt IR fails before raw HTML is returned. Plain
circled footnote references use the common Web superscript style; explicit
superscripts are not nested. Staging includes the existing specification adapter
and consumer modules. Commands, editing surfaces and `manual-ir/v1` are unchanged.


Prepared Web warning/note tables now cross the Pandoc boundary as public
ManualIR. The source adapter validates the declared label/body geometry and
records ComponentSpec, rich HTML and image references. Restoration validates
both the public envelope and agreement of semantics/assets with the markup,
then returns the original HTML bytes without reopening the source file. Actual
bundle path/model/region are supplied by the build; table language is retained
or reported as `und`. Corrupt IR or malformed declared callouts fail the build.
The internal placeholder map no longer accepts raw HTML as a parallel restore
path. CLI commands and `manual-ir/v1` remain unchanged. Notices inside
already-protected composite figures remain separate; see the
[shared-source plan](../dev/latex_indesign_same_source_plan.md).


Standalone `{callout}` now uses that same public IR adapter and consumer after
Sphinx renders its parsed child nodes. This preserves resolved cross-references,
image paths, lists and inline markup. Explicit `:variant:` remains authoritative
for custom labels; configured language is carried even when source HTML has no
`lang` attribute. The owned optional declaration is validated and replayed with
the component semantics. Old prepared-Web projection payloads remain unchanged.
The staged runtime reuses existing callout modules; an extension environment
version change invalidates old doctrees. Nested tables or callouts in a callout
body fail the shared single-table contract with source context; they are not
silently flattened. Other rich Markdown nodes continue through Sphinx, and
non-HTML writers retain ordinary body rendering.


Prepared Web Inbox now assembles and consumes a scoped public IR before its
figure enters Pandoc protection. The existing `HB-SPECIAL-INBOX` owns all three
cards and its TIP label/body; no second callout interpretation is introduced.
The `web-inbox` projection retains the ComponentSpec, heading/card/tip markup
and image references, with actual source/model/region/language context. Replay
validates hashes, semantics and complete unspanned rows before replacing caller
DOM. The direct ComponentSpec-only Web path and hardcoded `und` facade have
exited. Existing figure-target admission and EN/FR/ES output stay unchanged;
other composite figures and the generic figure protection map remain separate.


Prepared Web FCC now uses the public source/assembler/consumer path as well.
The `web-fcc` projection carries its existing `HB-SPECIAL-FCC` ComponentSpec
(opening lines, ordered paragraphs/measures, column break) plus the resolved
logical-mark-to-image binding. Rendering uses those semantics directly and
needs neither original HTML nor FCC marker configuration after serialization.
The source adapter records actual target context and hashes the active FCC
config with registry/theme provenance. Invalid IR, source identity or mark
binding fails before the original page is changed. The old direct Web
ComponentSpec-only route exits; existing marker/filename language fallback,
paragraph normalization and three-locale output remain. FCC admission now follows source content across all targets.
This is not a new general rich-text parser or a Word/IDML FCC migration.


The prepared Web signal-word legend now crosses public IR before its figure is
protected. The `web-symbol-signals` projection owns localized headers, labels,
meanings, retained table markup and image references. The existing source gate
still selects the table; replay verifies public hashes and semantic/markup/asset
agreement before applying the completed figure. Every row's localized label and
complete unspanned two-cell geometry are checked before any caller DOM mutation.
This closes the former partial-change failure on a malformed final label. Rich
meaning markup and whitespace left by print-column removal are preserved; the
captured EN/FR/ES outputs are byte-identical. The adjacent symbol-pair table,
other figure admission, CLI and `manual-ir/v1` stay unchanged.


The adjacent icon/meaning matrix now also uses public IR. Its scoped
`web-symbol-pairs` block retains four localized headers, ordered left/right
pairs, table markup and image references. The existing left-six/right-five
contract is unchanged. The source decoder rejects ambiguous candidates,
empty/spanned/nested rows, missing/multiple icon sources and nonempty content
in a would-be-discarded right pair before caller mutation. The Web main module's
direct matrix decoder/render loop has moved to the IR source and a dedicated
pair consumer. Both symbol-table families share provenance/envelope checks;
the existing signal IR bytes remain unchanged. Actual EN/FR/ES whole-page
outputs are byte-identical. Fixed matrix admission and retained-HTML parsing
remain source debt; other components and JP native layout are separate.


App download now follows `ManualSource → public IR → Web consumer` before
figure protection. The `web-app-download` projection carries its heading label,
original semantic image, two ordered rich-copy columns, store/QR artwork
bindings and complete image references. The old direct source/render function
exits `web_presentation`. Replay needs neither the source file nor source config;
it checks hashes, column semantics/order and markup/assets before changing the
caller. Ambiguous image/heading candidates, incomplete copy and empty artwork
bindings fail atomically. Existing target admission, one-split/two-paragraph
input forms and EN/FR/ES whole-page output stay unchanged. Paragraph splitting
and retained inline HTML remain source-adapter debt; App inline controls,
reference figures and JP native layout are separate.


The App add-device inline button also crosses public IR. `web-app-control`
retains its source paragraph, localized label and image references; the source
adapter owns prefix/button-vocabulary matching. Replay validates markup/label/
asset agreement without reopening the source or config, then substitutes the
same accessible `+` glyph in the same sentence position. Duplicate paragraphs,
missing/multiple/empty labels or artwork inside the consumed label fail before
caller mutation. The old direct function exits `web_presentation`. Existing
EN/FR/ES output, source/target gate and Pandoc inline protection stay unchanged;
retained HTML, source matching and the raw inline handoff remain adapter debt.

JBP-2000B EU English Web intake uses `configs/config.bp-eu-en.yaml` and the
[versioned Git source](../../manual_sources/JBP-2000B/EU/en/2.0/README.md); the
existing six-language BP configuration remains available.

Web 提示框支持 `NOTES` 标签；纯文字 LCD 说明表隐藏无对应图标的编号和空图标列。已包含在整图中的开关文字，通过插图覆盖声明移除重复显示。
