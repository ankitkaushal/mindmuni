import re
from dataclasses import dataclass

# A link starts with http://, https:// or www. after a non-word character, and runs until whitespace or a
# character that can't be in a bare URL.
LINK_PATTERN = re.compile(r"(?<![\w@/.])(?:https?://|www\.)[^\s<>\"'`]+", re.IGNORECASE)
TRAILING_PUNCTUATION = ".,;:!?'\""
CLOSING_BRACKETS = {")": "(", "]": "[", "}": "{"}


@dataclass(frozen=True, slots=True)
class FoundLink:
    """A link in a string: text[start:end] is what was written, url is what to open."""

    start: int
    end: int
    url: str


def find_links(text: str) -> list[FoundLink]:
    """The web links written in the text, in order.

    Punctuation that ends a sentence isn't part of a link ("see https://a.com." links "https://a.com"), and nor
    is a closing bracket without its opening one in the link ("(https://a.com)" links "https://a.com", while
    "https://en.wikipedia.org/wiki/Tk_(software)" keeps its bracket). A link written as "www.…" opens with https.
    """
    links = []
    for match in LINK_PATTERN.finditer(text):
        written = _trim_end(match.group())
        if written.lower() in ("http://", "https://", "www."):
            continue
        url = written if "://" in written else f"https://{written}"
        links.append(FoundLink(match.start(), match.start() + len(written), url))
    return links


def _trim_end(link: str) -> str:
    while link:
        last = link[-1]
        if last in TRAILING_PUNCTUATION:
            link = link[:-1]
        elif last in CLOSING_BRACKETS and link.count(CLOSING_BRACKETS[last]) < link.count(last):
            link = link[:-1]
        else:
            break
    return link
