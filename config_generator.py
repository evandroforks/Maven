# All of SublimeMaven is licensed under the MIT license.

#   Copyright (c) 2012 Nick Lloyd

#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:

#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#   THE SOFTWARE.

import sublime
import sublime_plugin

import os
import json
import shutil

try:
    from Maven.utils.mvn import pom
except ImportError:
    from SublimeMaven.utils.mvn import pom

CURRENT_PATH = os.path.dirname( os.path.realpath( __file__ ) )


def plugin_loaded():
    settings = sublime.load_settings('Preferences.sublime-settings')
    this_file = os.path.normpath(os.path.abspath(__file__))
    plugin_path = os.path.dirname(this_file)

    # write the configuration dependent 'Side Bar', 'Context', and 'Command pallet'
    # using user-specified command lists, or defaults if none found
    def generate_config():

        # Stop showing: FileNotFoundError: [Errno 2] No such file or directory: '.../Packages/Maven/Context.sublime-menu'
        # when uninstalling the StudioChannel channel collection.
        if not os.path.isdir( plugin_path ):
            return

        maven_cmd_entry_list = settings.get('maven_menu_commands',
            [
                { "caption": "Maven: Run install", "command": "maven", "args": {"paths": [], "goals": ["install"]} },
                { "caption": "Maven: Run clean install", "command": "maven", "args": {"paths": [], "goals": ["clean", "install"]} },
                { "caption": "Maven: Test", "command": "maven", "args": {"paths": [], "goals": ["test"], "props": ["-DskipTests=false", "-Dtest=$CLASS"]} },
                { "caption": "Maven: Exec:java", "command": "maven", "args": {"paths": [], "goals": ["compile", "exec:java"], "props": ["-Dexec.mainClass=$CLASS"]} },
                { "caption": "Maven: Run ...", "command": "maven", "args": {"paths": [], "goals": []} }
            ])

        has_custom_run = False
        for menu_entry in maven_cmd_entry_list:
            if len(menu_entry['args']['goals']) == 0:
                has_custom_run = True

        if not has_custom_run:
            maven_cmd_entry_list.append({ "caption": "Maven: Run ...", "command": "maven", "args": {"paths": [], "goals": []} })

        commands_str = json.dumps(maven_cmd_entry_list, indent = 4)

        for menu_entry in maven_cmd_entry_list:
            menu_entry['caption'] = menu_entry['caption'].replace('Maven: ', '', 1)

        maven_cmd_entry_list.append({ "caption": "-" })
        maven_cmd_entry_list.append({
                "caption": "Generate Project from all POMs in Path",
                "command": "import_maven_projects",
                "args": { "paths": [] }
            })

        menu_cmd_list = \
        [
            {
                "caption": "Project Specific",
                "id": "project-specific",
                "children":
                [
                    { "caption": "-", "id": "maven_commands" },
                    {
                    "caption": "Maven",
                    "children": maven_cmd_entry_list
                    }
                ]
            }
        ]

        menu_cmd_list_str = "// AUTO GENERATED FILE BY MAVEN PACKAGE!\n%s" \
                "\n// AUTO GENERATED FILE BY MAVEN PACKAGE!\n" % json.dumps(menu_cmd_list, indent = 4)

        maven_config = open(os.path.join(plugin_path, "Context.sublime-menu"), "w")
        maven_config.write(menu_cmd_list_str)
        maven_config.flush()
        maven_config.close()
        maven_config = open(os.path.join(plugin_path, "Side Bar.sublime-menu"), "w")
        maven_config.write(menu_cmd_list_str)
        maven_config.flush()
        maven_config.close()
        maven_config = open(os.path.join(plugin_path, "Generated.sublime-commands"), "w")
        maven_config.write(commands_str)
        maven_config.flush()
        maven_config.close()
        disable_linter_context_menu()

    sublime.set_timeout_async(generate_config, 1000)
    settings.clear_on_change('maven_menu_commands')
    settings.add_on_change('maven_menu_commands', generate_config)

class HideMenuOnActivation(sublime_plugin.EventListener):

    def on_activated_async(self, view):
        disable_linter_context_menu()

def disable_linter_context_menu():
    """
        Disable the linter Context Menu, if not on a linter view.

        Allow to hide .sublime-menu folders
        https://github.com/SublimeTextIssues/Core/issues/1859
    """
    origin_context_menu  = os.path.join( CURRENT_PATH, 'Context.sublime-menu' )
    destine_context_menu = os.path.join( CURRENT_PATH, 'Context.sublime-menu-hidden' )

    origin_side_bar  = os.path.join( CURRENT_PATH, 'Side Bar.sublime-menu' )
    destine_side_bar = os.path.join( CURRENT_PATH, 'Side Bar.sublime-menu-hidden' )

    try:
        if is_current_view_linted( sublime.active_window().active_view() ):
            shutil.move( destine_side_bar, origin_side_bar )
            shutil.move( destine_context_menu, origin_context_menu )

        else:
            shutil.move( origin_side_bar, destine_side_bar )
            shutil.move( origin_context_menu, destine_context_menu )

    except IOError:
        pass

def is_current_view_linted(view):
    if view:
        file = view.file_name()
    else:
        return False
    return pom.find_nearest_pom( file ) != None if file else False
