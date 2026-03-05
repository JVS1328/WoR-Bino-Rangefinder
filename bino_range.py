"""
War of Rights — Binocular Range Estimator
Hotkey: SHIFT + CAPS LOCK
  • First press  → starts listening for scroll wheel clicks
  • Second press → freezes display and shows estimated range
  • Third press  → resets back to idle
"""

import math
import tkinter as tk
import threading
from pynput import mouse, keyboard

# ── Constants ────────────────────────────────────────────────────────────────
A, B = 13.0253, 1.18761          # f(x) = A * B^x  (from Desmos export)

# Confirmed reference points (clicks → yards)
CONFIRMED = {12: 100, 16: 200, 18: 300, 20: 400}

HOTKEY = {keyboard.Key.shift, keyboard.Key.caps_lock}

# ── Range calculation ─────────────────────────────────────────────────────────
def estimate_range(clicks: int) -> int:
    if clicks <= 0:
        return 0
    return round(A * (B ** clicks))


def range_label(clicks: int) -> str:
    if clicks in CONFIRMED:
        return f"~{CONFIRMED[clicks]} yd  ✓"
    return f"~{estimate_range(clicks)} yd"


# ── App ───────────────────────────────────────────────────────────────────────
class RangeEstimator:
    IDLE    = "idle"
    LISTEN  = "listen"
    RESULT  = "result"

    def __init__(self):
        self.state  = self.IDLE
        self.clicks = 0
        self.keys_held: set = set()

        self._build_gui()
        self._start_listeners()

    # ── GUI ───────────────────────────────────────────────────────────────────
    def _build_gui(self):
        self.root = tk.Tk()
        self.root.title("Bino Range")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1a1a1a")

        # Compact fixed size
        self.root.geometry("260x160")

        pad = dict(padx=16, pady=6)

        self.lbl_state = tk.Label(
            self.root, text="IDLE", font=("Courier New", 11, "bold"),
            fg="#555", bg="#1a1a1a"
        )
        self.lbl_state.pack(**pad)

        self.lbl_clicks = tk.Label(
            self.root, text="Clicks: 0", font=("Courier New", 14),
            fg="#aaa", bg="#1a1a1a"
        )
        self.lbl_clicks.pack(**pad)

        self.lbl_range = tk.Label(
            self.root, text="—", font=("Courier New", 26, "bold"),
            fg="#c8a96e", bg="#1a1a1a"
        )
        self.lbl_range.pack(**pad)

        self.lbl_hint = tk.Label(
            self.root, text="SHIFT+CAPS to start",
            font=("Courier New", 9), fg="#444", bg="#1a1a1a"
        )
        self.lbl_hint.pack(pady=(0, 8))

    # ── State machine ─────────────────────────────────────────────────────────
    def _advance(self):
        if self.state == self.IDLE:
            self.clicks = 0
            self.state  = self.LISTEN
        elif self.state == self.LISTEN:
            self.state  = self.RESULT
        else:                           # RESULT → reset
            self.clicks = 0
            self.state  = self.IDLE
        self._refresh()

    def _refresh(self):
        self.root.after(0, self._update_gui)

    def _update_gui(self):
        if self.state == self.IDLE:
            self.lbl_state.config(text="IDLE",    fg="#555")
            self.lbl_clicks.config(text="Clicks: 0", fg="#aaa")
            self.lbl_range.config(text="—",       fg="#c8a96e")
            self.lbl_hint.config(text="SHIFT+CAPS to start")

        elif self.state == self.LISTEN:
            self.lbl_state.config(text="● TRACKING", fg="#4caf50")
            self.lbl_clicks.config(text=f"Clicks: {self.clicks}", fg="#eee")
            r = range_label(self.clicks) if self.clicks else "scroll now…"
            self.lbl_range.config(text=r, fg="#c8a96e")
            self.lbl_hint.config(text="SHIFT+CAPS to lock range")

        else:  # RESULT
            self.lbl_state.config(text="LOCKED",  fg="#e57373")
            self.lbl_clicks.config(text=f"Clicks: {self.clicks}", fg="#eee")
            self.lbl_range.config(text=range_label(self.clicks), fg="#ffd54f")
            self.lbl_hint.config(text="SHIFT+CAPS to reset")

    # ── Input listeners ───────────────────────────────────────────────────────
    def _start_listeners(self):
        threading.Thread(target=self._kb_listener,    daemon=True).start()
        threading.Thread(target=self._mouse_listener, daemon=True).start()

    def _kb_listener(self):
        def on_press(key):
            self.keys_held.add(key)
            if HOTKEY.issubset(self.keys_held):
                self._advance()

        def on_release(key):
            self.keys_held.discard(key)

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        listener.join()

    def _mouse_listener(self):
        def on_scroll(x, y, dx, dy):
            if self.state == self.LISTEN:
                self.clicks = max(0, self.clicks + dy)
                self._refresh()

        with mouse.Listener(on_scroll=on_scroll):
            import time
            while True:
                time.sleep(1)

    def run(self):
        self.root.mainloop()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    RangeEstimator().run()
