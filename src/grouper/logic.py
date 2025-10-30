from __future__ import annotations

import hashlib
import random
import time
import re
from typing import Dict, List, Sequence, Tuple


def compute_seed_from_timestamp() -> int:
    """Compute a 32-bit integer seed from the current time.

    Algorithm: use time.time_ns(), sha256 it, and mod 2**31-1.
    """
    t = str(time.time_ns()).encode("utf-8")
    h = hashlib.sha256(t).hexdigest()
    seed = int(h[:16], 16)  # take high bits
    return seed & 0x7FFFFFFF


def parse_names_block(text: str) -> List[str]:
    """Parse names from a multi-line text block.

    - Splits by newlines, commas, semicolons, tabs, and Chinese punctuation.
    - Trims whitespace, drops empty rows, and de-duplicates while preserving order.
    """
    if not text:
        return []
    # Normalize separators
    seps = [",", "，", ";", "；", "\t"]
    for s in seps:
        text = text.replace(s, "\n")
    names = []
    seen = set()
    for raw in text.splitlines():
        name = raw.strip()
        if not name:
            continue
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


def parse_teachers_with_counts(text: str) -> Tuple[List[str], Dict[str, int]]:
    """Parse teacher lines with optional per-teacher counts.

    Supports inline count notations such as:
    - "张三:3" or "张三：3"
    - "张三 (3)" or "张三（3）"
    - "张三 x3" / "张三×3" / "张三 X3"
    - "张三 = 3" or with whitespace separators

    Lines without a recognized trailing integer are treated as plain names.

    Returns:
      (teachers, counts) where counts maps teacher name -> desired count.
    """
    if not text:
        return [], {}

    # Normalize common separators to newlines first
    for s in [",", "，", ";", "；", "\t"]:
        text = text.replace(s, "\n")

    teachers: List[str] = []
    counts: Dict[str, int] = {}
    seen = set()

    # Regex to capture optional trailing integer with various separators
    # e.g., "Name: 3", "Name（3）", "Name x3", "Name  3"
    pat = re.compile(r"^\s*(?P<name>.+?)\s*(?:[:：=\(（xX×]?\s*(?P<num>\d+)\)?\s*)?$")

    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        m = pat.match(raw)
        if not m:
            continue
        name = (m.group("name") or "").strip()
        if not name:
            continue
        if name in seen:
            # If duplicate teacher lines appear, keep the first occurrence
            continue
        seen.add(name)
        teachers.append(name)
        num_str = m.group("num")
        if num_str:
            try:
                n = int(num_str)
                if n >= 0:
                    counts[name] = n
            except ValueError:
                pass

    return teachers, counts


def group_students(
    students: Sequence[str],
    teachers: Sequence[str],
    per_teacher: int,
    seed: int,
    per_teacher_counts: Dict[str, int] | None = None,
) -> Dict[str, List[str]]:
    """Assign students to teachers using `seed` with optional per-teacher counts.

    - Each student is assigned at most once.
    - A teacher may specify a custom desired count (via `per_teacher_counts`).
      If not specified, `per_teacher` is used as the default.
    - Teachers may receive fewer students if insufficient students remain.
    - Any leftover students remain unassigned.
    """
    rng = random.Random(seed)
    students_list = list(students)
    teachers_list = list(teachers)
    rng.shuffle(students_list)

    result: Dict[str, List[str]] = {t: [] for t in teachers_list}

    # Determine desired counts per teacher
    desired: Dict[str, int] = {}
    for t in teachers_list:
        if per_teacher_counts and t in per_teacher_counts:
            desired[t] = max(0, int(per_teacher_counts[t]))
        else:
            desired[t] = max(0, int(per_teacher))

    total_needed = sum(desired.values())
    total_take = min(len(students_list), total_needed)
    idx = 0

    for t in teachers_list:
        if idx >= total_take:
            break
        take_for_t = min(desired.get(t, 0), total_take - idx)
        if take_for_t <= 0:
            result[t] = []
            continue
        result[t] = students_list[idx : idx + take_for_t]
        idx += take_for_t

    return result
