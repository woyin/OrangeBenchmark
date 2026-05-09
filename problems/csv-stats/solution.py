import csv


def analyze_csv(filepath: str) -> dict:
    with open(filepath, newline="") as f:
        rows = list(csv.reader(f))

    if not rows:
        return {}

    headers = rows[0]
    values = {header: [] for header in headers}
    nulls = {header: 0 for header in headers}
    non_numeric = set()

    for row in rows[1:]:
        for idx, header in enumerate(headers):
            cell = row[idx].strip() if idx < len(row) else ""
            if cell == "":
                nulls[header] += 1
                continue
            try:
                values[header].append(float(cell))
            except ValueError:
                non_numeric.add(header)

    result = {}
    for header in headers:
        if header in non_numeric:
            result[header] = {"type": "non-numeric", "null_count": nulls[header]}
            continue
        nums = values[header]
        result[header] = {
            "mean": sum(nums) / len(nums) if nums else None,
            "max": max(nums) if nums else None,
            "min": min(nums) if nums else None,
            "null_count": nulls[header],
        }
    return result
