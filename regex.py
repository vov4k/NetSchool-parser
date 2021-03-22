from re import compile as re_compile

REGEX = {
    'salt': r"salt.*:\s*[\'\"](\d+)[\'\"]",
    'attachment': r"\(\s*[\'\"]([^\'\"]+)[\'\"],\s*(\d+)\s*\)",
    # 'link': r"((https?:\/\/)|\/)[^\s]*",
    'timetable_event': r"\(\s*(\d+),\s*(\d+)\s*\)",
    'event_name_strip': r"\s*(?:(?:(?:Каникулы)|(?:Праздник)|(?:Школьное мероприятие)|(?:Урок)):)?\s*(.*)\s*",
    'lesson_link': r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)",
    'error_message': r"var\s+text\s*=\s*([\'\"])(.+?)\1"
}

for key in REGEX:
    REGEX[key] = re_compile(REGEX[key])
