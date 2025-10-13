# 🚀 Proslenkey

A lightweight GTK4 application launcher for Wayland

![Screenshot](https://github.com/user-attachments/assets/ae51c3e6-5118-4828-bb1a-c26f055549a4)

## 💭 Why?

-   **⚪️ Simple:** A minimal launcher that runs commands with arguments. No complex features or configurations.
-   **◽ Small:** Small and easy-to-understand code.
-   **🐈️ Sleek & Subtle:** A slim, temporary window that stays out of your way, quietly resting at the bottom.
-   **🤝 Plays Nice with IMEs:** Works smoothly with Fcitx5 on Wayland. It just works.

## ✨ Features

-   Lists executables from your `PATH`.
-   Horizontal list of suggestions.
-   Searches for suggestions based on subsequences.
-   Appearance is customizable through CSS.

## 📋 Requirements

-   Python 3.9 or later
-   [PyGObject](https://gitlab.gnome.org/GNOME/pygobject)
-   [gtk4-layer-shell](https://github.com/wmww/gtk4-layer-shell)

## 📦 Installation

### From AUR

If you are on an Arch-based distribution, you can install it from the [AUR](https://aur.archlinux.org/packages/proslenkey):

```bash
yay -S proslenkey
```

### From source

```bash
git clone https://github.com/hikyae/proslenkey.git
cd proslenkey
pip install -e .
```

## 💻 Usage

Start `proslenkey` from your terminal or a keybinding in your window manager.

-   **Typing:** Shows suggestions that match the typed text.
-   **Enter:** Executes the command in the entry.
-   **Escape:** Quits the app.
-   **Tab / Shift+Tab:** Cycles through the suggestions.
-   **Click:** Executes the command in the suggestions.
-   **Ctrl+Enter / Ctrl+Click:** Puts the focused suggestion into the entry.

## 🎨 Customization

You can customize the look and feel of the launcher by creating a `style.css` file in `~/.config/proslenkey/`.

The default style is hardcoded into the source code.

Here is an example `style.css`:

```css
window {
	background: rgba(0, 0, 0, 0.4);
	border-radius: 8px;
}

entry {
	min-width: 550px;
	font-size: 18px;
	font-weight: bold;
	background: rgba(0, 0, 0, 0);
	color: white;
	border: 2px solid white;
	border-radius: 12px;
	outline-color: rgba(0, 0, 0, 0);
	box-shadow: none;
}

button {
	font-size: 18px;
	font-weight: bold;
	background: rgba(33, 57, 80, 0.7);
	color: white;
	border: none;
	border-radius: 12px;
}

button:focus {
	border: 2px solid white;
	outline-color: rgba(0, 0, 0, 0);
}
```
