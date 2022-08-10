function diffed_files {
  git diff --name-only --merge-base origin/master | grep .py$
}
