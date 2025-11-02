#!/usr/bin/env python3
# git_cleanup_audit.py
"""Git cleanup audit - agent-optimized for minimal token usage

Two-phase cleanup process:
1. Process and remove worktrees first (parallel)
2. Process and remove remaining branches (parallel)

This order prevents attempting to delete branches that are
currently checked out in worktrees, which would fail."""
import sys
import subprocess
import argparse
import os
from multiprocessing import Pool, cpu_count
from pathlib import Path


def run_git_command(cmd, check_error=True):
    """Run a git command with proper error handling

    Args:
        cmd: List of command arguments
        check_error: If True, check for errors and handle them

    Returns:
        Tuple of (success, stdout, stderr, returncode)
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # Don't raise on non-zero exit
        )

        if check_error and result.returncode != 0:
            # Git command failed
            return (False, result.stdout, result.stderr, result.returncode)

        return (True, result.stdout, result.stderr, result.returncode)

    except FileNotFoundError:
        # Git not installed
        return (False, "", "git command not found", 127)
    except Exception as e:
        # Other unexpected errors
        return (False, "", str(e), 1)


def validate_git_repository():
    """Ensure we're in a git repository"""
    success, stdout, stderr, code = run_git_command(["git", "rev-parse", "--git-dir"])
    if not success:
        if "not a git repository" in stderr.lower():
            print("Error: Not a git repository")
        else:
            print(f"Error: Git command failed: {stderr.strip()}")
        sys.exit(2)
    return True


def change_to_repo_root():
    """Change to repository root directory"""
    success, stdout, stderr, code = run_git_command(["git", "rev-parse", "--show-toplevel"])
    if not success:
        print(f"Error: Cannot determine repository root: {stderr.strip()}")
        sys.exit(2)

    repo_root = stdout.strip()
    try:
        os.chdir(repo_root)
        return True
    except Exception as e:
        print(f"Error: Cannot change to repository root {repo_root}: {e}")
        sys.exit(2)


def switch_to_main_branch():
    """Switch to main branch if not already on it"""
    success, stdout, stderr, code = run_git_command(["git", "branch", "--show-current"])
    if not success:
        print(f"Error: Cannot determine current branch: {stderr.strip()}")
        sys.exit(2)

    current = stdout.strip()
    if current != "main":
        # Try to switch to main
        success, stdout, stderr, code = run_git_command(["git", "checkout", "main"])
        if not success:
            print(f"Error: Cannot switch to main branch: {stderr.strip()}")
            print(f"(was on branch: {current})")
            sys.exit(2)
    return True


def pull_latest_from_origin():
    """Pull latest changes from origin/main"""
    success, stdout, stderr, code = run_git_command(["git", "pull", "origin", "main"])
    if not success:
        print(f"Error: Cannot pull from origin/main: {stderr.strip()}")
        sys.exit(2)
    return True


def ensure_on_main_branch():
    """Ensure we're on the main branch (legacy check, now redundant with switch_to_main_branch)"""
    success, stdout, stderr, code = run_git_command(["git", "branch", "--show-current"])
    if not success:
        print(f"Error: Cannot determine current branch: {stderr.strip()}")
        sys.exit(2)

    current = stdout.strip()
    if current != "main":
        print(f"Error: Must be on main branch (currently on {current})")
        sys.exit(2)
    return True


def has_uncommitted_changes():
    """Check for uncommitted changes"""
    success, stdout, stderr, code = run_git_command(["git", "status", "--porcelain"])
    if not success:
        # If we can't check, assume unsafe
        return True
    return bool(stdout.strip())


def has_stashes():
    """Check for stashes"""
    success, stdout, stderr, code = run_git_command(["git", "stash", "list"])
    if not success:
        # If we can't check, assume unsafe
        return True
    return bool(stdout.strip())


def fetch_latest():
    """Fetch latest from origin"""
    success, stdout, stderr, code = run_git_command(["git", "fetch", "--prune"])
    if not success:
        print(f"Warning: Could not fetch from origin: {stderr.strip()}")
        # Don't fail, but warn user
    return success


def get_local_branches():
    """Get all local branches except current"""
    success, stdout, stderr, code = run_git_command(["git", "branch", "--format=%(refname:short)"])
    if not success:
        print(f"Error: Cannot list branches: {stderr.strip()}")
        return []

    # Get current branch
    success2, current, stderr2, code2 = run_git_command(["git", "branch", "--show-current"])
    if not success2:
        current = "main"  # Fallback
    else:
        current = current.strip()

    branches = []
    output = stdout.strip()
    if output:  # Only process if there's output
        for branch in output.split('\n'):
            if branch and branch != current and branch != "main":
                branches.append(('branch', branch, branch))
    return branches


def get_worktrees():
    """Get all worktrees except the main repository"""
    success, stdout, stderr, code = run_git_command(["git", "worktree", "list", "--porcelain"])
    if not success:
        print(f"Warning: Cannot list worktrees: {stderr.strip()}")
        return []

    # Get the main repository path to exclude it
    success2, main_repo, stderr2, code2 = run_git_command(["git", "rev-parse", "--show-toplevel"])
    if not success2:
        print(f"Warning: Cannot determine main repository path: {stderr2.strip()}")
        return []

    main_repo = main_repo.strip()

    worktrees = []
    entries = []
    current_entry = {}

    # Parse worktree output with proper state machine
    for line in stdout.strip().split('\n'):
        if line.startswith("worktree "):
            # New worktree entry
            if current_entry:
                entries.append(current_entry)
            current_entry = {"path": line.split(" ", 1)[1]}
        elif line.startswith("HEAD "):
            current_entry["head"] = line.split(" ", 1)[1]
        elif line.startswith("branch "):
            # Get the full ref path (e.g., "branch refs/heads/feature/name")
            current_entry["ref"] = line.split(" ", 1)[1]
            # Extract branch name from ref (everything after refs/heads/)
            if current_entry["ref"].startswith("refs/heads/"):
                current_entry["branch"] = current_entry["ref"].replace("refs/heads/", "", 1)
        elif line.startswith("detached"):
            current_entry["branch"] = None  # Detached HEAD
        elif line == "":
            # End of entry
            if current_entry:
                entries.append(current_entry)
                current_entry = {}

    # Don't forget the last entry
    if current_entry:
        entries.append(current_entry)

    # Filter entries
    for entry in entries:
        path = entry.get("path", "")
        branch = entry.get("branch")

        # Skip if:
        # 1. It's the main repository
        # 2. It has no branch (detached HEAD)
        # 3. It's on main branch
        if path == main_repo:
            continue  # Skip main repository
        if not branch:
            continue  # Skip detached HEAD
        if branch == "main":
            continue  # Skip main branch worktrees

        # Use the branch name for git rev-list command
        worktrees.append(('worktree', path, branch))

    return worktrees


def verify_entity(work_unit):
    """Verify entity is fully merged to main (dry-run mode)"""
    entity_type, name, ref = work_unit

    # Get commits in branch not in main
    success, stdout, stderr, code = run_git_command(["git", "rev-list", f"main..{ref}"])

    if not success:
        # If we can't verify, report as error
        return {
            "status": "error",
            "type": entity_type,
            "name": name,
            "error": stderr.strip()
        }

    unmerged = stdout.strip().split('\n') if stdout.strip() else []

    if unmerged:
        return {
            "status": "failed",
            "type": entity_type,
            "name": name,
            "commits": unmerged
        }

    return {"status": "clean", "type": entity_type, "name": name}


def get_working_directory_state():
    """Get a snapshot of the working directory state for verification

    Returns a tuple of (HEAD sha, tracked files status) that uniquely identifies
    the current working directory state for tracked files only
    """
    # Get current HEAD commit
    success, head_sha, stderr, code = run_git_command(["git", "rev-parse", "HEAD"])
    if not success:
        return (None, None)

    # Get status of tracked files only (ignore untracked)
    # Using diff-index to check if any tracked files differ from HEAD
    success, diff_output, stderr, code = run_git_command(["git", "diff-index", "HEAD"])
    if not success:
        return (None, None)

    # Create a hash of tracked file changes
    import hashlib
    diff_hash = hashlib.sha256(diff_output.encode()).hexdigest()

    return (head_sha.strip(), diff_hash)


def verify_working_directory_unchanged(before_state):
    """Verify that the working directory state hasn't changed

    This is a critical sanity check to ensure cleanup only removed
    references (branches/worktrees) and didn't modify any tracked files.

    Args:
        before_state: Tuple of (HEAD sha, tracked files hash) from before cleanup

    Returns:
        True if state is unchanged, False otherwise
    """
    after_state = get_working_directory_state()

    if before_state[0] is None or after_state[0] is None:
        # Couldn't get state, assume something went wrong
        return False

    # HEAD should be exactly the same
    if before_state[0] != after_state[0]:
        print(f"CRITICAL: HEAD changed during cleanup! Before: {before_state[0][:8]}, After: {after_state[0][:8]}")
        return False

    # Tracked files status should be exactly the same
    if before_state[1] != after_state[1]:
        print("CRITICAL: Tracked files were modified during cleanup!")
        # Show what changed in tracked files
        success, diff, stderr, code = run_git_command(["git", "diff", "--name-status", "HEAD"])
        if success and diff.strip():
            print("Modified tracked files:")
            print(diff)
        return False

    return True


def verify_and_clean_entity(work_unit):
    """Verify entity is fully merged to main and clean if safe"""
    entity_type, name, ref = work_unit

    # Get commits in branch not in main
    success, stdout, stderr, code = run_git_command(["git", "rev-list", f"main..{ref}"])

    if not success:
        # If we can't verify, report as error
        return {
            "status": "error",
            "type": entity_type,
            "name": name,
            "error": stderr.strip()
        }

    unmerged = stdout.strip().split('\n') if stdout.strip() else []

    if unmerged:
        return {
            "status": "failed",
            "type": entity_type,
            "name": name,
            "commits": unmerged
        }

    # Clean the entity with error handling
    if entity_type == "branch":
        success, stdout, stderr, code = run_git_command(["git", "branch", "-D", name])
        if not success:
            return {
                "status": "cleanup_failed",
                "type": entity_type,
                "name": name,
                "error": stderr.strip()
            }
    elif entity_type == "worktree":
        success, stdout, stderr, code = run_git_command(["git", "worktree", "remove", name, "--force"])
        if not success:
            return {
                "status": "cleanup_failed",
                "type": entity_type,
                "name": name,
                "error": stderr.strip()
            }

    return {"status": "cleaned", "type": entity_type, "name": name}


def main():
    parser = argparse.ArgumentParser(description="Git cleanup audit")
    parser.add_argument("--dry-run", action="store_true", help="Audit only")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--workers", type=int, default=cpu_count())
    parser.add_argument("--skip-fetch", action="store_true", help="Skip fetching from origin")
    args = parser.parse_args()

    # Validate we're in a git repository
    validate_git_repository()

    # NEW PREFLIGHT CHECKS (before existing checks):
    # 1. Change to repository root (in case we're in a subdirectory)
    change_to_repo_root()

    # 2. Switch to main branch (if not already on it)
    switch_to_main_branch()

    # 3. Pull latest from origin/main (unless skipped)
    if not args.skip_fetch:
        pull_latest_from_origin()

    # EXISTING PREFLIGHT CHECKS:
    # Pre-flight checks
    if has_uncommitted_changes():
        print("Uncommitted changes detected")
        return 2

    if has_stashes():
        print("Stashes detected")
        return 2

    # Capture state before any cleanup for sanity check
    # This ensures we only removed references, not actual content
    before_state = get_working_directory_state()
    if before_state[0] is None:
        print("Error: Cannot capture working directory state")
        return 3

    # Fetch latest unless skipped
    if not args.skip_fetch:
        if args.verbose:
            print("Fetching latest from origin...")
        fetch_latest()

    # Two-phase cleanup: Process worktrees first, then branches
    # This ensures branches used by worktrees aren't attempted to be deleted
    # before their worktrees are removed (which would fail)

    # Choose function based on dry-run mode
    if args.dry_run:
        func = verify_entity
    else:
        func = verify_and_clean_entity

    # Phase 1: Process all worktrees
    worktrees = get_worktrees()
    if args.verbose and worktrees:
        print(f"Phase 1: Processing {len(worktrees)} worktree(s)...")
        for entity_type, name, _ in worktrees:
            print(f"  {entity_type}: {name}")

    worktree_results = []
    if worktrees:
        # Use parallel processing if beneficial
        if len(worktrees) < 3:
            worktree_results = [func(e) for e in worktrees]
        else:
            with Pool(args.workers) as pool:
                worktree_results = pool.map(func, worktrees)

    # Check if any worktrees failed before proceeding to branches
    worktree_has_errors = any(
        r["status"] in ["error", "failed", "cleanup_failed"]
        for r in worktree_results
    )

    if worktree_has_errors:
        # Stop here if worktrees failed - don't attempt branches
        results = worktree_results
        if args.verbose:
            print("Phase 2: Skipped (worktree processing failed)")
    else:
        # Phase 2: Process remaining branches (excludes those removed with worktrees)
        branches = get_local_branches()
        if args.verbose and branches:
            print(f"Phase 2: Processing {len(branches)} branch(es)...")
            for entity_type, name, _ in branches:
                print(f"  {entity_type}: {name}")

        branch_results = []
        if branches:
            # Use parallel processing if beneficial
            if len(branches) < 3:
                branch_results = [func(e) for e in branches]
            else:
                with Pool(args.workers) as pool:
                    branch_results = pool.map(func, branches)

        # Combine results from both phases
        results = worktree_results + branch_results

    if args.verbose:
        print(f"Total entities processed: {len(results)}")

    # If no entities at all
    if not results:
        if not args.verbose:
            print("OK")
        return 0

    # Check for different types of failures
    errors = [r for r in results if r["status"] == "error"]
    failures = [r for r in results if r["status"] == "failed"]
    cleanup_failures = [r for r in results if r["status"] == "cleanup_failed"]

    # Report errors first
    if errors:
        for e in errors:
            print(f"Error checking {e['type']} {e['name']}: {e.get('error', 'unknown error')}")
        return 3  # New exit code for execution errors

    # Report cleanup failures
    if cleanup_failures:
        for c in cleanup_failures:
            print(f"Failed to clean {c['type']} {c['name']}: {c.get('error', 'unknown error')}")
        return 3

    # Report unmerged work
    if failures:
        for f in failures:
            print(f"{f['type'].capitalize()} {f['name']}: {len(f['commits'])} commit(s) not in main")
        return 1

    # CRITICAL SANITY CHECK: Verify working directory is unchanged
    # Cleanup should only remove references (branches/worktrees), never modify content
    if not args.dry_run:
        if not verify_working_directory_unchanged(before_state):
            print("CRITICAL: Working directory state changed unexpectedly!")
            print("This indicates a bug in the cleanup logic.")
            print("Your repository may need manual inspection.")
            return 3

    # Final verification: no uncommitted changes should have appeared
    if not args.dry_run and has_uncommitted_changes():
        print("CRITICAL: Uncommitted changes appeared during cleanup!")
        print("This should never happen. Please check your working directory.")
        success, status, stderr, code = run_git_command(["git", "status", "--short"])
        if success:
            print(status)
        return 3

    # Success - minimal output
    if not args.verbose:
        print("OK")

    return 0


if __name__ == "__main__":
    sys.exit(main())