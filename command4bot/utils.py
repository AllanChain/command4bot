from typing import List


def split_keyword(content: str) -> List[str]:
    split_st = content.split(" ", 1)
    if len(split_st) == 1:
        return [split_st[0], ""]
    return split_st
