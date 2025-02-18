# check-markdown-links

## Usage

```
usage: check-markdown-links [-h] files [files ...]

Check the specified files for invalid links to local files, all other URLs are
ignored. The command checks that the files referenced by regular links
(`[Text](other_file.md)`) and image links (`![Text](image.png)`) exits. If a
regular link references a heading (`other_file.md#heading`), the command
checks that the referenced file contains a matching heading.

positional arguments:
  files

options:
  -h, --help  show this help message and exit
```

## Development Setup

```shell
pre-commit install
make venv
```
