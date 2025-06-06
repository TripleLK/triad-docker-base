#!/usr/bin/env python3
"""
Git Cleanup and Push Script

Handles git operations as part of the AI cleanup process.
Adds changes, commits with descriptive messages, and pushes to remote.
Creates and uses a new branch for AI work instead of pushing to main.

Created by: Electric Shark
Date: 2025-01-19
Project: Triad Docker Base
"""

import subprocess
import sys
import os
from datetime import datetime
import argparse


def run_command(command, description=""):
    """Run a shell command and return result."""
    print(f"Running: {command}")
    if description:
        print(f"  {description}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR in command: {command}")
        print(f"STDERR: {result.stderr}")
        return False, result.stderr
    
    if result.stdout:
        print(f"OUTPUT: {result.stdout}")
    
    return True, result.stdout


def get_git_status():
    """Get current git status information."""
    success, output = run_command("git status --porcelain")
    if not success:
        return None, None
    
    modified_files = []
    untracked_files = []
    
    for line in output.strip().split('\n'):
        if not line:
            continue
        if len(line) < 3:
            continue
        status = line[:2]
        filename = line[2:].strip()  # Skip status (2 chars), then strip any spaces
        
        if status.startswith('M') or status.startswith(' M') or 'M' in status:
            modified_files.append(filename)
        elif status.startswith('D') or status.startswith(' D') or 'D' in status:
            modified_files.append(filename)  # Deleted files are still "modified"
        elif status.startswith('??'):
            untracked_files.append(filename)
    
    return modified_files, untracked_files


def get_current_branch():
    """Get the current git branch name."""
    success, output = run_command("git branch --show-current")
    if success:
        return output.strip()
    return None


def create_ai_branch_name(model_name=None):
    """Create a branch name for AI work."""
    # Use a single shared branch for all AI work
    return "ai-work"


def create_commit_message(model_name=None, session_type="AI Session Work"):
    """Create a descriptive commit message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if model_name:
        return f"{session_type} by {model_name} - {timestamp}"
    else:
        return f"{session_type} - {timestamp}"


def check_git_config():
    """Ensure git user configuration is set."""
    success, _ = run_command("git config user.name")
    if not success:
        print("Git user.name not configured. Please set it:")
        print("git config --global user.name 'Your Name'")
        return False
    
    success, _ = run_command("git config user.email")
    if not success:
        print("Git user.email not configured. Please set it:")
        print("git config --global user.email 'your.email@example.com'")
        return False
    
    return True


def branch_exists(branch_name):
    """Check if a branch exists locally."""
    success, output = run_command(f"git branch --list {branch_name}")
    return success and branch_name in output


def get_branch_operations(target_branch, current_branch):
    """Determine what branch operations are needed."""
    if target_branch == current_branch:
        return []
    elif branch_exists(target_branch):
        return [f"git checkout {target_branch}"]
    else:
        return [f"git checkout -b {target_branch}"]


def main():
    parser = argparse.ArgumentParser(description='Git cleanup and push script for AI sessions')
    parser.add_argument('--model-name', '-m', help='AI model code name for commit message and branch')
    parser.add_argument('--branch-name', '-b', help='Custom branch name (overrides auto-generated)')
    parser.add_argument('--message', '-msg', help='Custom commit message')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--skip-push', '-s', action='store_true', help='Skip the push to remote')
    parser.add_argument('--add-all', '-a', action='store_true', help='Add all files including untracked')
    parser.add_argument('--use-current-branch', '-c', action='store_true', help='Use current branch instead of creating new one')
    
    args = parser.parse_args()
    
    print("=== Git Cleanup and Push Script ===")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("ERROR: Not in a git repository!")
        sys.exit(1)
    
    # Check git configuration
    if not check_git_config():
        sys.exit(1)
    
    # Get current branch info
    current_branch = get_current_branch()
    print(f"Current branch: {current_branch}")
    
    # Determine target branch
    if args.use_current_branch:
        target_branch = current_branch
        branch_operations = []
    elif args.branch_name:
        target_branch = args.branch_name
        branch_operations = get_branch_operations(target_branch, current_branch)
    else:
        target_branch = create_ai_branch_name(args.model_name)
        branch_operations = get_branch_operations(target_branch, current_branch)
    
    # Get current status
    print("\n=== Current Git Status ===")
    modified_files, untracked_files = get_git_status()
    
    if not modified_files and not untracked_files:
        print("No changes to commit!")
        sys.exit(0)
    
    print(f"Modified files: {len(modified_files)}")
    for f in modified_files[:10]:  # Show first 10
        print(f"  M {f}")
    if len(modified_files) > 10:
        print(f"  ... and {len(modified_files) - 10} more")
    
    print(f"Untracked files: {len(untracked_files)}")
    for f in untracked_files[:10]:  # Show first 10
        print(f"  ? {f}")
    if len(untracked_files) > 10:
        print(f"  ... and {len(untracked_files) - 10} more")
    
    # Determine what to add
    if args.add_all:
        add_command = "git add ."
        files_to_add = "all files"
    else:
        # Add only modified files and specific patterns
        ai_management_files = [f for f in untracked_files if f.startswith('.project_management/') or f.startswith('.cursor/')]
        important_files = modified_files + ai_management_files
        
        if important_files:
            # Quote filenames to handle spaces
            quoted_files = [f'"{f}"' for f in important_files]
            add_command = f"git add {' '.join(quoted_files)}"
            files_to_add = f"{len(important_files)} important files"
        else:
            print("No important files to add.")
            sys.exit(0)
    
    # Create commit message
    if args.message:
        commit_message = args.message
    else:
        commit_message = create_commit_message(args.model_name)
    
    print(f"\n=== Planned Operations ===")
    if branch_operations:
        print(f"Branch: Create and switch to '{target_branch}'")
    else:
        print(f"Branch: Stay on current branch '{target_branch}'")
    print(f"Add: {files_to_add}")
    print(f"Commit message: {commit_message}")
    print(f"Push to remote: {'No' if args.skip_push else f'Yes (to {target_branch})'}")
    
    if args.dry_run:
        print("\n=== DRY RUN - No actual changes made ===")
        for branch_op in branch_operations:
            print(f"Would run: {branch_op}")
        print(f"Would run: {add_command}")
        print(f"Would run: git commit -m \"{commit_message}\"")
        if not args.skip_push:
            print(f"Would run: git push -u origin {target_branch}")
        sys.exit(0)
    
    # Confirm with user unless running in automated mode
    if os.isatty(sys.stdin.fileno()):  # Only ask if running interactively
        response = input("\nProceed with these operations? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
    
    # Execute git operations
    print("\n=== Executing Git Operations ===")
    
    # Create/switch to branch if needed
    for branch_op in branch_operations:
        success, _ = run_command(branch_op, f"Creating/switching to branch {target_branch}")
        if not success:
            print(f"Failed to create/switch to branch {target_branch}!")
            sys.exit(1)
    
    # Add files
    success, _ = run_command(add_command, "Adding files to staging area")
    if not success:
        print("Failed to add files!")
        sys.exit(1)
    
    # Commit
    commit_cmd = f'git commit -m "{commit_message}"'
    success, _ = run_command(commit_cmd, "Creating commit")
    if not success:
        print("Failed to create commit!")
        sys.exit(1)
    
    # Push (if not skipped)
    if not args.skip_push:
        push_cmd = f"git push -u origin {target_branch}"
        success, _ = run_command(push_cmd, f"Pushing to remote branch {target_branch}")
        if not success:
            print(f"Failed to push to remote branch {target_branch}!")
            print(f"You may need to run 'git push -u origin {target_branch}' manually later.")
            sys.exit(1)
        else:
            print(f"✅ Successfully pushed to remote branch '{target_branch}'!")
    else:
        print(f"⚠️  Skipped push to remote. Run 'git push -u origin {target_branch}' manually when ready.")
    
    print("\n=== Git Cleanup Complete ===")
    print(f"Working branch: {target_branch}")


if __name__ == "__main__":
    main() 