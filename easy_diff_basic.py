"""
Easy Diff Basic Commands

Copyright (c) 2013 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime
import sublime_plugin
from os.path import basename
from EasyDiff.easy_diff_global import load_settings, log, debug, get_external_diff
from EasyDiff.easy_diff_dynamic_menu import update_menu
from EasyDiff.easy_diff import EasyDiffView, EasyDiffInput, EasyDiff

LEFT = None


class EasyDiffSetLeftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global LEFT
        LEFT = {"win_id": self.view.window().id(), "view_id": self.view.id(), "clip": None}
        name = self.view.file_name()
        if name is None:
            name = "Untitled"
        update_menu(basename(name))


class EasyDiffSetLeftClipboardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global LEFT
        LEFT = {"win_id": None, "view_id": None, "clip": EasyDiffView("**clipboard**", sublime.get_clipboard(), "UTF-8")}
        update_menu("**clipboard**")

    def is_enabled(self):
        return bool(load_settings().get("use_clipboard", True))

    is_visible = is_enabled


class _EasyDiffSelection(object):
    def get_selections(self):
        bfr = ""
        length = len(self.view.sel())
        for s in self.view.sel():
            if s.size() == 0:
                continue
            bfr += self.view.substr(s)
            if length > 1:
                bfr += "\n"
            length -= 1
        return bfr

    def get_encoding(self):
        return self.view.encoding()

    def has_selections(self):
        selections = False
        if bool(load_settings().get("multi_select", False)):
            for s in self.view.sel():
                if s.size() > 0:
                    selections = True
                    break
        else:
            selections = len(self.view.sel()) == 1 and self.view.sel()[0].size() > 0
        return selections


class EasyDiffSetLeftSelectionCommand(sublime_plugin.TextCommand, _EasyDiffSelection):
    def run(self, edit):
        global LEFT
        LEFT = {"win_id": None, "view_id": None, "clip": EasyDiffView("**selection**", self.get_selections(), self.get_encoding())}
        update_menu("**selection**")

    def is_enabled(self):
        return bool(load_settings().get("use_selections", True)) and self.has_selections()

    def is_visible(self):
        return bool(load_settings().get("use_selections", True))


class _EasyDiffCompareBothCommand(sublime_plugin.TextCommand):
    def set_right(self):
        pass

    def run(self, edit, external=False):
        self.set_right()

        lw = None
        rw = None
        lv = None
        rv = None

        for w in sublime.windows():
            if w.id() == LEFT["win_id"]:
                lw = w
            if w.id() == self.right["win_id"]:
                rw = w
            if lw is not None and rw is not None:
                break

        if lw is not None:
            for v in lw.views():
                if v.id() == LEFT["view_id"]:
                    lv = v
                    break
        else:
            if LEFT["clip"]:
                lv = LEFT["clip"]

        if rw is not None:
            for v in rw.views():
                if v.id() == self.right["view_id"]:
                    rv = v
                    break
        else:
            if self.right["clip"]:
                rv = self.right["clip"]

        if lv is not None and rv is not None:
            ext_diff = get_external_diff()
            if external:
                EasyDiff.extcompare(EasyDiffInput(lv, rv, external=True), ext_diff)
            else:
                EasyDiff.compare(EasyDiffInput(lv, rv))
        else:
            log("Can't compare")

    def check_enabled(self):
        return True

    def is_enabled(self):
        return LEFT is not None and self.check_enabled()


class EasyDiffCompareBothViewCommand(_EasyDiffCompareBothCommand):
    def set_right(self):
        self.right = {"win_id": self.view.window().id(), "view_id": self.view.id(), "clip": None}

    def check_enabled(self):
        return not (self.view.window().id() == LEFT["win_id"] and self.view.id() == LEFT["view_id"])


class EasyDiffCompareBothClipboardCommand(_EasyDiffCompareBothCommand):
    def set_right(self):
        self.right = {"win_id": None, "view_id": None, "clip": EasyDiffView("**clipboard**", sublime.get_clipboard(), "UTF-8")}

    def check_enabled(self):
        return bool(load_settings().get("use_clipboard", True))

    def is_visible(self):
        return self.check_enabled()


class EasyDiffCompareBothSelectionCommand(_EasyDiffCompareBothCommand, _EasyDiffSelection):
    def set_right(self):
        self.right = {"win_id": None, "view_id": None, "clip": EasyDiffView("**selection**", self.get_selections(), self.get_encoding())}

    def check_enabled(self):
        return bool(load_settings().get("use_selections", True)) and self.has_selections()

    def is_visible(self):
        return bool(load_settings().get("use_selections", True))


class EasyDiffListener(sublime_plugin.EventListener):
    def on_close(self, view):
        global LEFT
        vid = view.id()
        if LEFT is not None and vid == LEFT["view_id"]:
            LEFT = None
            update_menu()


def basic_reload():
    global LEFT
    LEFT = None
    update_menu()
    settings = load_settings()
    settings.clear_on_change('reload_basic')
    settings.add_on_change('reload_basic', basic_reload)


def plugin_loaded():
    basic_reload()
