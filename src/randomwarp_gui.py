import socket
import struct
import random
import string
import time
import threading
import customtkinter as ctk
from tkinter import scrolledtext
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RCONClient:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.sock = None
        self._req_id = 1

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect((self.host, self.port))
        self._send(3, self.password)
        resp_id, _, _ = self._recv()
        if resp_id == -1:
            raise ConnectionRefusedError("RCON auth failed — wrong password?")

    def command(self, cmd):
        self._send(2, cmd)
        _, _, body = self._recv()
        return body

    def _send(self, pkt_type, body):
        data = body.encode("utf-8")
        payload = struct.pack("<ii", self._req_id, pkt_type) + data + b"\x00\x00"
        self.sock.sendall(struct.pack("<i", len(payload)) + payload)
        self._req_id += 1

    def _recv(self):
        raw_len = self._recv_bytes(4)
        length = struct.unpack("<i", raw_len)[0]
        raw = self._recv_bytes(length)
        req_id, pkt_type = struct.unpack("<ii", raw[:8])
        body = raw[8:-2].decode("utf-8", errors="replace")
        return req_id, pkt_type, body

    def _recv_bytes(self, n):
        data = b""
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError("RCON connection dropped.")
            data += chunk
        return data

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass


def random_dimension_code():
    length = random.randint(5, 9)
    return "".join(random.choices(string.ascii_lowercase, k=length))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Random Warp — 20w14infinite")
        self.geometry("620x700")
        self.resizable(False, False)

        self.rcon: RCONClient | None = None
        self._running = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.BAR_ID = "randomwarp:timer"

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 16, "pady": 6}

        # ── Header ──────────────────────────────────────────────────────────
        header = ctk.CTkLabel(self, text="Random Warp — 20w14∞",
                              font=ctk.CTkFont(size=22, weight="bold"))
        header.pack(pady=(18, 4))

        # ── RCON Config frame ────────────────────────────────────────────────
        cfg = ctk.CTkFrame(self)
        cfg.pack(fill="x", **pad)

        ctk.CTkLabel(cfg, text="RCON Config", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=4, pady=(8, 4), padx=12, sticky="w")

        ctk.CTkLabel(cfg, text="Host").grid(row=1, column=0, padx=(12, 4), pady=4, sticky="e")
        self.host_var = ctk.StringVar(value="localhost")
        ctk.CTkEntry(cfg, textvariable=self.host_var, width=140).grid(row=1, column=1, pady=4, sticky="w")

        ctk.CTkLabel(cfg, text="Port").grid(row=1, column=2, padx=(12, 4), pady=4, sticky="e")
        self.port_var = ctk.StringVar(value="25575")
        ctk.CTkEntry(cfg, textvariable=self.port_var, width=70).grid(row=1, column=3, padx=(0, 12), pady=4, sticky="w")

        ctk.CTkLabel(cfg, text="Password").grid(row=2, column=0, padx=(12, 4), pady=(4, 10), sticky="e")
        self.pw_var = ctk.StringVar(value="")
        ctk.CTkEntry(cfg, textvariable=self.pw_var, show="*", width=220).grid(
            row=2, column=1, columnspan=3, padx=(0, 12), pady=(4, 10), sticky="w")

        # ── Interval ─────────────────────────────────────────────────────────
        int_frame = ctk.CTkFrame(self)
        int_frame.pack(fill="x", **pad)

        ctk.CTkLabel(int_frame, text="Warp Interval", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(8, 4), sticky="w")
        ctk.CTkLabel(int_frame, text="Seconds between warps:").grid(row=1, column=0, padx=(12, 8), pady=(0, 10), sticky="e")
        self.interval_var = ctk.StringVar(value="60")
        ctk.CTkEntry(int_frame, textvariable=self.interval_var, width=80).grid(
            row=1, column=1, padx=(0, 12), pady=(0, 10), sticky="w")

        # ── Status cards ──────────────────────────────────────────────────────
        cards = ctk.CTkFrame(self)
        cards.pack(fill="x", **pad)

        self._make_card(cards, "Status", 0)
        self.status_label = ctk.CTkLabel(cards, text="Idle", font=ctk.CTkFont(size=13),
                                          text_color="#aaaaaa")
        self.status_label.grid(row=1, column=0, padx=16, pady=(0, 10))

        self._make_card(cards, "Countdown", 1)
        self.countdown_label = ctk.CTkLabel(cards, text="--s", font=ctk.CTkFont(size=26, weight="bold"),
                                             text_color="#4fc3f7")
        self.countdown_label.grid(row=1, column=1, padx=16, pady=(0, 10))

        self._make_card(cards, "Last Dimension", 2)
        self.dim_label = ctk.CTkLabel(cards, text="—", font=ctk.CTkFont(size=13, weight="bold"),
                                       text_color="#a5d6a7")
        self.dim_label.grid(row=1, column=2, padx=16, pady=(0, 10))

        cards.grid_columnconfigure((0, 1, 2), weight=1)

        # ── Progress bar ──────────────────────────────────────────────────────
        self.progress = ctk.CTkProgressBar(self, width=580)
        self.progress.pack(pady=(2, 6))
        self.progress.set(0)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=4)

        self.start_btn = ctk.CTkButton(btn_frame, text="▶  Start", width=140,
                                        command=self._start, fg_color="#2e7d32", hover_color="#388e3c")
        self.start_btn.grid(row=0, column=0, padx=8)

        self.stop_btn = ctk.CTkButton(btn_frame, text="■  Stop", width=140,
                                       command=self._stop, fg_color="#b71c1c", hover_color="#c62828",
                                       state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=8)

        # ── Log ───────────────────────────────────────────────────────────────
        ctk.CTkLabel(self, text="Log", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=18)
        self.log_box = ctk.CTkTextbox(self, width=584, height=200, font=ctk.CTkFont(family="Courier", size=11))
        self.log_box.pack(padx=16, pady=(2, 16))
        self.log_box.configure(state="disabled")

    def _make_card(self, parent, title, col):
        ctk.CTkLabel(parent, text=title, font=ctk.CTkFont(size=11),
                     text_color="#888888").grid(row=0, column=col, padx=16, pady=(10, 2))

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{time.strftime('%H:%M:%S')}  {msg}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_status(self, text, color="#aaaaaa"):
        self.status_label.configure(text=text, text_color=color)

    def _start(self):
        host = self.host_var.get().strip()
        pw = self.pw_var.get().strip()
        try:
            port = int(self.port_var.get().strip())
            interval = int(self.interval_var.get().strip())
            if interval <= 0:
                raise ValueError
        except ValueError:
            self._log("Invalid port or interval.")
            return

        self._stop_event.clear()
        self._running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._set_status("Connecting…", "#fff176")

        self._thread = threading.Thread(target=self._run_loop,
                                         args=(host, port, pw, interval), daemon=True)
        self._thread.start()

    def _stop(self):
        self._stop_event.set()
        self._running = False
        self.stop_btn.configure(state="disabled")
        self._set_status("Stopping…", "#ff8a65")

    def _cleanup_ui(self):
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.countdown_label.configure(text="--s")
        self.progress.set(0)
        self._set_status("Idle", "#aaaaaa")

    def _run_loop(self, host, port, pw, interval):
        rcon = RCONClient(host, port, pw)
        try:
            rcon.connect()
        except Exception as e:
            self.after(0, lambda: self._log(f"Error connecting: {e}"))
            self.after(0, lambda: self._set_status("Connection failed", "#ef5350"))
            self.after(0, self._cleanup_ui)
            return

        self.after(0, lambda: self._log(f"Connected to {host}:{port}"))
        self.after(0, lambda: self._set_status("Running", "#81c784"))

        first = True
        try:
            while not self._stop_event.is_set():
                if not first:
                    self._do_warp(rcon)
                self._countdown(rcon, interval)
                if first:
                    self._do_warp(rcon)
                    first = False
        except Exception as e:
            self.after(0, lambda: self._log(f"Error: {e}"))
        finally:
            try:
                rcon.command(f"bossbar remove {self.BAR_ID}")
            except:
                pass
            rcon.close()
            self.after(0, lambda: self._log("⏹ Stopped."))
            self.after(0, self._cleanup_ui)

    def _do_warp(self, rcon):
        dim = random_dimension_code()
        self.after(0, lambda: self.dim_label.configure(text=dim))
        self.after(0, lambda: self._log(f"Warping to: {dim}"))
        rcon.command(f"execute as @a run warp {dim}")
        rcon.command("execute at @p run spawnpoint @a")

    def _countdown(self, rcon, total):
        try:
            rcon.command(f"bossbar add {self.BAR_ID} {{\"text\":\"Next warp...\"}}")
        except:
            pass
        rcon.command(f"bossbar set {self.BAR_ID} players @a")
        rcon.command(f"bossbar set {self.BAR_ID} color blue")
        rcon.command(f"bossbar set {self.BAR_ID} max {total}")

        for remaining in range(total, 0, -1):
            if self._stop_event.is_set():
                break
            rcon.command(f"bossbar set {self.BAR_ID} value {remaining}")
            rcon.command(f"bossbar set {self.BAR_ID} name {{\"text\":\"Next warp in {remaining}s\"}}")
            if remaining in (30, 10, 5, 3, 2, 1):
                rcon.command(f"say §eWarping in {remaining} second{'s' if remaining != 1 else ''}!")

            frac = remaining / total
            rem = remaining
            self.after(0, lambda r=rem: self.countdown_label.configure(text=f"{r}s"))
            self.after(0, lambda f=frac: self.progress.set(f))
            time.sleep(1)

        try:
            rcon.command(f"bossbar remove {self.BAR_ID}")
        except:
            pass

        self.after(0, lambda: self.countdown_label.configure(text="Warping!"))
        self.after(0, lambda: self.progress.set(0))


if __name__ == "__main__":
    app = App()
    app.mainloop()
