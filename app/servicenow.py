
import re
import requests

from requests.auth import HTTPBasicAuth
from app.config import setting


SYS_ID = re.compile(r"[a-fA-F0-9]{32}\Z")

TABLES = {
    "sys_script_include": "script_include",
    "sys_script": "business_rule"
}

FIELDS = [
    "sys_id",
    "name",
    "script",
    "sys_scope",
    "sys_updated_on"
]


class ServiceNowClient:

    def __init__(self):
        self.base = setting(
            "SERVICENOW_INSTANCE"
        ).rstrip("/")

        if not self.base.startswith("https://"):
            raise ValueError(
                "ServiceNow instance must use HTTPS"
            )

        self.session = requests.Session()

        self.session.auth = HTTPBasicAuth(
            setting("SERVICENOW_USER"),
            setting("SERVICENOW_PASSWORD")
        )

        self.session.headers["Accept"] = (
            "application/json"
        )

    def fetch_table(
        self,
        table,
        fields=None,
        query="",
        max_records=5000,
        page_size=100
    ):
        if table not in TABLES:
            raise ValueError("Unsupported table")

        if max_records < 1 or page_size < 1:
            raise ValueError(
                "Invalid pagination settings"
            )

        results = []
        offset = 0

        while len(results) < max_records:

            limit = min(
                page_size,
                max_records - len(results)
            )

            response = self.session.get(
                f"{self.base}/api/now/table/{table}",
                params={
                    "sysparm_query": query,
                    "sysparm_fields": ",".join(
                        fields or FIELDS
                    ),
                    "sysparm_limit": limit,
                    "sysparm_offset": offset,
                    "sysparm_display_value": "false",
                    "sysparm_exclude_reference_link":
                        "true"
                },
                timeout=30
            )

            response.raise_for_status()

            batch = response.json().get(
                "result", []
            )

            if not isinstance(batch, list):
                raise ValueError(
                    "Unexpected ServiceNow response"
                )

            results.extend(batch)

            if len(batch) < limit:
                return results, True

            offset += len(batch)

        # The record cap was reached.
        # Completeness is not established.
        return results, False

    def get_script_include(self, sys_id):
        if not SYS_ID.fullmatch(sys_id):
            raise ValueError("Invalid sys_id")

        records, _ = self.fetch_table(
            "sys_script_include",
            query=f"sys_id={sys_id}",
            max_records=1
        )

        return records[0] if records else None

    def get_components(self, max_records=5000):
        components = []
        completeness = {}

        for table, kind in TABLES.items():

            records, complete = self.fetch_table(
                table,
                max_records=max_records
            )

            completeness[table] = complete

            for record in records:
                scope = record.get("sys_scope") or ""

                if isinstance(scope, dict):
                    scope = scope.get("value", "")

                components.append({
                    "sys_id": record["sys_id"],
                    "name": record.get("name") or "",
                    "type": kind,
                    "scope": str(scope),
                    "script": record.get("script") or "",
                    "updated_at": record.get(
                        "sys_updated_on"
                    ) or ""
                })

        return components, completeness

    def close(self):
        self.session.close()
