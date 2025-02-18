# check-markdown-links

## Usage

`check-markdown-links` checks the specified files for invalid links. Only links to local
files are checked, all other URLs are ignored.

The command checks that the files referenced by regular links (`[Text](other_file.md)`)
and image links (`![Text](image.png)`) exits. If a regular link references a heading
(`other_file.md#heading`), the command checks that the referenced file contains a
matching heading.

```
usage: check-markdown-links [-h] [files ...]

Check the specified Markdown files for invalid links to local files.

positional arguments:
  files       Markdown files to check. Directories are searched recursively.
              Defaults to the current directory.

options:
  -h, --help  show this help message and exit
```

## Pre-Commit Hook

Set up a [`pre-commit`](https://pre-commit.com/) hook that runs this script:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: /Users/cs/Documents/Cloudscale/Code/check-markdown-links
    rev: main
    hooks:
      - id: check-markdown-links
        # Files in captain/api/docs/ can reference sections in the generated
        # API docs that are generated and not present in the source Markdown files.
        exclude: ^captain/api/docs/
```

## Development Setup

```shell
pre-commit install
make venv
```
