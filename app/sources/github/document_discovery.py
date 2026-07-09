from pathlib import PurePosixPath


# File extensions that may contain useful engineering
# decision documentation.
DOCUMENT_EXTENSIONS = {
    ".md",
    ".mdx",
    ".rst",
    ".txt",
}


# Common directory names and filename prefixes used by
# engineering repositories for decision-related documents.
DOCUMENT_PATTERNS = {
    "adr": [
        "adr",
        "adrs",
        "architecture-decision",
        "architecture-decisions",
        "decision-record",
        "decision-records",
    ],
    "rfc": [
        "rfc",
        "rfcs",
    ],
    "design": [
        "design",
        "designs",
        "design-doc",
        "design-docs",
    ],
    "proposal": [
        "proposal",
        "proposals",
    ],
    "enhancement": [
        "enhancement",
        "enhancements",
    ],
}


def classify_document(path: str) -> str | None:
    """
    Determine whether a repository file is a potential
    engineering decision document.

    Returns one of:

        adr
        rfc
        design
        proposal
        enhancement

    Otherwise returns None.

    IMPORTANT:
    This function only performs candidate discovery.

    It does NOT determine whether the document actually
    contains an engineering decision.
    """

    normalized_path = path.lower()

    file_path = PurePosixPath(normalized_path)

    # Ignore files that are not textual documentation.
    if file_path.suffix not in DOCUMENT_EXTENSIONS:
        return None

    path_parts = set(file_path.parts)

    filename = file_path.stem

    # Compare the path and filename against our
    # document discovery patterns.
    for document_type, patterns in DOCUMENT_PATTERNS.items():

        for pattern in patterns:

            # Example:
            #
            # docs/architecture-decisions/0001-use-react.md
            #
            # "architecture-decisions" exists as a directory.
            if pattern in path_parts:
                return document_type

            # Example:
            #
            # docs/ADR-0001-use-postgres.md
            #
            # Filename begins with "adr".
            if filename.startswith(pattern):
                return document_type

    return None


def discover_documents(
    tree_items: list[dict],
) -> list[dict]:
    """
    Examine GitHub repository tree items and return
    potential engineering decision documents.

    Expected GitHub tree item:

    {
        "path": "docs/architecture-decisions/0001-use-react.md",
        "mode": "100644",
        "type": "blob",
        "sha": "...",
        "size": 3456,
        "url": "..."
    }

    Returned document:

    {
        "path": "...",
        "sha": "...",
        "size": 3456,
        "git_url": "...",
        "document_type": "adr"
    }
    """

    discovered_documents = []

    for item in tree_items:

        # GitHub trees contain both directories ("tree")
        # and files ("blob").
        #
        # We only want files.
        if item.get("type") != "blob":
            continue

        path = item.get("path")

        if not path:
            continue

        document_type = classify_document(path)

        # Not a likely decision document.
        if document_type is None:
            continue

        document = {
            "path": path,
            "sha": item.get("sha"),
            "size": item.get("size"),
            "git_url": item.get("url"),
            "document_type": document_type,
        }

        discovered_documents.append(document)

    return discovered_documents