import re
from datetime import datetime

def parse_time_input(time_str):
    """
    解析时间输入，支持具体时间和时间段，返回标准格式
    :param time_str: 用户输入的时间字符串
    :return: 时间点返回标准格式 HH:MM，时间段返回 xh 格式
    """
    try:
        # 标准化输入
        time_str = time_str.strip().replace("：", ":").replace("点", ":").replace("半", ":30").replace(" ", "")

        # 解析时间点 (如: 17:30, 下午3点)
        time_result = parse_time_point(time_str)
        if time_result:
            return time_result

        # 解析时间段 (如: 7小时, 两个半小时, 2.5h)
        duration_result = parse_time_duration(time_str)
        if duration_result:
            return duration_result

        # 无法匹配，抛出异常
        raise ValueError(f"无法识别的时间输入：{time_str}")

    except ValueError as e:
        print(f"错误: {e}")
        return None


def parse_time_point(time_str):
    """
    解析具体时间点，返回 HH:MM 格式
    :param time_str: 用户输入的时间点字符串
    :return: 时间点的标准格式 HH:MM
    """
    patterns = [
        (r"^(上午|下午)?(\d{1,2}):?(\d{0,2})$", parse_with_ampm),  # 上午/下午 7:30 或 7
        (r"^(\d{1,2}):?(\d{2})$", parse_standard),               # 17:30 或 1730
        (r"^(\d{1,2})$", lambda m: f"{int(m.group(1)):02d}:00"), # 单个小时 7 -> 07:00
    ]
    for pattern, handler in patterns:
        match = re.match(pattern, time_str)
        if match:
            return handler(match)
    return None


def parse_time_duration(time_str):
    """
    解析时间段，返回 xh 格式
    :param time_str: 用户输入的时间段字符串
    :return: 时间段的标准格式 xh
    """
    chinese_numerals = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "半": 0.5, "两": 2}
    
    def chinese_to_number(chinese):
        if chinese in chinese_numerals:
            return chinese_numerals[chinese]
        return float(chinese) if chinese.replace(".", "").isdigit() else None

    patterns = [
        (r"^([\d.]+)h$", lambda m: f"{float(m.group(1))}h"),                       # 2.5h
        (r"^(\d+)小时$", lambda m: f"{float(m.group(1))}h"),                        # 7小时
        (r"^(半|一半)小时$", lambda m: "0.5h"),                                    # 半小时
        (r"^(两个半小时|2个半小时|2.5小时)$", lambda m: "2.5h"),                    # 两个半小时
        (r"^([一二三四五六七八九十半两]+)(个)?(小时|h)$", lambda m: f"{chinese_to_number(m.group(1))}h"),  # 七小时
    ]
    for pattern, handler in patterns:
        match = re.match(pattern, time_str)
        if match:
            return handler(match)
    return None


def parse_with_ampm(match):
    """
    解析上午/下午时间点
    :param match: 正则匹配对象
    :return: 时间点的标准格式 HH:MM
    """
    am_pm, hour, minute = match.groups()
    hour = int(hour)
    minute = int(minute) if minute else 0
    if am_pm == "下午" and hour < 12:
        hour += 12
    elif am_pm == "上午" and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"


def parse_standard(match):
    """
    解析标准时间格式
    :param match: 正则匹配对象
    :return: 时间点的标准格式 HH:MM
    """
    hour, minute = match.groups()
    return f"{int(hour):02d}:{int(minute):02d}"

