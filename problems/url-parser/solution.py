from urllib.parse import unquote_plus


def parse_url(url: str) -> dict:
    result = {
        "scheme": None,
        "host": None,
        "port": None,
        "path": "",
        "query_params": {},
        "fragment": None,
    }
    if url == "":
        return result

    rest = url
    if "://" in rest:
        result["scheme"], rest = rest.split("://", 1)

    if "#" in rest:
        rest, result["fragment"] = rest.split("#", 1)

    query = ""
    if "?" in rest:
        rest, query = rest.split("?", 1)

    if result["scheme"] or (rest and not rest.startswith("/")):
        host_part = rest
        path = ""
        if "/" in rest:
            host_part, path = rest.split("/", 1)
            path = "/" + path
        if host_part:
            if ":" in host_part:
                host, port = host_part.rsplit(":", 1)
                result["host"] = host or None
                result["port"] = int(port) if port else None
            else:
                result["host"] = host_part
        result["path"] = path
    else:
        result["path"] = rest

    if result["port"] is None:
        if result["scheme"] == "http":
            result["port"] = 80
        elif result["scheme"] == "https":
            result["port"] = 443

    if query:
        params = {}
        for pair in query.split("&"):
            if pair == "":
                continue
            key, value = pair.split("=", 1) if "=" in pair else (pair, "")
            params[unquote_plus(key)] = unquote_plus(value)
        result["query_params"] = params

    return result
