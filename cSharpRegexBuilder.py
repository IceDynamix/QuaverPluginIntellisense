import re


def optionalKeyword(keyword):
    return r"(?:(?P<" + keyword + r">" + keyword + r") )?"


REGEX = {}

LINE_START = r"^ +"
VISIBILITY = r"(?:(?P<visibility>public|private) )?"
TYPE = r"(?P<type>[\w\[\]\<\>, ]+)"
NAME = r"(?P<name>\w+)"
MOONSHARP_NOT_INVISIBLE = r"(?<!\[MoonSharpVisible\(false\)\]\n)"


FUNCTION_REGEX = re.compile("".join([
    MOONSHARP_NOT_INVISIBLE, LINE_START, VISIBILITY +
    optionalKeyword("static"), TYPE, " ", NAME, r"\((?P<params>.*?)\)"
]), re.MULTILINE)

CLASS_FIELD_REGEX = re.compile("".join([
    MOONSHARP_NOT_INVISIBLE, LINE_START, VISIBILITY +
    optionalKeyword("static"), TYPE, " ", NAME,  " {"
]), re.MULTILINE)

PARAM_REGEX = re.compile("".join([
    optionalKeyword("ref"), TYPE, " ", NAME
]), re.MULTILINE)
