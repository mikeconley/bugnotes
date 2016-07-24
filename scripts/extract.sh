# Dumps out untracked folders and runs them through evernote-extraction.py
git ls-files --others --exclude-standard --directory ../ | xargs ./evernote-extraction.py --verbose
