import socket
import struct
import random
import string
import time
import threading

# ── CONFIG ──────────────────────────────────────────────────────────────────
RCON_HOST = "localhost"
RCON_PORT = 25575
RCON_PASSWORD = "yourpassword"   # must match rcon.password in server.properties
# ────────────────────────────────────────────────────────────────────────────

class RCONClient:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.sock = None
        self._req_id = 1

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self._send(3, self.password) 
        resp_id, _, _ = self._recv()
        if resp_id == -1:
            raise ConnectionRefusedError("RCON auth failed — check your password.")

    def command(self, cmd):
        req = self._req_id
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
                raise ConnectionError("RCON connection lost.")
            data += chunk
        return data

    def close(self):
        if self.sock:
            self.sock.close()


def random_dimension_code():
    length = random.randint(5, 9)
    return "".join(random.choices(string.ascii_lowercase, k=length))


def do_warp(rcon: RCONClient):
    dim = random_dimension_code()
    print(f"\n>> Warping to dimension: {dim}")
    rcon.command(f"execute as @a run warp {dim}")
    rcon.command(f"execute at @p run spawnpoint @a")
    print("   Done.")


def run_bossbar_countdown(rcon: RCONClient, seconds: int, bar_id: str):
    rcon.command(f"bossbar add {bar_id} {{\"text\":\"Next warp in...\"}}")
    rcon.command(f"bossbar set {bar_id} players @a")
    rcon.command(f"bossbar set {bar_id} color blue")
    rcon.command(f"bossbar set {bar_id} max {seconds}")
    rcon.command(f"bossbar set {bar_id} value {seconds}")

    for remaining in range(seconds, 0, -1):
        rcon.command(f"bossbar set {bar_id} value {remaining}")
        rcon.command(f"bossbar set {bar_id} name {{\"text\":\"Next warp in {remaining}s\"}}")
        if remaining in (30, 10, 5, 3, 2, 1):
            rcon.command(f"say §eWarping in {remaining} second{'s' if remaining != 1 else ''}!")
        time.sleep(1)

    rcon.command(f"bossbar remove {bar_id}")


def main():
    print("=== Random Warp for 20w14infinite ===")
    print(f"Connecting to {RCON_HOST}:{RCON_PORT}...\n")

    rcon = RCONClient(RCON_HOST, RCON_PORT, RCON_PASSWORD)
    try:
        rcon.connect()
        print("Connected!\n")
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure server.properties has:")
        print("  enable-rcon=true")
        print(f"  rcon.port={RCON_PORT}")
        print(f"  rcon.password={RCON_PASSWORD}")
        input("\nPress Enter to exit.")
        return

    try:
        raw = input("Seconds between each warp (default 60): ").strip()
        interval = int(raw) if raw.isdigit() and int(raw) > 0 else 60
    except ValueError:
        interval = 60

    print(f"\nStarting — warping every {interval}s. Ctrl+C to stop.\n")

    bar_id = "randomwarp:timer"
    loop = 0

    try:
        while True:
            loop += 1
            if loop > 1:
                do_warp(rcon)

            run_bossbar_countdown(rcon, interval, bar_id)

            if loop == 1:
                do_warp(rcon)

    except KeyboardInterrupt:
        print("\nStopped.")
        try:
            rcon.command(f"bossbar remove {bar_id}")
        except:
            pass
    finally:
        rcon.close()


if __name__ == "__main__":
    main()
