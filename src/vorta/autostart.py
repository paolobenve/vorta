import sys

AUTOSTART_DELAY = """StartupNotify=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=20"""


def open_app_at_startup(enabled=True):
    """
    On macOS, this function adds/removes the current app bundle from Login items
    while on Linux it adds a .desktop file at ~/.config/autostart
    """
    if sys.platform == 'darwin':
        from Cocoa import NSURL, NSBundle
        from CoreFoundation import kCFAllocatorDefault
        from Foundation import NSDictionary

        # CF = CDLL(find_library('CoreFoundation'))
        from LaunchServices import (
            LSSharedFileListCopySnapshot,
            LSSharedFileListCreate,
            LSSharedFileListInsertItemURL,
            LSSharedFileListItemRemove,
            LSSharedFileListItemResolve,
            kLSSharedFileListItemHidden,
            kLSSharedFileListItemLast,
            kLSSharedFileListNoUserInteraction,
            kLSSharedFileListSessionLoginItems,
        )

        app_path = NSBundle.mainBundle().bundlePath()
        url = NSURL.alloc().initFileURLWithPath_(app_path)
        login_items = LSSharedFileListCreate(kCFAllocatorDefault, kLSSharedFileListSessionLoginItems, None)
        props = NSDictionary.dictionaryWithObject_forKey_(True, kLSSharedFileListItemHidden)

        if enabled:
            LSSharedFileListInsertItemURL(login_items, kLSSharedFileListItemLast, None, None, url, props, None)
        else:
            # From https://github.com/pudquick/pyLoginItems/blob/master/pyLoginItems.py
            list_ref = LSSharedFileListCreate(None, kLSSharedFileListSessionLoginItems, None)
            login_items, _ = LSSharedFileListCopySnapshot(list_ref, None)
            flags = kLSSharedFileListNoUserInteraction + kLSSharedFileListNoUserInteraction
            for i in login_items:
                err, a_CFURL, a_FSRef = LSSharedFileListItemResolve(i, flags, None, None)
                if 'Vorta.app' in str(a_CFURL):
                    LSSharedFileListItemRemove(list_ref, i)

    elif sys.platform.startswith('linux'):
        from pathlib import Path
        from appdirs import user_config_dir

        is_flatpak = Path('/.flatpak-info').exists()

        with open(Path(__file__).parent / "assets/metadata/com.borgbase.Vorta.desktop") as desktop_file:
            desktop_file_text = desktop_file.read()

        # Find XDG_CONFIG_HOME unless when running in flatpak
        if is_flatpak:
            autostart_path = Path.home() / '.config' / 'autostart'
        else:
            autostart_path = Path(user_config_dir("autostart"))

        if not autostart_path.exists():
            autostart_path.mkdir(parents=True, exist_ok=True)

        autostart_file_path = autostart_path / 'vorta.desktop'

        if enabled:
            # Replace command for flatpak if appropriate and start in background
            desktop_file_text = desktop_file_text.replace(
                "Exec=vorta",
                "Exec=flatpak run com.borgbase.Vorta --daemonize" if is_flatpak else "Exec=vorta --daemonize",
            )
            # Add autostart delay
            desktop_file_text += AUTOSTART_DELAY

            autostart_file_path.write_text(desktop_file_text)
        elif autostart_file_path.exists():
            autostart_file_path.unlink()
