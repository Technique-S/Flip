"""Explicit wire-version dispatch; frozen 1.0 cannot encode USER_SUPPLIED records."""

from flip_core import library_models_v1 as v1
from flip_core.library_models import VERSION, LibraryRequest


def parse_library_request(value):
    if isinstance(value, dict) and value.get("schemaVersion") == v1.VERSION:
        return v1.LibraryRequest.model_validate(value)
    return LibraryRequest.model_validate(value)


def upgrade_request(request):
    value = request.model_dump(mode="json")
    value["schemaVersion"] = VERSION
    return LibraryRequest.model_validate(value)


def legacy_result(result):
    value = result.model_dump(mode="json")
    suppressed = any(r["metadataTrust"] == "USER_SUPPLIED" for r in value["results"])
    value["schemaVersion"] = v1.VERSION
    value["catalog"]["schemaVersion"] = v1.VERSION
    for records in (value["catalog"]["records"], value["results"]):
        records[:] = [r for r in records if r["metadataTrust"] != "USER_SUPPLIED"]
    if suppressed:
        # Do not lie about trust to satisfy an old enum. The pointer remains in the
        # unchanged user overlay, and a 1.1 request can retrieve its truthful record.
        value.update(status="UNKNOWN", errorCode="UNSUPPORTED_SCHEMA_VERSION", total=None)
    return v1.LibraryResult.model_validate(value)
