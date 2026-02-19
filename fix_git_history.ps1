# Script to rewrite git history to remove secrets from commit 94d4be3

# Set environment variable for git rebase
$env:GIT_SEQUENCE_EDITOR = "sed -i 's/^pick 94d4be3/edit 94d4be3/'"

# Start interactive rebase from root
git rebase -i --root

# After rebase starts, we need to:
# 1. Fix the files in the commit
# 2. Amend the commit
# 3. Continue the rebase

# However, this is complex. Let's use a simpler approach:
# Create a new orphan branch and recommit everything

Write-Host "Creating backup branch..."
git branch backup-before-history-rewrite

Write-Host "Creating new orphan branch..."
git checkout --orphan temp-branch

Write-Host "Adding current files (which have secrets removed)..."
git add .

Write-Host "Creating new initial commit..."
git commit -m "Initial commit - secrets removed"

Write-Host "Now you can force push this branch to main"
Write-Host "Run: git branch -D main"
Write-Host "Run: git branch -m main"
Write-Host "Run: git push origin main --force"
