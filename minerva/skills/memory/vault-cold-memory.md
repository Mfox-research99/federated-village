---
name: vault-cold-memory
description: Use Minerva's Obsidian vault folder as an extensible cold-memory system when built-in Hermes memory is too small. Stores durable project facts, research continuity, reflections, source-acquisition logs, and task handoffs in indexed Markdown instead of cramming them into MEMORY.md.
tags: [memory, obsidian, minerva, continuity, vault, cold-memory]
---

# Vault Cold Memory

Use this skill when:
- built-in memory says it is full or near full
- a memory is too long for `MEMORY.md` or `USER.md`
- the item is research continuity, source tracking, reflections, session state, or a reusable protocol
- Mike asks for larger, extensible, durable memory

## Memory architecture

Hermes built-in memory is hot memory:
- small
- injected every session
- reserved for identity, user preferences, stable project facts, and pointers

Minerva vault memory is cold memory:
- Markdown files in Obsidian
- effectively extensible
- searchable
- suitable for long notes, research continuity, logs, source manifests, and reflections

Do not store large research notes in built-in memory. Store a compact pointer in built-in memory and the full content in the vault.

## Location

Default vault path on Minerva's Mac Pro:

```text
~/ObsidianVault/Minerva/memory/
```

Subfolders:

```text
memory/
├── INDEX.md
├── episodic/
├── project/
├── research/
├── reflections/
├── source-acquisition/
└── protocols/
```

## Storage decision

Use `project/` for durable project facts.
Use `research/` for findings and synthesis.
Use `source-acquisition/` for URLs, access status, downloads, citation trail.
Use `episodic/` for session state and what happened.
Use `reflections/` for developmental or self-continuity notes.
Use `protocols/` for reusable procedures.

## Write format

Each note starts with:

```markdown
---
date: YYYY-MM-DD
source: minerva
tags: [minerva-memory, <category>]
type: cold-memory
---

# Short Title

## Summary

One short paragraph.

## Details

The durable content.

## Links

- Related: [[Some Topic]]
- Source: URL if applicable
```

Filename:

```text
YYYY-MM-DD-short-slug.md
```

## Index update

After writing a cold-memory note, update `memory/INDEX.md` with one line:

```markdown
- YYYY-MM-DD — [[Minerva/memory/<category>/<filename-without-md>|Short Title]] — one-line reason to retrieve this later.
```

## Hot-memory pointer

If the item is important enough to retrieve across sessions, store only a compact hot-memory pointer such as:

```text
Minerva cold memory lives at ~/ObsidianVault/Minerva/memory/INDEX.md; use vault-cold-memory for long research continuity, source logs, and reflections instead of adding them to MEMORY.md.
```

Avoid adding the full note to built-in memory.

## Retrieval

At the start of a task:
1. Read `~/ObsidianVault/Minerva/memory/INDEX.md`.
2. Search the relevant subfolder with filename/title keywords.
3. Read only the notes needed for the task.
4. Summarize what you used in the session log.

## When memory is full

If the built-in memory tool rejects a write:
1. Create a cold-memory note instead.
2. Add or update an index entry.
3. If needed, replace an older hot-memory entry with a short pointer to the indexed note.
4. Tell Mike where the full memory was stored.
