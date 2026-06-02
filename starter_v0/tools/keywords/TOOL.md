---
name: keywords
track: bonus
kind: local_formatter
provider: null
requires_env: []
inputs: [text, top_k]
outputs: [keywords]
side_effect: false
requires_confirmation: false
---

# keywords

Extract a small list of keywords from a text snippet.

Notes:
- This is a local helper tool (no API calls).
- Intended for building digests (e.g., suggest tags) or quick topic extraction.

