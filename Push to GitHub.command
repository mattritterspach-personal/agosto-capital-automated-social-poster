#!/bin/bash
# Double-click to push this folder to a PRIVATE GitHub repo.
# Your API key (.zernio_key) is gitignored and will NOT be uploaded.
cd "$(dirname "$0")"
REPO="agosto-social-poster"

if ! command -v git >/dev/null 2>&1; then
  echo "git isn't installed. Install Xcode command line tools first:  xcode-select --install"
  read -p "Press Enter to close..."; exit 1
fi

# Initialize repo if needed
[ -d .git ] || git init -q
rm -f .git/index.lock 2>/dev/null   # clear any stale lock

git add -A

# Safety guard: make absolutely sure the API key is never committed
if git ls-files --error-unmatch .zernio_key >/dev/null 2>&1; then
  echo "Safety stop: .zernio_key was staged. Removing it from the commit."
  git rm --cached .zernio_key >/dev/null 2>&1
fi

git commit -q -m "Agosto Studio social poster" 2>/dev/null || echo "(no new changes to commit)"
git branch -M main

echo ""
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "Creating private repo '$REPO' and pushing..."
  if gh repo create "$REPO" --private --source=. --remote=origin --push; then
    echo ""
    echo "Done. Your code is at:  https://github.com/$(gh api user -q .login)/$REPO  (private)"
  else
    echo "Repo may already exist. Pushing to existing remote instead..."
    git push -u origin main 2>/dev/null || echo "Push failed - see messages above."
  fi
else
  echo "GitHub CLI (gh) isn't set up, so finish in two quick steps:"
  echo ""
  echo "  1) Install + log in once:   brew install gh && gh auth login"
  echo "     (choose GitHub.com, HTTPS, login with a browser)"
  echo "  2) Double-click this file again."
  echo ""
  echo "Or, if you'd rather not use gh: create a PRIVATE repo named '$REPO'"
  echo "at https://github.com/new (do NOT add a README), then run:"
  echo "  git remote add origin https://github.com/mattritterspach-personal/$REPO.git"
  echo "  git push -u origin main"
fi
echo ""
read -p "Press Enter to close..."
