from __future__ import annotations

import logging
import re
import sys
from argparse import ArgumentParser
from argparse import Namespace
from collections.abc import Iterator
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from urllib.parse import urlsplit

from mistletoe import Document
from mistletoe.block_token import BlockToken
from mistletoe.block_token import Heading
from mistletoe.markdown_renderer import MarkdownRenderer
from mistletoe.span_token import Image
from mistletoe.span_token import Link
from mistletoe.span_token import RawText
from mistletoe.token import Token


def rel_path(path: Path) -> Path:
    """
    Return the specified path relative to the working directory.
    Used in error messages.
    """
    return path.relative_to(Path().resolve(), walk_up=True)


def walk_tokens(root: Token) -> Iterator[Token]:
    """
    Iterate over all tokens in the tree under the specified token.
    """
    yield root

    for i in root.children or []:
        yield from walk_tokens(i)


def get_raw_text(token: Token) -> str:
    """
    Return the text content of the specified with all formatting removed.
    """
    return "".join(i.content for i in walk_tokens(token) if isinstance(i, RawText))


def get_line_number(token: Token) -> int:
    """
    Return the line number where the specified token is located
    in the parsed Markdown file.
    """
    # Span tokens don't have a line number;
    while not isinstance(token, BlockToken):
        token = token.parent

    # mypy: token has type "Any".
    return token.line_number  # type: ignore


def parse_markdown(text: str) -> Document:
    # Need to initialize a MarkdownRenderer instance beforehand,
    # see https://github.com/miyuchina/mistletoe/issues/56.
    with MarkdownRenderer() as renderer:
        return Document(text)


def gitlab_header_id(heading: str) -> str:
    """
    Return the HTML element ID that GitLab would generate for the
    specified heading text when rendering a Markdown file.
    """
    # The algorithm is specified here:
    # https://docs.gitlab.com/ee/user/markdown.html#heading-ids-and-links
    # It is implemented here: \https://gitlab.com/gitlab-org/gitlab/-/blob/master/lib/gitlab/utils/markdown.rb
    return re.sub("[ -]+", "-", re.sub(r"[^\w -]+", "", heading.strip().lower()))


@dataclass
class LoadedFile:
    document: Document
    heading_ids: list[str]


@cache
def load_markdown_file(path: Path) -> LoadedFile:
    assert path.is_absolute()

    document = parse_markdown(path.read_text())
    heading_ids = []

    for token in walk_tokens(document):
        if isinstance(token, Heading):
            heading_ids.append(gitlab_header_id(get_raw_text(token)))

    return LoadedFile(document, heading_ids)


@dataclass
class Application:
    has_errors: bool = False

    def log_error(self, path: Path, token: Token, message: str) -> None:
        # Log the absolute path of the file containing the error so
        # that IntelliJ allows opening the file by clicking the path.
        logging.error(f"{path}:{get_line_number(token)}: {message}")
        self.has_errors = True

    def check_link(self, source_path: Path, token: Link | Image) -> None:
        # Ignore links that reference a footnote.
        if token.dest_type != "uri":
            return

        if isinstance(token, Link):
            url = token.target
        else:
            url = token.src

        url_parts = urlsplit(url)

        # Ignore non-local URLs (only links to locals files are checked).
        if url_parts.scheme != "":
            return

        if url_parts.path == "":
            target_path = source_path
        else:
            # Absolute path to the file referenced by the link/image.
            target_path = (source_path.parent / url_parts.path).resolve()

        if not target_path.exists():
            self.log_error(
                source_path,
                token,
                f'Referenced file {rel_path(target_path)}" does not exist.',
            )
            return

        # Check whether a linked Markdown file contains a heading that
        # matches the fragment of the link's URL.
        if (
            isinstance(token, Link)
            and target_path.suffix == ".md"
            and url_parts.fragment
        ):
            heading_ids = load_markdown_file(target_path).heading_ids

            if url_parts.fragment not in heading_ids:
                headings_list_str = "\n".join(f"    #{i}" for i in heading_ids)
                self.log_error(
                    source_path,
                    token,
                    f"No heading #{url_parts.fragment} exists in referenced file "
                    f'"{rel_path(target_path)}.\n'
                    "The following headings are available:\n"
                    f"{headings_list_str}",
                )

    def check_file(self, path: Path) -> None:
        loaded_document = load_markdown_file(path)

        for token in walk_tokens(loaded_document.document):
            if isinstance(token, (Link, Image)):
                self.check_link(path, token)


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=(
            "Check the specified files for invalid links to local files, all other URLs"
            " are ignored. The command checks that the files referenced by regular"
            " links (`[Text](other_file.md)`) and image links (`![Text](image.png)`)"
            " exits. If a regular link references a heading (`other_file.md#heading`),"
            " the command checks that the referenced file contains a matching heading."
        )
    )
    parser.add_argument("files", type=Path, nargs="+")

    return parser.parse_args()


def main(files: list[Path]) -> None:
    application = Application()

    for path in files:
        application.check_file(path.resolve())

    if application.has_errors:
        sys.exit(1)


def entry_point() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    try:
        main(**vars(parse_args()))
    except KeyboardInterrupt:
        logging.error("Operation interrupted.")
        sys.exit(130)
