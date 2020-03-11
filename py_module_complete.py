import re
from importlib import import_module
import inspect

import sublime_plugin
import sublime


SCOPE_RE = re.compile(r'\bsource\.python\b')
LIB_MODULE_RE = re.compile(r'\bsupport\.module\.python\b')


def format_attr(attr, module):
    module_name = module.__name__
    pretty_attr = attr
    snippet_attr = attr

    obj = getattr(module, attr)

    # if inspect.isclass(attr):
    if isinstance(attr, type):
        pretty_attr = 'class {}()'.format(attr)
    elif callable(obj):
        pretty_attr = '{}()'.format(attr)
        snippet_attr = '{}'.format(attr)

    return (
        pretty_attr + '\t' + module_name,
        snippet_attr,
    )


def grab_module(view, cursor):
    ''' Grabs the entire module path under the cursor '''
    word_sel = view.word(cursor)

    pos = None

    # Are we on a dot right now?
    if view.substr(cursor.begin() - 1) == '.':
        pos = cursor.begin() - 1

    # Are we on a word?
    elif view.substr(word_sel.begin() - 1) == '.':
        pos = word_sel.begin() - 1

    # Not a module
    else:
        return False

    path_parts = []
    while view.substr(pos) == '.':
        # Expand prefix to a word
        word_sel = view.word(pos - 1)
        word = view.substr(word_sel)

        path_parts.append(word)
        pos = word_sel.begin() - 1

    # Format the module path
    path = '.'.join(reversed(path_parts))

    return path


class PythonAutoCompletion(sublime_plugin.EventListener):

    def __init__(self, *args, **kwargs):
        self.on_settings_update()
        self.watch_settings()

        super(PythonAutoCompletion, self).__init__(*args, **kwargs)

    def watch_settings(self):
        """Observe changes."""
        self.unwatch_settings()
        self._settings.add_on_change('PyComplete-settings-listener', self.on_settings_update)

    def unwatch_settings(self):
        self._settings.clear_on_change('PyComplete-settings-listener')

    def on_settings_update(self):
        self._settings = sublime.load_settings('PyComplete.sublime-settings')

    def on_query_completions(self, view, prefix, locations):
        cursor = view.sel()[-1]
        scopes = view.scope_name(cursor.begin())

        # Skip unknown languages
        if not SCOPE_RE.match(scopes):
            return

        # Grab the current path
        module_name = grab_module(view, cursor)
        if module_name not in self._settings.get('modules'):
            return

        module = import_module(module_name)
        properties = dir(module)

        completions = [
            # Convert to completions format
            format_attr(prop, module)

            for prop in properties

            # Filter out private properties
            if not prop.startswith('_')
        ]

        return (
            # Completions
            completions,

            # Flags:
            (
                # Disable document-word completions
                sublime.INHIBIT_WORD_COMPLETIONS
                # Disable .sublime-completions
                | sublime.INHIBIT_EXPLICIT_COMPLETIONS
            ),
        )

