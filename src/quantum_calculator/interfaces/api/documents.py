from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject

API_VERSION = "1.0"
API_PREFIX = "/api/v1"
SESSION_PATH = f"{API_PREFIX}/session"


def api_document(kind: str) -> JsonObject:
    return {"document": kind, "api_version": API_VERSION}


def error_document(code: str, message: str) -> JsonObject:
    return {**api_document("api_error"), "code": code, "message": message}
