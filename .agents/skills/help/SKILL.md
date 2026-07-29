---
name: help
description: "Explain the available SDD workflow skills. Use when the user invokes $help or asks how to use this framework."
---

# $help

**Phase:** meta — read-only
**Owning agent:** none

## Purpose
Print the workflow-skill catalog and the recommended phase order. Optionally
explain one workflow skill in depth.

## Inputs
- Optional `<skill-name>` (without the leading `$`).

## Reads
- `.agents/skills/`
- `.agents/skills/<skill-name>/SKILL.md` if a name was supplied.

## Writes
Nothing.

## Process
- No argument → print the workflow-skill table and the natural-language alias list.
- With argument → read the matching `SKILL.md` and summarize Purpose, Inputs,
  Reads, Writes, Process, Refuse if, and Done when.

## Refuse if
Never.

## Done when
Help text is rendered.
