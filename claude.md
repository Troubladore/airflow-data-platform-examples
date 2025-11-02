# Claude Development Guidelines

Development patterns, Git workflows, and lessons learned established for the airflow-data-platform repository, incorporating insights from repository separation and platform-as-dependency architecture.

## ⚠️ CRITICAL: Protected Branch Policy

**NEVER commit directly to main branch. NO EXCEPTIONS.**

### Workflow Rules:
1. **ALL work** must be done on feature branches
2. **ALL changes** must go through Pull Requests
3. **NEVER** `git push origin main` directly
4. **NEVER** commit to main, even for "small fixes"

### Correct Workflow:
```bash
# Create feature branch
git checkout -b fix/diagnostic-improvements

# Make changes, commit
git add .
git commit -m "fix: improve diagnostic"

# Push to feature branch
git push origin fix/diagnostic-improvements

# Create PR
gh pr create --base main

# After review and approval, merge via GitHub UI or gh pr merge
```

### If You Accidentally Commit to Main:
```bash
# DO NOT PUSH! Create branch from current state:
git branch fix/accidental-work
git reset --hard origin/main
git checkout fix/accidental-work
# Now create PR from this branch
```

### Why This Matters:
- Maintains code review process
- Prevents untested changes in main
- Enables rollback and bisection
- Tracks all changes through PR history
- Allows CI/CD validation before merge

## 🧹 Git Cleanup Automation

### When to Use `git-cleanup-audit.py`

**Use this utility after merging PRs to clean up local branches and worktrees automatically.**

**Trigger Scenarios:**
1. User just merged a PR and asks to "clean up" or "tidy up"
2. User asks to "remove old branches" or "clean up worktrees"
3. After completing a feature and merging to main
4. User mentions too many local branches cluttering their workspace

**How to Use:**
```bash
# First, ensure on main and up to date
git checkout main
git pull

# Run the cleanup utility
./git-cleanup-audit.py

# Expected output on success: "OK"
```

**What It Does:**
- Verifies you're on main branch with no uncommitted changes
- Fetches latest from origin
- Finds all local branches and worktrees
- Verifies each is fully merged to main
- Deletes merged branches and worktrees
- Reports any unmerged work for manual review

**Exit Codes:**
- `0`: Success - everything cleaned up
- `1`: Unmerged work detected - review required
- `2`: Pre-flight check failed (not on main, uncommitted changes, etc.)
- `3`: Execution error (git command failed)

**Common Usage Patterns:**

```bash
# See what would be cleaned without deleting
./git-cleanup-audit.py --dry-run --verbose

# Clean up in offline mode (skip fetch)
./git-cleanup-audit.py --skip-fetch

# Verbose output to see progress
./git-cleanup-audit.py --verbose
```

**Safety Features:**
- Will NOT run if uncommitted changes exist
- Will NOT run if stashes exist
- Will NOT run if not on main branch
- Will NOT delete branches with unmerged commits
- Fetches latest from origin to ensure accuracy

**Documentation:** See `docs/git-cleanup-audit.md` for full details.

## 🏗️ Repository Architecture Evolution

### Platform Separation (Major Learning)
**Previous**: Monorepo with mixed platform and business code
**Current**: Clean separation into platform and examples repositories

**Key Insight**: Repository separation prevents merge conflicts when businesses fork examples while allowing platform updates via dependency management.

**Architecture**:
- **Platform Repository** (`airflow-data-platform`): Generic `sqlmodel-framework` only
- **Examples Repository** (`airflow-data-platform-examples`): Business implementations using platform as UV dependency
- **Business Workflow**: Fork examples → customize → pull platform updates automatically

## 🏗️ Platform Design Principles

### Custom vs Prebuilt Image Semantics

**Critical distinction for PostgreSQL and other service images:**

**Custom Image Source:**
- "Custom" refers to the IMAGE SOURCE/PATH, not whether it's modified
- Local image: Just a name (e.g., `my-postgres:latest`)
- Remote image: Full path (e.g., `registry.company.com/postgres:custom`)
- Standard image: Docker Hub name (e.g., `postgres:17.5-alpine`)

**Prebuilt Flag:**
- `prebuilt=false` (default): **Platform layers additional customizations** on top of the image
  - May add SSL certificates
  - May add Kerberos configuration
  - May add corporate CA certificates
  - Platform builds/modifies the image before use
- `prebuilt=true`: **Use image as-is** with NO platform modifications
  - Image already has everything needed
  - Platform uses it directly without layering
  - Skips any build/customization steps

**Example Scenarios:**

```yaml
# Scenario 1: Standard image, platform adds customizations
image: postgres:17.5-alpine
prebuilt: false
# → Platform pulls image, layers on certs/config, then uses it

# Scenario 2: Standard image, use as-is
image: postgres:17.5-alpine
prebuilt: true
# → Platform pulls image and uses it directly

# Scenario 3: Custom corporate image with everything baked in
image: registry.corp.com/postgres:enterprise-2024
prebuilt: true
# → Platform uses corporate image as-is (already has certs/config)

# Scenario 4: Local custom image that needs platform additions
image: my-custom-postgres:latest
prebuilt: false
# → Platform layers on additional platform-specific config
```

**Implementation Rule:**
- `prebuilt=false`: Run build/customization logic
- `prebuilt=true`: Skip to direct usage

This distinction allows corporate environments to provide fully-configured images while still supporting standard Docker Hub images with platform enhancements.

## 🛠️ Tooling Standards

### Python Dependency Management
**ALWAYS use UV. NEVER use pip.**

```bash
# ✅ Correct - Use UV for all Python package operations
uv pip install package-name
uv pip install -r requirements.txt
uv sync                          # Install dependencies from pyproject.toml
uv add package-name              # Add new dependency

# ❌ Wrong - Never use pip directly
pip install package-name         # NEVER DO THIS
python -m pip install           # NEVER DO THIS
```

**Rationale:**
- UV is significantly faster than pip
- Consistent lock file behavior across team
- Better dependency resolution
- Integrated with our pyproject.toml workflow

### Python Version Management
**ALWAYS use PyEnv for Python versions and virtual environments.**

```bash
# ✅ Correct - Use PyEnv
pyenv install 3.11.0
pyenv local 3.11.0
pyenv virtualenv 3.11.0 myproject
pyenv activate myproject

# ❌ Wrong - Avoid other tools
python -m venv .venv            # Don't use venv directly
conda create -n myproject       # Don't use conda
```

**Rationale:**
- Consistent Python version management across team
- Isolated virtual environments per project
- Works seamlessly with UV
- Standard tool for our workflow

## 🔄 Git Workflow Standards

### Conventional Commits Format
All commits follow the **Conventional Commits** specification:

```
<type>: <description>

[optional body]

[optional footer]
```

**Commit Types:**
- `feat:` - New features or enhancements
- `fix:` - Bug fixes and corrections
- `docs:` - Documentation changes
- `style:` - Code formatting and style improvements
- `refactor:` - Code restructuring without changing functionality
- `test:` - Adding or modifying tests
- `chore:` - Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add sqlmodel-framework platform separation"
git commit -m "fix: resolve Field() server_default compatibility issues"
git commit -m "docs: update platform-as-dependency documentation"
```

### Current Branching Strategy
- **Main branch**: `main` (protected, requires PRs)
- **Feature branches**: `feature/layer2-data-processing-v2` (current active)
- **Working Branch**: Currently on `feature/layer2-data-processing-v2`

**Critical Pattern**:
- Platform changes in `airflow-data-platform` repository
- Example fixes in `airflow-data-platform-examples` repository
- Separate but coordinated development workflows

## 🎨 User Experience Testing - MANDATORY

### Critical Rule: UX Testing Runs in Parallel with Code Review

**EVERY code review (Task Xc) MUST include UX validation.**

### Required Pattern

When completing any task that affects user-facing output:

```
Task Xc: Launch 2 agents IN PARALLEL (single message, 2 Task calls):
1. superpowers:code-reviewer (technical review)
2. general-purpose agent (UX acceptance testing)

Agent 2 prompt must:
- Run REAL commands via subprocess
- Capture actual terminal output (stdout/stderr)
- Evaluate against ux_principles.md
- Check: prompts, formatting, spacing, alignment, colors, boxes
- Return structured feedback
```

### UX Test Requirements

Acceptance tests MUST:
- ✅ Run actual ./platform commands (not MockActionRunner)
- ✅ Capture real stdout/stderr
- ✅ **Check exit code** (must be 0, no crashes)
- ✅ **Verify no errors** (no Traceback, FileNotFoundError, etc.)
- ✅ **Validate outcomes** (use docker ps, ls, etc. to verify results)
- ✅ Evaluate formatting, spacing, alignment
- ✅ Check visual consistency across services
- ✅ Validate box borders, colors, symbols
- ✅ Use LLM agent for semantic UX evaluation

### Acceptance Test Must Verify

**Exit code:**
```bash
result = subprocess.run(['./platform', 'setup'], ...)
assert result.returncode == 0, "Wizard crashed!"
```

**No errors in output:**
```bash
assert 'Traceback' not in result.stderr
assert 'Error:' not in result.stderr or 'Error:' in expected_errors
```

**Outcomes match intent:**
```bash
# After setup
containers = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'])
assert 'platform-postgres' in containers.stdout

# After clean-slate
containers_after = subprocess.run(['docker', 'ps', '-a'])
assert len(containers_after.stdout) < len(containers_before.stdout)
```

### Why This Matters - Lesson Learned

We once had 448 passing tests but the wizard was completely broken:
- Duplicate prompts (shown twice)
- Wrong formatting ([False] instead of [y/N])
- Text running together on same line
- Crashes

**All tests passed ✅ but wizard was unusable ❌**

**Root cause:** Tests validated logic (state values) but never checked what users actually see.

**Solution:** LLM-based acceptance testing that evaluates real terminal output.

**Never skip UX testing.** It's not optional.

## 📝 Technical Lessons Learned

### 1. SQLModel Field Patterns (Critical Fix)
**Learning**: SQLModel Field() and SQLAlchemy Column() server_default handling is nuanced.

**What Broke**:
```python
# This causes TypeError: Field() got unexpected keyword argument 'server_default'
activebool: bool = Field(nullable=False, default=True, server_default=text("true"))
```

**Correct Pattern**:
```python
# server_default goes in sa_column, default stays in Field()
activebool: bool = Field(
    sa_column=Column(nullable=False, server_default=text("true")),
    default=True
)
```

**Why This Matters**: Enables platform-as-dependency pattern with UV installations.

### 2. UV Dependency Management
**Learning**: Git dependencies require specific configuration patterns.

**Required Configuration**:
```toml
# In pyproject.toml
[tool.hatch.metadata]
allow-direct-references = true

[tool.hatch.build.targets.wheel]
packages = ["datakits"]

dependencies = [
    "sqlmodel-framework @ git+https://github.com/Troubladore/airflow-data-platform.git@feature/layer2-data-processing-v2#subdirectory=sqlmodel-framework"
]
```

### 3. Test Infrastructure Architecture
**Learning**: PostgreSQL sandbox with automated bootstrap/teardown is essential.

**Working Pattern**:
```bash
./scripts/test-with-postgres-sandbox.sh
# ✅ Bootstraps PostgreSQL container
# ✅ Runs 22/22 framework tests
# ✅ Tests deployment script
# ✅ Clean teardown
```

**Key Insight**: Docker Compose `version:` attribute is obsolete and causes warnings.

### 4. Directory Structure Evolution
**Previous**: `data-workspace/data-platform-framework/` → `data-platform/sqlmodel-workspace/sqlmodel-framework/`
**Current**: `sqlmodel-framework/`

**Impact**: All test paths needed updating for new structure.

### 5. Import Structure Consistency
**Learning**: Framework renames must be complete and consistent.

**Pattern Applied**:
- `data_platform_framework` → `sqlmodel_framework`
- Updated all imports, tests, and deployment scripts
- Ensured no lingering old references

## 🧪 Testing Patterns That Work

### 1. Multi-Database Target Support
```bash
# Fast iteration
python scripts/deploy_datakit.py /path/to/datakit --target sqlite_memory

# Full PostgreSQL testing
python scripts/deploy_datakit.py /path/to/datakit --target postgres_local --validate
```

### 2. Framework Core Validation
```bash
# Table mixins (11/11 tests)
PYTHONPATH="./src:$PYTHONPATH" uv run -m pytest tests/unit/test_table_mixins.py -v

# Trigger builder (11/11 tests)
PYTHONPATH="./src:$PYTHONPATH" uv run -m pytest tests/unit/test_trigger_builder.py -v
```

### 3. Platform-as-Dependency Testing
```bash
# From examples repository
cd pagila-implementations/pagila-sqlmodel-basic
uv sync  # Should install framework from Git successfully
```

## 🛠️ Technical Patterns That Work

### 1. Table Mixin Architecture
```python
# Clean mixin inheritance
class ReferenceTableMixin(SQLModel):
    inactivated_date: datetime | None = Field(default=None)
    systime: datetime = Field(default_factory=lambda: datetime.now(UTC))

class TransactionalTableMixin(SQLModel):
    systime: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

### 2. Abstract Base Classes
```python
class ReferenceTable(ReferenceTableMixin, SQLModel):
    __abstract__ = True  # Critical: prevents direct instantiation
```

### 3. Deployment Script Pattern
```python
# Generic deployment to any datakit path
deploy_data_objects(table_classes, target_config)
# Supports multiple database targets
# Handles schema creation and validation
```

## 🎯 Documentation Strategies

### 1. Platform vs Examples Separation
**Platform Docs**: Technical framework documentation, API reference
**Examples Docs**: User-facing guides, getting started, business implementations

### 2. Test Plan Integration in PRs
```markdown
## Test Plan
### 1. Framework Core Tests
- [ ] 11/11 table mixin tests pass
- [ ] 11/11 trigger builder tests pass

### 2. Platform Integration
- [ ] UV sync installs framework from Git
- [ ] Deployment script discovers tables correctly
```

### 3. Architecture Decision Documentation
- Repository separation rationale clearly explained
- Migration path for business forks documented
- Platform-as-dependency benefits outlined

## 🚀 Current State & Future Work

### ✅ Completed Successfully
- Repository separation (platform vs examples)
- SQLModel compatibility fixes
- UV dependency installation working
- PostgreSQL test sandbox operational
- All 22 framework tests passing
- Updated PR descriptions and documentation

### 📋 Identified for Future Implementation
**Issue #8**: Missing table mixin column patterns
- Version tracking mixins
- Audit trail patterns (created_by/updated_by)
- Temporal versioning for advanced use cases
- Base column conflict resolution

### 🎉 Ready for Production Use
The framework separation provides:
- Clean business fork workflow
- Automated platform updates via UV dependency management
- Robust test infrastructure with PostgreSQL sandbox
- Production-ready table mixins and triggers
- Comprehensive deployment tooling

## 🔧 Core Development Principles

### 1. Test-Driven Problem Resolution (CRITICAL)
**Every discovered issue MUST have a test added FIRST:**
- Write test that fails (proves issue exists)
- Fix the issue in the standard setup
- Verify test passes (proves fix works)
- Test remains in suite (prevents regression)

**Never assert completion without:**
- Running formal test suites (not ad-hoc commands)
- Having test evidence to back assertions
- Tests for ALL discovered issues

**If it's not in the standard setup, it doesn't exist** - No manual hacks or workarounds allowed.

### 2. Real-World Testing is Essential
- Corporate environment constraints surface different issues
- User feedback reveals assumptions in documentation
- Cross-platform boundaries (Windows/WSL2) multiply complexity

### 3. Repository Architecture Decisions Have Long-Term Impact
- Early platform/examples separation prevents future merge conflicts
- Clean dependency patterns enable automated updates
- Test infrastructure design affects development velocity

### 4. Framework Compatibility is Critical
- SQLModel patterns must be precisely correct
- UV dependency management requires specific configuration
- Import structure changes must be complete and consistent

---

*This document captures lessons learned through February 2025, incorporating repository separation, platform-as-dependency architecture, and production deployment experience.*
