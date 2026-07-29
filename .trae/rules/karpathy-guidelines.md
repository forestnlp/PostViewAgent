# Karpathy AI Coding Guidelines

Behavioral guidelines to reduce common LLM coding mistakes. Derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls.

**Source**: [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills)  
**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

---

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- ✅ **State your assumptions explicitly**. If uncertain, ask.
- ✅ **Present multiple interpretations**. Don't pick silently.
- ✅ **Push back when warranted**. If a simpler approach exists, say so.
- ✅ **Stop and ask**. If something is unclear, name what's confusing.

**Anti-patterns to avoid**:
- ❌ Making assumptions without checking
- ❌ Hiding confusion and proceeding anyway
- ❌ Picking one interpretation without surfacing alternatives
- ❌ Continuing when confused instead of asking

---

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- ✅ Write only the code needed to solve the stated problem
- ✅ No features beyond what was asked
- ✅ No abstractions for single-use code
- ✅ No "flexibility" or "configurability" that wasn't requested
- ✅ No error handling for impossible scenarios
- ✅ If you write 200 lines and it could be 50, rewrite it

**The senior engineer test**:
Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

**Anti-patterns to avoid**:
- ❌ Adding "nice-to-have" features not requested
- ❌ Building abstractions for code that will only run once
- ❌ Adding configuration options nobody asked for
- ❌ Handling edge cases that can't happen in this context
- ❌ Over-engineering simple problems

---

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- ✅ **Touch only what's necessary**. Focus on the specific task.
- ✅ **Don't "improve" adjacent code**. Leave comments, formatting alone.
- ✅ **Don't refactor things that aren't broken**.
- ✅ **Match existing style**. Even if you'd do it differently.
- ✅ **Mention dead code**. If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- ✅ **Clean up YOUR mess**. Remove imports/variables/functions that YOUR changes made unused.
- ❌ **Don't delete pre-existing dead code** unless explicitly asked.

**The test**: Every changed line should trace directly to the user's request.

**Anti-patterns to avoid**:
- ❌ "While I'm here, let me also fix..." (scope creep)
- ❌ Reformatting code you didn't write
- ❌ Renaming things to match your preferences
- ❌ Deleting dead code you noticed but didn't create
- ❌ Changing comments you don't fully understand

---

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform vague tasks into verifiable goals:

| Vague Task | Verifiable Goal |
|------------|----------------|
| "Add validation" | "Write tests for invalid inputs, then make them pass" |
| "Fix the bug" | "Write a test that reproduces it, then make it pass" |
| "Refactor X" | "Ensure tests pass before and after" |
| "Improve performance" | "Measure baseline, optimize, verify 2x improvement" |

For multi-step tasks, state a brief plan:
```
1. [Step 1] → verify: [how to check]
2. [Step 2] → verify: [how to check]
3. [Step 3] → verify: [how to check]
```

**Strong success criteria** let you loop independently.  
**Weak criteria** ("make it work") require constant clarification.

---

## Project-Specific Guidelines for PostViewAgent

### Project Overview
- **Name**: PostViewAgent (慧邮智析)
- **Purpose**: 邮政经营分析智能体 - 基于 DeerFlow 2.0 构建
- **Stack**: Python 3.12+, FastAPI, LangGraph, Next.js 16, TypeScript
- **Key Features**: 智能问数、业务诊断、趋势预测、网络优化

### Code Style Rules
- **Python**: Follow PEP 8, use type hints, docstrings for public APIs
- **TypeScript**: Use strict mode, prefer `interface` over `type`
- **Naming**: Use snake_case for Python, camelCase for TypeScript
- **Comments**: Chinese comments for Chinese projects, English for international

### Testing Expectations
- Write tests for new functionality
- Use pytest for Python, Jest/Vitest for TypeScript
- Mock external services and APIs

### Deployment
- Use Docker for containerization
- Follow 12-factor app principles
- Keep config in environment variables

---

## How to Know These Guidelines Are Working

✅ **Good signs**:
- Clarifying questions appear BEFORE implementation
- PRs are smaller and more focused
- AI stops "improving" things that were fine
- Changes are surgical and traceable to requests
- Fewer rewrites due to overcomplication

❌ **Bad signs**:
- AI charges ahead without asking questions
- Large diffs with unrelated changes
- "While I'm here" scope creep
- Over-engineered solutions for simple problems
- Code style changes unrelated to the task

---

**Remember**: These guidelines are working if you see fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
