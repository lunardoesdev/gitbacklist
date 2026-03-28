# gitbacklist

Incremental git backup tool. Collects repositories from GitHub profiles (via PyGithub) or any git-compatible host (Codeberg, GitLab, Gitea, Bitbucket, etc.) and maintains local mirrors that stay in sync with upstream.

## Installation

```bash
pip install gitbacklist
```

Or with [PDM](https://pdm-project.org/):

```bash
pdm add gitbacklist
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install gitbacklist
```

## Usage

### Basic example

```python
from gitbacklist import Backlist

bl = Backlist(target_dir="~/backups/git")

# Add all public repos of a GitHub user
bl.add_github_profile("torvalds")

# Add individual repos from any host
bl.add_git_repo("https://codeberg.org/forgejo/forgejo")
bl.add_git_repo("https://gitlab.com/inkscape/inkscape.git")
bl.add_git_repo("https://github.com/neovim/neovim")

# Clone new repos, pull & reset existing ones
bl.start(verbose=True)
```

### API reference

#### `Backlist(target_dir=".")`

Create a backup list. `target_dir` is the directory where all repository clones will be stored (created automatically if missing).

#### `add_github_profile(username)`

Enumerate all **public** repositories of `username` on GitHub and add them to the list. No authentication required.

Each repo is stored in a directory named `<username>-<reponame>`.

#### `add_git_repo(repo_url)`

Add a single repository by its clone URL. Works with any git-compatible host:

| Host | Example URL |
|---|---|
| GitHub | `https://github.com/user/repo` |
| Codeberg | `https://codeberg.org/user/repo` |
| GitLab | `https://gitlab.com/user/repo.git` |
| Bitbucket | `https://bitbucket.org/user/repo` |
| Self-hosted Gitea | `https://git.example.com/user/repo` |

The local directory is named `<owner>-<repo>` (extracted from the URL path).

#### `start(verbose=False)`

Execute the backup:

- **New repos** are `git clone`-d.
- **Existing repos** are `git fetch --all --prune` followed by `git reset --hard origin/<default-branch>` and `git clean -fd`, so the working tree always matches the remote exactly.

Set `verbose=True` to see progress output.

## Single-script usage with uv

You can use gitbacklist as a self-contained script without installing anything beforehand. Create a file (e.g. `backup.py`):

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["gitbacklist"]
# ///

from gitbacklist import Backlist

bl = Backlist(target_dir="./my-backups")

bl.add_github_profile("torvalds")
bl.add_git_repo("https://codeberg.org/forgejo/forgejo")

bl.start(verbose=True)
```

Then run it directly:

```bash
chmod +x backup.py
./backup.py
```

`uv` will automatically create an isolated environment, install `gitbacklist` and its dependencies, and run the script.

## License

MIT
