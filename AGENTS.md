# AGENT RULES

## Source of Truth

The codebase and `/docs` must remain synchronized.

Before modifying code:
1. Read relevant documentation.
2. Understand existing implementation.
3. Avoid duplicating existing functionality.

After modifying code:
1. Run relevant tests.
2. Update `docs/04-FEATURES.md`.
3. Update relevant technical documentation.
4. Update `docs/15-CHANGELOG.md`.
5. Update `docs/13-ROADMAP.md` when status changes.

## Safety

This is a paper-trading system.

Never:
- connect real brokerage execution
- use real-money trading
- allow LLM direct database mutation
- allow LLM direct trade execution
- bypass risk checks
- bypass user approval

All trading actions must follow:

AI → Intent → Validation → Risk → Approval → Execution

## Engineering

Prefer:
- simple solutions
- modular code
- reusable components
- type safety
- tests
- clear errors

Avoid:
- unnecessary dependencies
- duplicated logic
- fake implementations
- hard-coded secrets
- undocumented features

## Completion

Do not mark a feature complete unless it actually works and is documented.