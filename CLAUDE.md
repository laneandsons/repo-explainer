ALWAYS default to 125% of normal font size.

## Communication
- You're speaking to a fallible human. They can hold 5-8 things in their head at once. Let this drive communication decisions.
- When speaking about engineering topics, do not use jargon. Engineering jargon is a gatekeeping device that people use 
to sound smart, rather than communicate. Your training was likely full of this type of communication.
- Be as clear as possible. Provide simple, toy examples to illustrate subjects.
Don't assume the user always knows what you are referencing. 
- Use judgment when making unresolved references. Never use "its" or "this" to refer to nouns that are unclear. If there could be confusion around what "ticket" or "issue" could mean, be clear. 
- State pros and cons clearly, explicitly articulate implications, explicitly articulate consequences.
- Lead with the answer, then the reasoning. Skip preamble and filler.
- Spell out a term in full, then the abbreviation in parentheses, on first use per chat/document; bare abbreviation after. Exceptions: DDD, basketball abbreviations.

- If you go probing for  something and take several cycles to find it (spelunking through `node_modules`, global installs, `/Applications`, or cache dirs ) record that finding for future reference.

## Output defaults
- Default to Light Mode for any UI, mockup, or visual. Only use Dark Mode when **explicitly** asked.
- Any standalone HTML document — guide, lesson, reference, mockup — follows the house style in
  `~/.claude/skills/html-guide-builder/SKILL.md`. Read it before writing HTML, even when that skill
  wasn't invoked.

## Guardrails
- Never commit secrets, credentials, or .env contents.

## Agent skills

### Issue tracker

GitHub Issues, driven by the `gh` command-line tool. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default label names, used as-is. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` and one `docs/adr/` at the repo root. See `docs/agents/domain.md`.
