# Product matrix seed (spike)

This directory is a seed from a one-off read of all published web manuals on 2026-11-16.
It holds a proposed attribute dictionary of 140 attributes (`attribute_dictionary_v0.csv`)
and the mapping from printed labels in 13 languages to attribute keys (`label_inventory.csv`; example values were removed),
plus the throwaway scripts that produced them (`scripts/`).

It is reference input for the product matrix tooling tracked as REV-50. It is not production
code, is not covered by the repository's guardrails and must not be merged as is.
The files contain no product values: only attribute definitions, printed labels and counts.

How the scripts were run, against a checkout of the published manuals:
`parse_manuals.py` first, then `build_outputs.py`, `prose_scan.py` and `report_stats.py`.
The scripts may contain absolute local paths; they are throwaway and were left as is.
