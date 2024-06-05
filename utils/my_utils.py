from typing import List, Any

def unique_by_key(lst: List[Any], key_func) -> List[Any]:
    # 用字典来存储唯一的项
    unique_dict = {}
    for item in lst:
        # 使用 key_func 提供的键作为字典的键
        unique_dict[key_func(item)] = item
    # 返回字典的值作为去重后的列表
    return list(unique_dict.values())