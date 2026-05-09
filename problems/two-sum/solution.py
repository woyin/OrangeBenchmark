def two_sum(nums: list[int], target: int) -> list[int]:
    seen: dict[int, int] = {}
    for idx, value in enumerate(nums):
        need = target - value
        if need in seen:
            return [seen[need], idx]
        seen[value] = idx
    return []
