#!/usr/bin/env python3
"""Print selected environment vars and test importing Gtk/Gdk.

Run this from the same environment VS Code uses (via a task or launch) so
we can see exactly what variables are present when the segfault occurs.
"""
import os
import sys

keys = [
    'PATH', 'LD_LIBRARY_PATH', 'PYTHONPATH', 'GI_TYPELIB_PATH',
    'DISPLAY', 'WAYLAND_DISPLAY', 'XDG_RUNTIME_DIR',
    'DBUS_SESSION_BUS_ADDRESS', 'HOME', 'LANG'
]

print('--- ENV ---')
for k in keys:
    print(f'{k}={os.environ.get(k)!r}')

print('\n--- PYTHON INFO ---')
print('executable=', sys.executable)
print('version=', sys.version.replace('\n',' '))

try:
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk
    print('gi import: OK ->', getattr(gi, '__file__', repr(gi)))
    disp = Gdk.Display.get_default()
    print('Gdk.Display.get_default() ->', disp)
    if disp is not None:
        try:
            print('display name:', disp.get_name())
        except Exception as e:
            print('display name error:', e)
except Exception as e:
    print('gi import/display error:', repr(e))

print('\nTo reproduce: run this script as the same interpreter VS Code uses.')
