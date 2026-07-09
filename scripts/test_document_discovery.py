import base64

from app.sources.github.client import GitHubClient
from app.sources.github.document_discovery import discover_documents


OWNER = "backstage"
REPO = "backstage"


def main():
    client = GitHubClient()

    print("\nFetching repository tree...")

    repository_tree = client.get_repository_tree(
        owner=OWNER,
        repo=REPO,
    )

    tree_items = repository_tree["tree"]

    print(f"Tree items fetched: {len(tree_items)}")
    print(
        f"Tree truncated: "
        f"{repository_tree.get('truncated')}"
    )

    print("\nDiscovering decision documents...")

    documents = discover_documents(tree_items)

    print(f"Potential documents found: {len(documents)}")

    for document in documents[:20]:
        print(
            f"[{document['document_type'].upper()}] "
            f"{document['path']}"
        )

    if not documents:
        print("\nNo documents found.")
        return

    first_document = documents[0]

    print(
        f"\nDownloading first document: "
        f"{first_document['path']}"
    )

    file_data = client.get_file_content(
        owner=OWNER,
        repo=REPO,
        path=first_document["path"],
    )

    encoded_content = file_data.get("content", "")

    decoded_content = base64.b64decode(
        encoded_content
    ).decode(
        "utf-8",
        errors="replace",
    )

    print("\nDOCUMENT PREVIEW")
    print("-" * 50)
    print(decoded_content[:1000])


if __name__ == "__main__":
    main()