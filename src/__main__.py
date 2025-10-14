import os
import shlex
import subprocess
from ctypes import CDLL
from pathlib import Path

# For GTK4 Layer Shell to get linked before libwayland-client
# we must explicitly load it before importing with gi
CDLL("libgtk4-layer-shell.so")

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")

from gi.repository import Gdk, Gtk
from gi.repository import Gtk4LayerShell as LayerShell

APP_NAME = "proslenkey"
CSS_FILE = "style.css"


def get_path_commands() -> list[str]:
    """Return executable filenames from PATH, sorted with shorter names first."""
    commands: set[str] = set()
    for p in (Path(p) for p in os.getenv("PATH", "").split(os.pathsep)):
        if not p or not p.is_dir():
            continue
        for f in p.iterdir():
            if f.is_file() and os.access(f, os.X_OK):
                commands.add(f.name)
    return sorted(commands, key=lambda c: (len(c), c))


def get_config_path() -> Path:
    """Return config path."""
    return (
        Path(
            os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"),
        )
        / APP_NAME
    )


def subseqmatch(sub: str, full: str) -> bool:
    """Check if `sub` is a subsequence of `full`."""
    if not sub:
        return False
    pos = -1
    for c in sub:
        pos = full.find(c, pos + 1)
        if pos == -1:
            return False
    return True


class Launcher(Gtk.Application):
    """GTK4 layer-shell launcher."""

    def __init__(self) -> None:
        super().__init__(application_id=f"app.{APP_NAME}")
        self.commands = get_path_commands()
        self.entry: Gtk.Entry
        self.scroller: Gtk.ScrolledWindow
        self.suggestion_box: Gtk.Box

    # ------------------------
    # Application lifecycle
    # ------------------------

    def do_activate(self) -> None:
        """Build and show the window when the app is activated."""
        self.configure_style()
        window = Gtk.ApplicationWindow(application=self)
        self.configure_layer_shell(window)
        self.build_ui(window)
        window.present()

    # ------------------------
    # UI setup
    # ------------------------

    def configure_style(self) -> None:
        """Load CSS file or fallback to default."""
        css_path = get_config_path() / CSS_FILE

        if css_path.exists():
            css_config = Gtk.CssProvider()
            css_config.load_from_path(str(css_path))

            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                css_config,
                Gtk.STYLE_PROVIDER_PRIORITY_USER,
            )

        # Fallback default CSS
        default_css = b"""
            window {
                min-height: 50px;
            }

            entry {
                min-width: 500px;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid rgb(0, 129, 194);
                outline-color: rgba(0, 0, 0, 0);
                border-radius: 10px;
            }

            button {
                font-size: 18px;
                font-weight: bold;
                border-radius: 18px;
            }

            button:focus {
                border: 2px solid rgb(0, 129, 194);
                outline-color: rgba(0, 0, 0, 0);
            }
        """

        css_fallback = Gtk.CssProvider()
        css_fallback.load_from_data(default_css)

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_fallback,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def configure_layer_shell(self, window: Gtk.ApplicationWindow) -> None:
        """Configure window as GTK layer shell overlay."""
        LayerShell.init_for_window(window)
        LayerShell.set_layer(window, LayerShell.Layer.OVERLAY)
        for edge in (
            LayerShell.Edge.BOTTOM,
            LayerShell.Edge.LEFT,
            LayerShell.Edge.RIGHT,
        ):
            LayerShell.set_anchor(window, edge, anchor_to_edge=True)
            LayerShell.set_margin(window, edge, 0)
        LayerShell.set_keyboard_mode(window, LayerShell.KeyboardMode.EXCLUSIVE)

    def build_ui(self, window: Gtk.ApplicationWindow) -> None:
        """Build the main UI layout."""
        window.set_decorated(False)

        root_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        root_box.set_margin_top(6)
        root_box.set_margin_bottom(6)
        root_box.set_margin_start(6)
        root_box.set_margin_end(6)
        window.set_child(root_box)

        # Entry for user input
        self.entry = Gtk.Entry()
        self.entry.set_hexpand(True)
        self.entry.connect("changed", self.on_entry_changed)
        self.entry.connect("activate", self.on_activate_entry)
        root_box.append(self.entry)

        # Global key handler
        global_key_controller = Gtk.EventControllerKey()
        global_key_controller.connect("key-pressed", self.on_key_pressed)
        root_box.add_controller(global_key_controller)

        # Suggestions container
        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_visible(False)
        self.scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.scroller.set_hexpand(True)

        # ScrolledWindow key handler
        scroller_key_controller = Gtk.EventControllerKey()
        scroller_key_controller.connect("key-pressed", self.on_scroller_key_pressed)
        self.scroller.add_controller(scroller_key_controller)

        self.suggestion_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.scroller.set_child(self.suggestion_box)
        root_box.append(self.scroller)

    # ------------------------
    # Entry handling
    # ------------------------

    def append_char(self, char: str) -> None:
        """Append a character to entry."""
        text = self.entry.get_text()
        self.entry.set_text(text + char if char != "\b" else text[:-1])

    def focus_entry(self) -> None:
        """Focus on entry."""
        self.entry.grab_focus()
        self.entry.set_position(-1)

    def set_cmd(self, cmd: str) -> None:
        """Set entry text safely."""
        self.entry.set_text(shlex.quote(cmd))

    # ------------------------
    # Suggestion handling
    # ------------------------

    def on_entry_changed(self, entry: Gtk.Entry) -> None:
        """Update suggestion list when entry text changes."""
        text = entry.get_text()
        self.refresh_suggestions(text)

    def refresh_suggestions(self, text: str) -> None:
        """Rebuild suggestion buttons matching the input text."""
        child = self.suggestion_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.suggestion_box.remove(child)
            child = next_child

        matches = [command for command in self.commands if subseqmatch(text, command)]

        if not matches:
            self.hide_suggestions()
            return

        self.show_suggestions()

        for cmd in matches[:20]:
            btn = Gtk.Button(label=cmd)
            btn.set_can_focus(True)
            gesture = Gtk.GestureClick()
            gesture.connect("pressed", self.on_btn_clicked, cmd)
            btn.add_controller(gesture)

            btn_key_controller = Gtk.EventControllerKey()
            btn_key_controller.connect("key-pressed", self.on_btn_key_pressed)
            btn.add_controller(btn_key_controller)

            self.suggestion_box.append(btn)

    def show_suggestions(self) -> None:
        self.scroller.set_visible(True)
        self.entry.set_hexpand(False)

    def hide_suggestions(self) -> None:
        self.scroller.set_visible(False)
        self.entry.set_hexpand(True)

    # ------------------------
    # Key handling
    # ------------------------

    def on_key_pressed(
        self,
        _controller: Gtk.EventController,
        keyval: int,
        _keycode: int,
        state: Gdk.ModifierType,
    ) -> bool:
        """Handle key events for global shortcuts."""
        if keyval == Gdk.KEY_Escape:
            self.quit()
            return True
        return False

    def on_scroller_key_pressed(
        self,
        _controller: Gtk.EventController,
        keyval: int,
        _keycode: int,
        state: Gdk.ModifierType,
    ) -> bool:
        """Handle key events for scroller."""
        # Let GTK handle `Tab`, `Escape`, `Return` and modifier keys normally
        if keyval in (
            Gdk.KEY_Tab,
            Gdk.KEY_KP_Tab,
            Gdk.KEY_ISO_Left_Tab,
            Gdk.KEY_Escape,
            Gdk.KEY_Return,
            Gdk.KEY_Shift_L,
            Gdk.KEY_Shift_R,
            Gdk.KEY_Control_L,
            Gdk.KEY_Control_R,
        ):
            return False

        # Propagate printable chars to update entry text
        codepoint = Gdk.keyval_to_unicode(keyval)
        char = chr(codepoint) if codepoint else ""
        self.append_char(char)
        self.focus_entry()
        return True

    def on_btn_key_pressed(
        self,
        controller: Gtk.EventController,
        keyval: int,
        _keycode: int,
        state: Gdk.ModifierType,
    ) -> bool:
        # Disable space key from activating buttons
        if keyval == Gdk.KEY_space:
            self.append_char(" ")
            self.focus_entry()
            return True

        if keyval == Gdk.KEY_Return:
            cmd = controller.get_widget().get_label()
            # `Ctrl+Return` to pick suggestion
            if state == Gdk.ModifierType.CONTROL_MASK:
                self.set_cmd(cmd)
                self.focus_entry()
                return True
            # `Return` to execute command
            self.exec_one(cmd)
            self.quit()
            return True

        return False

    def on_btn_clicked(
        self,
        gesture: Gtk.GestureClick,
        _n_press: int,
        _x: float,
        _y: float,
        cmd: str,
    ) -> None:
        state = gesture.get_current_event_state()
        # `Ctrl+Click` to pick suggestion
        if state == Gdk.ModifierType.CONTROL_MASK:
            self.set_cmd(cmd)
            self.focus_entry()
            return
        # `Click` to execute command
        self.exec_one(cmd)
        self.quit()

    # ------------------------
    # Command execution
    # ------------------------

    def exec_one(self, cmd: str) -> None:
        """Execute a single command without arguments."""
        subprocess.Popen(shlex.quote(cmd), shell=True)

    def on_activate_entry(self, entry: Gtk.Entry) -> None:
        """Run the entered command."""
        cmdline = entry.get_text().strip()
        if not cmdline:
            return
        subprocess.Popen(cmdline, shell=True)
        self.quit()


def main() -> None:
    """Application entrypoint."""
    app = Launcher()
    app.run(None)


if __name__ == "__main__":
    main()
