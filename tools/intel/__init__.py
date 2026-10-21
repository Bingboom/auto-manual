"""External intelligence loop: collect events, push decisions, keep the judgments.

A self-contained package that can leave this repository as it is. It imports
only the Python standard library and its own modules (relative imports), so
nothing here depends on the rest of ``tools``; ``tests/test_external_intel_boundary.py``
fails if that changes. Everything outside is passed in: the Feishu calls
(``run``), the policy records an event joins, the clock (``today``).

- ``events``: the intake file ``external-intel/events.json`` and its snapshot.
- ``digest``: the push-ready decision digest of a snapshot.
- ``sync``: a Feishu 外部情报 table merged into the intake as append-only revisions.
- ``push``: the digest as one Feishu group post.
- ``delivery``: the pending push kept outside the checkout until a send is acknowledged.
- ``feishu``: lark-cli calls and complete table reads.
- ``files``: atomic replacement of the files the package writes.
- ``wiki``: the Markdown view beside the intake, for Obsidian and llm_wiki.
- ``policies``: the ``market-policy`` records policy events join by ID.
- ``cli``: ``python -m tools.intel sync|push|wiki``.

The host repository renders the research page and the optional product lens
from the package's snapshot and digest; the package never imports them. To
stand alone, move this directory, ``tests/test_intel_*.py`` and
``tests/fixtures/external_intel/`` and rename the ``tools.intel`` import prefix
in those tests.
"""
