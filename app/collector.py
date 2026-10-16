
import os

from app.servicenow import ServiceNowClient
from app.parser import extract_references
from app.resolver import resolve_references
from app.graph import DependencyGraph


def synchronize():

    snow = ServiceNowClient()
    graph = DependencyGraph()

    try:
        graph.initialize()

        max_records = int(
            os.getenv(
                "MAX_RECORDS_PER_TABLE",
                "5000"
            )
        )

        components, completeness = (
            snow.get_components(max_records)
        )

        includes = [
            component
            for component in components
            if component["type"] == "script_include"
        ]

        # Save all nodes first.
        for component in components:
            graph.save_component(component)

        dependency_count = 0

        # Parse and resolve dependencies.
        for component in components:

            references = extract_references(
                component["script"]
            )

            dependencies = resolve_references(
                component,
                references,
                includes
            )

            graph.replace_outgoing_dependencies(
                component["sys_id"],
                dependencies
            )

            dependency_count += len(dependencies)

        return {
            "components": len(components),
            "candidate_dependencies":
                dependency_count,
            "collection_complete": completeness,
            "warning": (
                "Incomplete scans can omit "
                "dependencies."
            )
        }

    finally:
        snow.close()
        graph.close()


if __name__ == "__main__":
    print(synchronize())
