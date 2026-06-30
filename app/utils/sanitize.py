def sanitize_int(value: int | None, default: int = 0) -> int:
    if value is None:
        return default
    return value


def sanitize_str(value: str | None, default: str = "") -> str:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return default
    return value


def sanitize_cultura_resposta(resposta: dict) -> dict:
    result = {}
    for codigo in ("A", "B", "C", "D"):
        val = resposta.get(codigo)
        if isinstance(val, dict):
            result[codigo] = {"atual": sanitize_int(val.get("atual"), 0)}
        elif val is None:
            result[codigo] = {"atual": 0}
        else:
            result[codigo] = {"atual": sanitize_int(int(val), 0)}
    return result
