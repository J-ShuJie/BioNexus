#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间格式化工具

提供智能的时间显示格式：
- < 1分钟: 显示秒（如 "45秒"）
- 1-120分钟: 显示分钟（如 "15分钟"）
- > 120分钟: 显示小时（如 "3.5小时"）
"""


def format_runtime(seconds: int, language: str = 'zh_CN') -> str:
    """
    智能格式化运行时长

    规则：
    - 0-59秒: 显示秒（"45秒"）
    - 60秒-7199秒 (1-119.98分钟): 显示分钟（"15分钟"）
    - 7200秒+ (120分钟+): 显示小时（"3.5小时"）

    Args:
        seconds: 运行时长（秒）
        language: 语言代码（zh_CN, en_US等）

    Returns:
        格式化的时间字符串

    Examples:
        >>> format_runtime(30)
        '30秒'
        >>> format_runtime(90)
        '2分钟'
        >>> format_runtime(7200)
        '2.0小时'
        >>> format_runtime(9000)
        '2.5小时'
    """
    if seconds < 0:
        seconds = 0

    # 定义语言文本
    texts = {
        'zh_CN': {
            'seconds': '秒',
            'minutes': '分钟',
            'hours': '小时',
        },
        'en_US': {
            'seconds': 's',
            'minutes': 'min',
            'hours': 'h',
        },
        'ja_JP': {
            'seconds': '秒',
            'minutes': '分',
            'hours': '時間',
        },
    }

    # 获取语言文本，默认中文
    text = texts.get(language, texts['zh_CN'])

    # 情况 1: 小于 1 分钟 (< 60 秒)
    if seconds < 60:
        return f"{seconds}{text['seconds']}"

    # 情况 2: 1-120 分钟 (60-7199 秒)
    elif seconds < 7200:  # 120 * 60 = 7200
        minutes = seconds // 60
        return f"{minutes}{text['minutes']}"

    # 情况 3: 大于等于 120 分钟 (>= 7200 秒)
    else:
        hours = seconds / 3600
        # 保留一位小数
        return f"{hours:.1f}{text['hours']}"


def format_runtime_detailed(seconds: int, language: str = 'zh_CN') -> str:
    """
    详细格式化运行时长（组合显示）

    规则：
    - < 1分钟: "45秒"
    - 1-60分钟: "15分钟30秒"
    - > 60分钟: "2小时30分钟"

    Args:
        seconds: 运行时长（秒）
        language: 语言代码

    Returns:
        详细的时间字符串

    Examples:
        >>> format_runtime_detailed(45)
        '45秒'
        >>> format_runtime_detailed(90)
        '1分钟30秒'
        >>> format_runtime_detailed(3665)
        '1小时1分钟'
    """
    if seconds < 0:
        seconds = 0

    # 定义语言文本
    texts = {
        'zh_CN': {
            'seconds': '秒',
            'minutes': '分钟',
            'hours': '小时',
        },
        'en_US': {
            'seconds': 's',
            'minutes': 'min',
            'hours': 'h',
        },
        'ja_JP': {
            'seconds': '秒',
            'minutes': '分',
            'hours': '時間',
        },
    }

    text = texts.get(language, texts['zh_CN'])

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    # 小于 1 分钟
    if hours == 0 and minutes == 0:
        return f"{secs}{text['seconds']}"

    # 小于 1 小时
    elif hours == 0:
        if secs > 0:
            return f"{minutes}{text['minutes']}{secs}{text['seconds']}"
        else:
            return f"{minutes}{text['minutes']}"

    # 大于等于 1 小时
    else:
        if minutes > 0:
            return f"{hours}{text['hours']}{minutes}{text['minutes']}"
        else:
            return f"{hours}{text['hours']}"


def format_runtime_compact(seconds: int) -> str:
    """
    紧凑格式化运行时长（H:MM:SS 格式）

    Args:
        seconds: 运行时长（秒）

    Returns:
        紧凑格式的时间字符串

    Examples:
        >>> format_runtime_compact(45)
        '0:00:45'
        >>> format_runtime_compact(3665)
        '1:01:05'
        >>> format_runtime_compact(36000)
        '10:00:00'
    """
    if seconds < 0:
        seconds = 0

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours}:{minutes:02d}:{secs:02d}"


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("时间格式化测试")
    print("=" * 60)

    test_cases = [
        (0, "0秒使用"),
        (30, "30秒使用"),
        (59, "59秒使用（临界）"),
        (60, "1分钟使用（临界）"),
        (90, "1.5分钟使用"),
        (300, "5分钟使用"),
        (1800, "30分钟使用"),
        (3600, "1小时使用"),
        (7199, "119.98分钟使用（临界）"),
        (7200, "120分钟使用（临界）"),
        (9000, "2.5小时使用"),
        (36000, "10小时使用"),
    ]

    print("\n智能格式化 (format_runtime):")
    print("-" * 60)
    for seconds, desc in test_cases:
        formatted = format_runtime(seconds)
        print(f"{desc:20s} ({seconds:5d}秒) → {formatted}")

    print("\n详细格式化 (format_runtime_detailed):")
    print("-" * 60)
    for seconds, desc in test_cases:
        formatted = format_runtime_detailed(seconds)
        print(f"{desc:20s} ({seconds:5d}秒) → {formatted}")

    print("\n紧凑格式化 (format_runtime_compact):")
    print("-" * 60)
    for seconds, desc in test_cases:
        formatted = format_runtime_compact(seconds)
        print(f"{desc:20s} ({seconds:5d}秒) → {formatted}")

    print("\n多语言支持测试:")
    print("-" * 60)
    test_seconds = 9000  # 2.5小时
    print(f"中文: {format_runtime(test_seconds, 'zh_CN')}")
    print(f"英文: {format_runtime(test_seconds, 'en_US')}")
    print(f"日文: {format_runtime(test_seconds, 'ja_JP')}")
