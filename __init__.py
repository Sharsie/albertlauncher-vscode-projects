# -*- coding: utf-8 -*-

"""List and open VSCode projects based on recently opened paths."""

import os
import json
import unicodedata

from albert import *


__title__ = "VS Code Projects"
__version__ = "0.4.0"
__triggers__ = "vc "
__author__ = "Sharsie"

default_icon = os.path.dirname(__file__) + "/vscode.svg"
HOME_DIR = os.environ["HOME"]

# User/sync/globalState/lastSyncglobalState.json
# Path to the vscode storage json file where recent paths can be queried
STORAGE_DIR_XDG_CONFIG_DIRS = [
    os.path.join(HOME_DIR, ".config/Code/storage.json"),
    os.path.join(HOME_DIR, ".config/Code/User/globalStorage/storage.json"),
]

# Path to the Project Manager plugin configuration
PROJECT_MANAGER_XDG_CONFIG_DIR = os.path.join(
    HOME_DIR,
    ".config/Code/User/globalStorage/alefragnani.project-manager/projects.json"
)

# If Project Manager is installed, you can disable recent projects by switching
# the following variable to True
INCLUDE_RECENT = True

# Sort order of the Project Manager entries (match by Name)
ORDER_PM_NAME = 0
# Sort order of the Project Manager entries (match by Path)
ORDER_PM_PATH = 0
# Sort order of the Project Manager entries (match by Tags)
ORDER_PM_TAG = 100
# Sort order of the recently opened paths in VSCode
ORDER_RECENT = 200

# Normalizes search string (accents and whatnot)


def normalizeString(input):
    return ''.join(c for c in unicodedata.normalize('NFD', input)
                   if unicodedata.category(c) != 'Mn').lower()

# Helper method to create project entry from various sources


def createProjectEntry(name, path, index, secondary_index):
    return {
        'name': name,
        'path': path,
        # Zeropad for easy sorting
        'index': '{0:04d}'.format(index),
        # Secondary index is used for sorting based on recently opened path order
        'index_secondary': '{0:04d}'.format(secondary_index),
    }

# The entry point for the plugin, will be called by albert.


def handleQuery(query):
    print("query.string")
    if query.isTriggered:
        # Create projects dictionary to store projects by paths
        projects = {}

        # Normalize user query
        normalizedQueryString = normalizeString(query.string)

        for storageFile in STORAGE_DIR_XDG_CONFIG_DIRS:
            # No vscode storage file
            if os.path.exists(storageFile):
                with open(storageFile) as configFile:
                    # Load the storage json
                    storageConfig = json.loads(configFile.read())

                    if (
                        INCLUDE_RECENT == True
                        and "lastKnownMenubarData" in storageConfig
                        and "menus" in storageConfig['lastKnownMenubarData']
                        and "File" in storageConfig['lastKnownMenubarData']['menus']
                        and "items" in storageConfig['lastKnownMenubarData']['menus']['File']
                    ):
                        # Use incremental index for sorting which will keep the projects
                        # sorted from least recent to oldest one
                        sortIndex = ORDER_RECENT + 1

                        # These are all the menu items in File dropdown
                        for menuItem in storageConfig['lastKnownMenubarData']['menus']['File']['items']:
                            # Cannot safely detect proper menu item, as menu item IDs change over time
                            # Instead we will search all submenus and check for IDs inside the submenu items
                            if (
                                not "id" in menuItem
                                or not "submenu" in menuItem
                                or not "items" in menuItem['submenu']
                            ):
                                continue

                            for submenuItem in menuItem['submenu']['items']:
                                # Check of submenu item with id "openRecentFolder" and make sure it contains necessarry keys
                                if (
                                    not "id" in submenuItem
                                    or submenuItem['id'] != "openRecentFolder"
                                    or not "enabled" in submenuItem
                                    or submenuItem['enabled'] != True
                                    or not "label" in submenuItem
                                    or not "uri" in submenuItem
                                    or not "path" in submenuItem['uri']
                                ):
                                    continue

                                # Get the full path to the project
                                recentPath = submenuItem['uri']['path']
                                if not os.path.exists(recentPath):
                                    continue

                                # Normalize the directory in which the project resides
                                normalizedDir = normalizeString(
                                    recentPath.split("/")[-1])
                                normalizedLabel = normalizeString(submenuItem['label'])

                                # Compare the normalized dir with user query
                                if (
                                    normalizedDir.find(normalizedQueryString) != -1
                                    or normalizedLabel.find(normalizedQueryString) != -1
                                ):
                                    # Inject the project
                                    projects[recentPath] = createProjectEntry(
                                        normalizedDir, recentPath, ORDER_RECENT, sortIndex)
                                    # Increment the sort index
                                    sortIndex += 1


        # Check whether the Project Manager config file exists
        if os.path.exists(PROJECT_MANAGER_XDG_CONFIG_DIR):
            with open(PROJECT_MANAGER_XDG_CONFIG_DIR) as configFile:
                configuredProjects = json.loads(configFile.read())

                for project in configuredProjects:
                    # Make sure we have necessarry keys
                    if (
                        not "rootPath" in project
                        or not "name" in project
                        or not "enabled" in project
                        or project['enabled'] != True
                    ):
                        continue

                    # Grab the path to the project
                    rootPath = project['rootPath']
                    if not os.path.exists(rootPath):
                        continue

                    # Normalize name and dir of the project
                    normalizedName = normalizeString(project['name'])
                    normalizedDir = normalizeString(
                        rootPath.split("/")[-1])

                    found = False
                    orderIndex = 0

                    # Search against the query string
                    if normalizedName.find(normalizedQueryString) != -1:
                        orderIndex = ORDER_PM_NAME
                        found = True
                    elif normalizedDir.find(normalizedQueryString) != -1:
                        orderIndex = ORDER_PM_PATH
                        found = True
                    elif "tags" in project:
                        for tag in project['tags']:
                            if normalizeString(tag).find(normalizedQueryString) != -1:
                                orderIndex = ORDER_PM_TAG
                                found = True
                                break

                    if found:
                        projects[rootPath] = createProjectEntry(
                            project['name'],
                            rootPath,
                            orderIndex,
                            # Secondary index is zero, because we will sort the rest by project name
                            0
                        )

        # Array of Items we will return to albert launcher
        items = []

        # disable automatic sorting
        query.disableSort()

        # Sort projects by indexes
        sorted_project_items = sorted(projects.items(), key=lambda item: "%s_%s_%s" % (
            item[1]['index'], item[1]['index_secondary'], item[1]['name']), reverse=False)

        for item in sorted_project_items:
            project = item[1]
            name = project['name']
            path = project['path']
            output_entry = Item(
                id="%s_%s" % (path, name),
                icon=default_icon,
                text=name,
                subtext=path,
                completion=__triggers__ + name,
                actions=[
                    ProcAction(text="Open in VSCode",
                               commandline=["code", path],
                               cwd=path)
                ]
            )

            items.append(output_entry)

        return items
