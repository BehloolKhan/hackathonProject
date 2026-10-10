Getting started:

Run pip install mss pillow keyboard. Tkinter comes with the normal Windows Python installer.
Test the pieces in order, so you know exactly which part breaks:
python capture.py full: does grabbing the screen work at all?
python capture.py snip: does drag-to-select work? Esc or right-click cancels.
python capture.py listen: does Print Screen open your tool instead of Windows’? Ctrl+C stops it.

About replacing the Windows screenshot key. Python can’t swap out the built-in tool itself. What it can do, like ShareX or Greenshot, is catch the Print Screen key system-wide and block Windows from seeing it. That’s the listen mode.

On Windows 11, if the Snipping Tool still pops up, turn off Settings → Accessibility → Keyboard → “Use the Print screen key to open screen capture”.
Win+Shift+S is reserved by Windows, so hijacking it is unreliable. Stick with Print Screen, or change HOTKEY to something like "ctrl+alt+s".
Your README lists global shortcuts under “leave out today”. Get snip working before spending time on listen.