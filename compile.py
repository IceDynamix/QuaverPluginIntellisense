import datetime
import re
from os import path

import git

from cSharpRegexBuilder import CLASS_FIELD_REGEX, FUNCTION_REGEX, PARAM_REGEX

OUTPUT_FILE = "intellisense.lua"

IMGUI_NET_GENERATED = "./ImGui.NET/src/ImGui.NET/Generated/"
QUAVER_SHARED = "./Quaver/Quaver.Shared/"
QUAVER_ENUM_DIR = "./Quaver/Quaver.API/Quaver.API/Enums/"

REPOSITORIES = [
    ("Quaver", "https://github.com/Quaver/Quaver"),
    ("ImGui.NET", "https://github.com/mellinoe/ImGui.NET")
]

ENUMS = [
    # imgui
    ("imgui_input_text_flags", IMGUI_NET_GENERATED + "ImGuiInputTextFlags.gen.cs"),
    ("imgui_data_type", IMGUI_NET_GENERATED + "ImGuiDataType.gen.cs"),
    ("imgui_tree_node_flags", IMGUI_NET_GENERATED + "ImGuiTreeNodeFlags.gen.cs"),
    ("imgui_selectable_flags", IMGUI_NET_GENERATED + "ImGuiSelectableFlags.gen.cs"),
    ("imgui_mouse_cursor", IMGUI_NET_GENERATED + "ImGuiMouseCursor.gen.cs"),
    ("imgui_cond", IMGUI_NET_GENERATED + "ImGuiCond.gen.cs"),
    ("imgui_window_flags", IMGUI_NET_GENERATED + "ImGuiWindowFlags.gen.cs"),
    ("imgui_dir", IMGUI_NET_GENERATED + "ImGuiDir.gen.cs"),
    ("imgui_drag_drop_flags", IMGUI_NET_GENERATED + "ImGuiDragDropFlags.gen.cs"),
    ("imgui_tab_bar_flags", IMGUI_NET_GENERATED + "ImGuiTabBarFlags.gen.cs"),
    ("imgui_tab_item_flags", IMGUI_NET_GENERATED + "ImGuiTabItemFlags.gen.cs"),
    ("imgui_color_edit_flags", IMGUI_NET_GENERATED + "ImGuiColorEditFlags.gen.cs"),
    ("imgui_key", IMGUI_NET_GENERATED + "ImGuiKey.gen.cs"),
    ("imgui_col", IMGUI_NET_GENERATED + "ImGuiCol.gen.cs"),
    ("imgui_combo_flags", IMGUI_NET_GENERATED + "ImGuiComboFlags.gen.cs"),
    ("imgui_focused_flags", IMGUI_NET_GENERATED + "ImGuiFocusedFlags.gen.cs"),
    ("imgui_hovered_flags", IMGUI_NET_GENERATED + "ImGuiHoveredFlags.gen.cs"),
    # quaver
    ("game_mode", QUAVER_ENUM_DIR + "GameMode.cs"),
    ("hitsounds", QUAVER_ENUM_DIR + "Hitsounds.cs"),
    ("time_signature", QUAVER_ENUM_DIR + "TimeSignature.cs")
    # keys isn't listed here since it uses its own function to convert
]

CLASSES = [
    ("imgui", QUAVER_SHARED + "Scripting/ImGuiWrapper.cs"),
    ("state", QUAVER_SHARED + "Scripting/LuaPluginState.cs"),
    ("state", QUAVER_SHARED + "Screens/Edit/Plugins/EditorPluginState.cs"),
    ("map", QUAVER_SHARED + "Screens/Edit/Plugins/EditorPluginMap.cs"),
    ("utils", QUAVER_SHARED + "Screens/Edit/Plugins/EditorPluginUtils.cs"),
    ("actions", QUAVER_SHARED + "Screens/Edit/Actions/EditorPluginActionManager.cs"),
]

LUA_TYPE_DEFAULT_VALUES = {
    "double": 0.0,
    "float": 0.0,
    "int": 0,
    "long": 0,
    "bool": "false",
    "gamemode": "game_mode.Keys4",
    "string": '""'
}

LUA_KEYWORD_AS_PARAM_REPLACEMENTS = {
    "repeat": "rep"
}


def unindent(s: str, n: int) -> str:
    # monogame keys enum has tabs and spaces mixed for some reason
    return re.sub(r"^(\t| {4}){" + str(n) + r"}", "", s, flags=re.MULTILINE)


def loadCSharpTextContent(path: str, type: str) -> str:
    with open(path, "r") as file:
        fileContent = file.read()

    # grabs the relevant class/enum/type {...} part of the file
    regex = re.compile(
        r"(?:" + type +
        r" \w+.*\n)(?P<content>(?P<indent>\s+)\{[\s\S]*(?P=indent)\})",
        flags=re.MULTILINE
    )

    match = regex.search(fileContent)
    if match:
        commentsConverted = re.sub(
            r"//+", "--", match.group("content")
        )
        unindentCount = 1
        unindented = re.sub(
            r"^(\t| {4}){" + str(unindentCount) + r"}", "", commentsConverted,
            flags=re.MULTILINE
        )

        return unindented


def generateEnum(enumName, path) -> str:
    print(f"Generating enum {path}")
    enumTextContent = loadCSharpTextContent(path, "enum")
    if enumTextContent:
        return f"-- {path}\n{enumName} = {enumTextContent}"


def generateKeys() -> str:
    name = "keys"
    path = "./Quaver/Wobble/MonoGame/MonoGame.Framework/Input/Keys.cs"
    print(f"Generating enum {path}")

    # changes all <summary> comments to be in the same line as the value
    enumTextContent = re.sub(
        r"^(\s+)-- ?<.*>\n^\s+(-- .*)\n^\s+-- ?</.*>\n\s+(.*)",
        r"\1\3 \2",
        loadCSharpTextContent(path, "enum"),
        flags=re.MULTILINE
    )

    if enumTextContent:
        return f"-- {path}\n{name} = {enumTextContent}"


def generateClass(className: str, path: str) -> str:
    print(f"Generating class {path}")
    classTextContent = loadCSharpTextContent(path, "class")
    if classTextContent:
        lines = [f"-- {path}"]

        for match in CLASS_FIELD_REGEX.finditer(classTextContent):
            name = match.group('name')
            defaultValue = LUA_TYPE_DEFAULT_VALUES.get(match.group('type').lower(), "{}")
            comment = f"-- {match.group('type')}"
            lines.append(f"{className}.{name} = {defaultValue} {comment}")

        for match in FUNCTION_REGEX.finditer(classTextContent):
            functionName = match.group('name')
            paramNames = [
                LUA_KEYWORD_AS_PARAM_REPLACEMENTS.get(param.group("name"), param.group("name"))
                for param in PARAM_REGEX.finditer(match.group('params'))
            ]
            lines.append(f"function {className}.{functionName}({', '.join(paramNames)}) end")

        return "\n".join(lines)


def generateIntellisenseFile():
    date = [f"-- LAST UPDATED: {datetime.date.today().isoformat()}"]
    enumContent = [generateEnum(cSharpEnum[0], cSharpEnum[1]) for cSharpEnum in ENUMS]
    classContent = [generateClass(cSharpClass[0], cSharpClass[1]) for cSharpClass in CLASSES]
    keysContent = [generateKeys()]

    tables = date + enumContent + classContent + keysContent

    with open(OUTPUT_FILE, "w+") as file:
        file.write("\n\n".join(tables))

    print(f"Written to {OUTPUT_FILE}")


def updateRepo(name: str, url: str) -> None:
    if not path.exists(name):
        print(f"Cloning repository {name} from {url}")
        git.Repo.clone_from(url, name, multi_options=["--depth 1", "--recurse-submodules"])
    else:
        print(f"Pulling repository {name}")
        git.Repo(name).remotes.origin.pull()


def updateRepos():
    for repo in REPOSITORIES:
        updateRepo(repo[0], repo[1])


if __name__ == "__main__":
    updateRepos()
    generateIntellisenseFile()
