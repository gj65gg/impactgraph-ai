
from tree_sitter import Language, Parser
import tree_sitter_javascript


JAVASCRIPT = Language(
    tree_sitter_javascript.language()
)

PARSER = Parser(JAVASCRIPT)


def extract_references(source: str) -> list[dict]:
    """
    Extract JavaScript constructor references.

    These are candidate dependencies,
    not verified runtime relationships.
    """

    if not source:
        return []

    code = source.encode("utf-8")
    tree = PARSER.parse(code)

    references = []

    def walk(node):

        if node.type == "new_expression":

            constructor = node.child_by_field_name(
                "constructor"
            )

            if constructor:
                symbol = code[
                    constructor.start_byte:
                    constructor.end_byte
                ].decode("utf-8")

                if constructor.type in (
                    "identifier",
                    "member_expression"
                ):
                    references.append({
                        "symbol": symbol,
                        "kind": "constructor",
                        "line": (
                            node.start_point.row + 1
                        )
                    })

        for child in node.children:
            walk(child)

    walk(tree.root_node)

    return references
