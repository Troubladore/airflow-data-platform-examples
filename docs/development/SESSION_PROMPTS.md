# Working Session Prompts for Bronze Layer Implementation

## Master Prompt Template

Use this template when starting work on any Bronze layer issue:

```
We're implementing Bronze Layer Issue #[NUMBER] from the airflow-data-platform-examples repo.

First, analyze the issue and all related context:
1. Read the GitHub issue #[NUMBER]
2. Review the Bronze layer design in docs/plans/2025-11-02-bronze-layer-design.md
3. Check for any existing code in the relevant directories
4. Identify dependencies and verify they're complete

Then execute using these superpowers:
- Use superpowers:using-git-worktrees to create an isolated workspace for this issue
- Use superpowers:test-driven-development for all code implementation
- Use superpowers:dispatching-parallel-agents when multiple independent tasks exist
- Use superpowers:systematic-debugging if you encounter any issues
- Use superpowers:verification-before-completion before claiming anything works

Follow RED-GREEN-REFACTOR strictly:
1. RED: Write failing tests for each acceptance criteria
2. GREEN: Write minimal code to pass
3. REFACTOR: Clean up while keeping tests green

When complete, use superpowers:requesting-code-review before creating the PR.

Start by identifying the optimal approach for this specific issue.
```

## Issue-Specific Prompts

### Issue #12: Environment Setup & Network Discovery

```
We're starting Bronze Layer Issue #12: Environment Setup & Network Discovery.

This is a research spike, so instead of TDD:
1. Use superpowers:brainstorming to identify all network patterns we need to test
2. Create a test harness to validate each connectivity pattern
3. Document findings in docs/setup/NETWORK_PATTERNS.md

Key validations needed:
- Platform services connectivity (Postgres, Kerberos)
- Pagila database access (both local and remote)
- Container-to-container networking
- Kerberos ticket mounting

Create executable test scripts that prove each pattern works.
```

### Issue #13: Build SQLModel Runner

```
We're implementing Issue #13: Build SQLModel Runner Image.

This is infrastructure, so:
1. First validate the Dockerfile builds successfully
2. Create test script to verify all imports work
3. Test mounting code into the runner
4. Validate Kerberos libraries function

Use TDD approach for the validation script:
- RED: Write tests that verify each required package imports
- GREEN: Fix Dockerfile until all imports work
- REFACTOR: Optimize image size

Success = working image < 500MB with all dependencies.
```

### Issue #14: Data Models

```
We're implementing Issue #14: SQLModel table definitions with temporal patterns.

Perfect for TDD! Start with:
1. Use superpowers:using-git-worktrees for issue-14-data-models branch
2. Use superpowers:test-driven-development strictly:
   - RED: Write tests for temporal_base.py mixin
   - GREEN: Implement TemporalTable mixin
   - RED: Write tests for first Pagila table (start with 'language' - simplest)
   - GREEN: Implement language model
   - Continue for all 15 tables

Consider using superpowers:dispatching-parallel-agents to model multiple tables simultaneously after the pattern is established.

Tables: actor, address, category, city, country, customer, film, film_actor, film_category, inventory, language, payment, rental, staff, store
```

### Issue #15: Ingestion Logic

```
We're implementing Issue #15: Core ingestion logic (loader, merger, triggers).

This has multiple independent components - perfect for parallelism:

Use superpowers:dispatching-parallel-agents to implement in parallel:
1. Agent 1: loader.py - batch reading from source
2. Agent 2: merger.py - UPSERT operations
3. Agent 3: triggers.py - temporal trigger management

Then integrate in main.py with TDD:
- RED: Integration tests for full pipeline
- GREEN: Wire components together
- REFACTOR: Optimize performance

Each agent should use TDD internally for their component.
```

### Issue #16: Airflow Orchestration

```
We're implementing Issue #16: Bronze DAG for Astronomer.

Approach:
1. Use superpowers:test-driven-development for DAG validation
2. RED: Write tests that verify DAG structure
3. GREEN: Implement DAG with KubernetesPodOperator
4. Test locally with astro dev start

Key validations:
- All 15 tables have tasks
- Parallel execution configured
- Proper error handling and retries
- Volume mounts for code and Kerberos
```

### Issue #17: Testing Suite

```
We're implementing Issue #17: Comprehensive testing.

This is meta-testing, so:
1. Use superpowers:dispatching-parallel-agents for test categories:
   - Agent 1: Unit tests (80% coverage target)
   - Agent 2: Integration tests (end-to-end flow)
   - Agent 3: Performance tests (benchmark suite)

2. Each agent should create appropriate fixtures and mocks
3. Integrate into CI/CD pipeline

Focus on testing the riskiest parts first (merger logic, trigger creation).
```

### Issue #18: Documentation

```
We're completing Issue #18: Documentation and handoff.

Approach:
1. Review all code and existing docs
2. Use superpowers:writing-clearly-and-concisely for documentation
3. Create runbook with specific procedures
4. Test all procedures yourself first

Validation: Have simulated "other developer" test the setup guide.
```

## Decision Tree: Design vs TDD

For each issue, ask:

**Need Additional Design?**
- NO if: Acceptance criteria are clear and testable
- NO if: Technical approach is defined
- YES if: Multiple valid approaches exist
- YES if: Integration points unclear

**Can Use Pure TDD?**
- YES if: Behavior is well-defined (Issues #14, #15, #16, #17)
- PARTIAL if: Infrastructure work (Issues #12, #13)
- NO if: Pure documentation (Issue #18)

## Optimal Execution Strategy

### For Maximum Speed:

1. **Parallel P0 Issues**: #12 and #13 can run simultaneously
   ```
   Start both in parallel:
   - Terminal 1: Work on environment setup (#12)
   - Terminal 2: Build runner image (#13)
   ```

2. **Parallel P1 Development**: After P0 completes
   ```
   #14 (Models) and early parts of #15 (Logic) can overlap:
   - Models team works on table definitions
   - Logic team implements generic loader/merger
   ```

3. **Use Worktrees Aggressively**:
   ```bash
   git worktree add -b issue-12-setup ../issue-12
   git worktree add -b issue-13-runner ../issue-13
   # Work independently, merge when complete
   ```

## Session Kickoff Checklist

Before using any prompt:

1. **Check Dependencies**:
   ```bash
   gh issue view [DEPENDENCY_ISSUE] --json state
   ```

2. **Create Worktree**:
   ```bash
   git worktree add -b issue-[NUMBER]-[name] ../issue-[NUMBER]
   cd ../issue-[NUMBER]
   ```

3. **Set Up Environment**:
   ```bash
   # Start platform services if needed
   cd ~/repos/airflow-data-platform
   ./platform start base-platform
   ```

4. **Use the Prompt** with appropriate superpower

## Quick Reference: Issue Order and Approach

| Issue | Approach | Superpowers | Can Parallelize? |
|-------|----------|-------------|------------------|
| #12 | Research Spike | brainstorming | Yes (with #13) |
| #13 | Infrastructure | TDD for validation | Yes (with #12) |
| #14 | Pure TDD | test-driven-development, parallel-agents | After #12 |
| #15 | Pure TDD | test-driven-development, parallel-agents | After #13 & #14 |
| #16 | TDD + Testing | test-driven-development | After #15 |
| #17 | Meta-testing | parallel-agents | After #16 |
| #18 | Documentation | writing-clearly-and-concisely | After #17 |

## Example: Starting Issue #14 (Data Models)

```
We're implementing Issue #14: SQLModel table definitions with temporal patterns.

First, check that Issue #12 is complete (environment ready).

Then:
1. Use superpowers:using-git-worktrees to create issue-14-data-models branch
2. Use superpowers:test-driven-development for the implementation
3. Start with the simplest table (language) to establish the pattern
4. Use superpowers:dispatching-parallel-agents to implement remaining tables in parallel
5. Use superpowers:verification-before-completion to ensure all models work

Begin by writing failing tests for the TemporalTable mixin.
```

This will drive maximum velocity while maintaining quality through TDD.