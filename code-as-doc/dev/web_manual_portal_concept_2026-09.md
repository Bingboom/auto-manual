# Manual portal region selector and twelve-language rollout concept

Status: design proposal. Operator-confirmed visual reference: the Jackery
official site's styling for the manual-center home. Operator-confirmed
interaction: a region dropdown with US selected by default and US / EU / UK
options, product selection, and a twelve-language dropdown linking independent
manual pages. EU and UK share the same product catalog and manuals today.
A language change preserves the product and applicable manual version
and opens the destination manual at its start. Execution ownership remains
[Milestone M](../next_optimization_checklist.md).

## 1. Confirmed scope

Every model in the operator-designated EU rollout will receive English,
French, Spanish, German, Italian, Portuguese, Dutch, Polish, Ukrainian, Greek,
Hebrew and Arabic. The last seven are in translation and will return in batches.
The Portuguese regional variant follows the translation brief when received.

The entrance region selector defaults to US and offers exactly US, EU and UK.
Do not add country-by-country options such as Germany or France, or replace the
US default through inferred geolocation. The selector filters product discovery;
it is distinct from the reading page's language selector.

| Entrance selection | Catalog / manual binding |
| --- | --- |
| US (default) | US product catalog and approved US editions |
| EU | Shared EUUK product catalog and approved EUUK editions |
| UK | The same EUUK catalog, editions and published URLs as EU |

EUUK is a shared catalog binding, not a fourth dropdown option. EU and UK are
separate public choices but must not duplicate source content, assets, builds or
releases. Existing source targets, including current EU build targets, keep
their identifiers; selecting UK does not require creating a UK build target.
Keep the selected EU/UK entrance label in navigation state while resolving both
to the same canonical manual links. Switching EU to UK changes the entrance
selection, not the product list or manual edition.

Approved hardware and legal applicability remain authoritative. US must never
silently fall back to an EUUK manual. If a future product requires distinct
EU/UK editions, change its explicit binding rather than copy the whole catalog.
Language switching always preserves the applicable bound edition. The confirmed
twelve-language rollout above is for the EUUK product set; the US entrance does
not itself declare a new twelve-language requirement for US manuals.

The [current RTD home](https://ht-doc.readthedocs.io/) exposes a flat list of
model/region/manual links. This design adds product discovery around those
existing publications.

## 2. Proposed screen

```text
Jackery | Manuals                                  Region [US v]
                                                          US (selected)
                                                          EU
                                                          UK

                  Find your product manual
       [ Search product name or model number                         ]

 All products | Power stations | Battery packs | Solar panels | Accessories

 [Product image]                 [Product image]             [Product image]
 Explorer 2000                   SolarSaga 100 Air            Battery Pack 2000
 Model: JE-2000F                 Model: JS-100I               Model: JBP-2000B
 [View manual]                   [View manual]               [View manual]

 Product / reading header (after selecting EU or UK):
 < All products     Explorer 2000 · JE-2000F · EUUK     Language [English v]
```

Use product images, consumer names and exact model numbers. Search accepts
both commercial names and model numbers; generation/variant labels distinguish
similarly named products. Category names follow the available catalog.

The product/reading page uses a language dropdown with these options:

English · Français · Español · Deutsch · Italiano · Português · Nederlands ·
Polski · Українська · Ελληνικά · עברית · العربية

Each published option opens that language's independently addressable manual
at its beginning. Preserve the selected product, applicable market edition and
document type. Do not carry chapter anchors or scroll position across languages.
The current page determines the selected option and its lang/dir metadata.

All twelve options may be listed; enable published languages and label disabled
ones Not yet available. Exact production progress remains internal. Existing
published languages stay accessible while new translations are prepared.
A missing requested language offers an explicit published alternative rather
than silently changing the page language.

Use a labeled, keyboard-accessible dropdown on desktop and mobile. Mixed
LTR/RTL labels need directional isolation. On mobile, chapter navigation may
use a drawer; the language selector keeps the same interaction.

The home visually references the [Jackery official site](https://www.jackery.com/):
black/white/orange branding, a prominent search-oriented title, generous spacing,
product imagery and clean cards. Use Jackery orange for primary actions and
active category states, with a responsive product grid beneath search. The
region/product/language information structure above remains the agreed flow.
The reading pages keep the existing shared manual component styles.
Download PDF appears only when a matching approved PDF URL
exists; the current Web publication path does not store print artifacts.

## 3. Language effort and incremental returns

The shared registry already includes EN/FR/ES/DE/IT/UK and Brazilian Portuguese.
[lang_registry.py](../../tools/lang_registry.py) has no Dutch, Polish, Greek,
Hebrew, Arabic or European Portuguese entry, and LanguageSpec has no direction
field. Inspected Web styles contain physical left/right rules with no general
RTL policy. Twelve-language support therefore requires shared implementation
work as well as content intake.

Existing LTR languages primarily need matching translated content and assets.
New LTR languages need metadata, localized labels, reusable content carriers,
font checks and validation. Hebrew and Arabic additionally need one shared RTL
implementation: lang/dir, logical CSS spacing, navigation, font coverage and
bidirectional isolation for model numbers, units, URLs and mixed text.
Use real returned Arabic/Hebrew copy to verify shaping and table readability.

Preserve semantic slot and component IDs across locales. Tables remain
structured HTML; Overview, Operation and Charging require locale-matched
text-bearing full panels. Product diagrams and approved images keep their
physical orientation. Do not mirror all artwork for RTL. Text-only returns may
leave an illustration gap even after all prose is available.

Track required, received, reviewed, verified and published coverage separately
for each model, document type, source revision and locale. A future requirement
must not be added blindly to runtime build declarations before its inputs exist.
Previously published translations retain their own content revision.

Print renderer expansion and IR-D01 through IR-D06 remain deferred.

## 4. Publication and catalog design

[publish_branch_assembly.py](../../tools/publish_branch_assembly.py) currently
stores a release at model/region/md and replaces that directory during staging.
Before separate languages are published incrementally, add language to release
identity, storage, discovery and aggregation together. Verify that publishing
the second language preserves the first. This is a prospective collision risk,
not evidence of existing release loss.

Keep independent locale URLs and compatible existing QR/short links. The
dropdown follows the published link index; it does not infer a destination by
replacing strings in the current URL. RTD's project language/version prefix is
separate from manual language and document revision.

Use the existing Sphinx/Read the Docs deployment with a customized static
landing page, product cards and a small search/filter index. Keep ordinary
links usable without JavaScript. Portal code lives in auto-manual and flows
to Hello-Docs through the established publication process.

Generate a compact catalog by combining product metadata with published
release metadata:

| Object | Minimum useful fields |
| --- | --- |
| Product | ID, model, display name, category, image, search aliases |
| Region selection | US / EU / UK, default US, catalog binding US / EUUK |
| Catalog binding | US or shared EUUK group, product ID, applicable existing source/edition |
| Language | code, native label, direction, required status |
| Release | product/edition/type/locale/revision, URL, optional approved PDF URL |

Manual body content remains in its governed frozen sources. The index stores
metadata and links; an online metadata table can be added later without
duplicating the manual corpus.

## 5. Proposed next work

First make the home with its US-default region dropdown, shared EU/UK product
binding, product cards and language dropdown states reviewable with existing
published languages. Prepare the shared language registry, RTL and
locale-specific publication storage while translated copy is returning.
Then enable each verified language incrementally. These are proposed design
steps; Milestone M remains the only execution checklist.

Design acceptance includes the US default and exactly three region options,
identical EU/UK product lists and canonical manual links without duplicate
releases, US edition isolation, model search, mobile dropdown operation, disabled
unpublished options, correct independent URLs, opening the selected language at
its start, preserved product/edition, unchanged QR links, and an RTL example.
