import re
from collections import Counter

LOG_PATTERN = re.compile(
    r'^\S+ \S+ \S+ \[[^\]]+\] "(?P<method>\S+) (?P<path>\S+) [^"]+" '
    r"(?P<status>\d{3}) \S+(?: \"[^\"]*\" \"[^\"]*\"(?: (?P<time>\d+(?:\.\d+)?))?)?$"
)


def analyze_log(filepath: str) -> dict:
    methods: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    paths: Counter[str] = Counter()
    total = 0
    response_total = 0.0
    response_count = 0

    with open(filepath) as f:
        for raw_line in f:
            match = LOG_PATTERN.match(raw_line.strip())
            if not match:
                continue
            total += 1
            methods[match.group("method")] += 1
            statuses[match.group("status")] += 1
            paths[match.group("path")] += 1
            response_time = match.group("time")
            if response_time is not None:
                response_total += float(response_time)
                response_count += 1

    avg = response_total / response_count if response_count else 0.0
    return {
        "total_requests": total,
        "methods": dict(methods),
        "status_codes": dict(statuses),
        "top_paths": paths.most_common(10),
        "avg_response_time": round(avg, 6),
    }
