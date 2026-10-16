
BUILTINS = {
    "GlideRecord",
    "GlideAggregate",
    "GlideDateTime",
    "Date",
    "Object",
    "Array",
    "Error",
    "String",
    "Number",
    "RegExp",
    "Map",
    "Set",
    "Promise"
}


def resolve_references(
    component,
    references,
    includes
):
    dependencies = []

    for ref in references:
        symbol = ref["symbol"]

        if symbol in BUILTINS:
            continue

        matches = [
            item for item in includes
            if symbol in (
                item["name"],
                item.get("api_name")
            )
        ]

        # Do not guess when multiple records match.
        if len(matches) != 1:
            continue

        target = matches[0]

        if target["sys_id"] == component["sys_id"]:
            continue

        dependencies.append({
            "source_id": component["sys_id"],
            "target_id": target["sys_id"],
            "symbol": symbol,
            "line": ref["line"],
            "method": "ast_constructor",
            "status": "candidate"
        })

    return dependencies
