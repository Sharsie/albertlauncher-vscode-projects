# Albert launcher plugin for Visual Studio Code

Based on https://github.com/mqus/jetbrains-albert-plugin

This is a plugin for the [albert launcher](https://albertlauncher.github.io/) which lists and lets you start projects of VS Code IDE

Supports listing of recently opened paths and integrates with [Project Manager extension](https://marketplace.visualstudio.com/items?itemName=alefragnani.project-manager)

Sorting is based on
1) If query matches on either path or name of a Project Manager entry, it will be sorted first and then alphabetically by name
2) If query matches on the tag of Project Manager entry, it will be sorted second and then alphabetically by name
3) Last come recently opened paths in VS Code sorted in the same way as they are shown in VS Code File -> Open Recent

## How to install:
Copy contents of this directory to ${XDG_DATA_HOME:-$HOME/.local/share}/albert/org.albert.extension.python/modules/vscode-projects

## Project Manager
Search is based on the rootPath of the project, its name and its tags

## Disclaimer

Not a python guy, this plugin was scripted together with my buddy ol' pal uncle Google. Like... Entirely.

I am in no way affiliated with VS Code or Microsoft.

VS Code logo used based on the [brand guidelines](https://code.visualstudio.com/brand).
