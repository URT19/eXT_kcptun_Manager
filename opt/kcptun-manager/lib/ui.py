"""UI helpers: colors, prompts, banner, logo, tables."""
import os
import sys
import subprocess


# ============================================================
#  Colors
# ============================================================
class C:
    R = "\033[0;31m"                # red
    G = "\033[0;32m"                # green
    Y = "\033[0;33m"                # yellow
    B = "\033[0;34m"                # blue
    CY = "\033[0;36m"               # cyan
    M = "\033[0;35m"                # magenta
    W = "\033[0;37m"                # white
    BRIGHT_BLUE = "\033[1;94m"      # light blue
    BRIGHT_ORANGE = "\033[38;5;208m"  # orange
    GRAY = "\033[38;5;240m"          # dark gray
    BOLD = "\033[1m"
    DIM = "\033[2m"
    NC = "\033[0m"


def info(msg):  print(f"{C.B}[INFO]{C.NC} {msg}")
def ok(msg):    print(f"{C.G}[OK]{C.NC} {msg}")
def warn(msg):  print(f"{C.Y}[WARN]{C.NC} {msg}")
def err(msg):   print(f"{C.R}[ERR]{C.NC} {msg}", file=sys.stderr)
def die(msg):   err(msg); sys.exit(1)
def step(msg):  print(f"\n{C.M}{C.BOLD}==> {msg}{C.NC}")


def hr():
    print(f"{C.GRAY}{'·' * 60}{C.NC}")


def clear():
    os.system("clear")


# ============================================================
#  Big logo (clean 5-row ASCII)
# ============================================================
# هر حرف دقیقاً 5 ردیف، عرض متغیر
_ASCII = {
    "K": ["█  █", "█ █ ", "██  ", "█ █ ", "█  █"],
    "C": [" ███", "█   ", "█   ", "█   ", " ███"],
    "P": ["███ ", "█  █", "███ ", "█   ", "█   "],
    "T": ["████", "  █ ", "  █ ", "  █ ", "  █ "],
    "U": ["█  █", "█  █", "█  █", "█  █", " ██ "],
    "N": ["█  █", "██ █", "█ ██", "█  █", "█  █"],
    "M": ["█   █", "██ ██", "█ █ █", "█   █", "█   █"],
    "A": [" ██ ", "█  █", "████", "█  █", "█  █"],
    "G": [" ███", "█   ", "█ ██", "█  █", " ███"],
    "E": ["████", "█   ", "███ ", "█   ", "████"],
    "R": ["███ ", "█  █", "███ ", "█ █ ", "█  █"],
    " ": ["  ", "  ", "  ", "  ", "  "],
}


def _render_word(word):
    rows = ["" for _ in range(5)]
    for ch in word:
        glyph = _ASCII.get(ch, _ASCII[" "])
        for r in range(5):
            rows[r] += glyph[r] + " "
    # حذف فاصله‌ی آخر هر ردیف
    return [r.rstrip() for r in rows]


def logo_banner(role: str, version: str = None, connections: int = 0,
                tunnels: int = 0):
    """Clean logo + two-column info box (fixed layout)."""
    import os, subprocess
    if version is None:
        try:
            from lib.backup import get_version
            version = get_version()
        except Exception:
            version = "unknown"

    os.system("clear")

    PURPLE = "\033[38;5;183m"
    TEAL   = "\033[38;5;80m"
    NC     = C.NC
    GRAY   = C.GRAY

    # نقش‌ها
    role_label = role.upper()
    if role_label in ("IRAN",):
        role_col = "\033[1;32m"      # green
    elif role_label in ("KHAREJ", "FOREIGN"):
        role_label = "KHAREJ"          # هر جا FOREIGN بود، KHAREJ نشون بده
        role_col = "\033[1;31m"      # red
    else:
        role_col = "\033[1;36m"

    rows1 = _render_word("KCPTUN")
    rows2 = _render_word("MANAGER")
    w1 = max(len(r) for r in rows1)
    rows1 = [r.ljust(w1) for r in rows1]

    print()
    for i in range(5):
        print("  " + PURPLE + rows1[i] + NC + "   " + TEAL + rows2[i] + NC)
    print()

    print(f"  {GRAY}Multi-Protocol Tunnel Manager  ·  TCP · KCP · Raw · HAProxy{NC}")
    print()

    # Public IP
    try:
        ip = subprocess.run(
            ["bash", "-c",
             "curl -4fsS --max-time 2 https://api.ipify.org 2>/dev/null || "
             "curl -4fsS --max-time 2 https://ifconfig.me 2>/dev/null || echo '?'"],
            capture_output=True, text=True, timeout=4
        ).stdout.strip() or "?"
    except Exception:
        ip = "?"

    # ---- Info box ----
    BOX_W = 76
    inner_w = BOX_W - 4
    top    = "  ┌" + "─" * inner_w + "┐"
    bottom = "  └" + "─" * inner_w + "┘"
    print(GRAY + top + NC)

    lcol = 34
    rcol = inner_w - lcol - 3

    def row(l_plain, l_colored, r_plain, r_colored):
        lpad = max(0, lcol - len(l_plain))
        rpad = max(0, rcol - len(r_plain))
        print(f"  {GRAY}│{NC}{l_colored}{' ' * lpad}   {r_colored}{' ' * rpad}{GRAY}│{NC}")

    row(
        "  Version: " + version, f"  {GRAY}Version:{NC} {C.CY}{version}{NC}",
        "  IP: " + ip,           f"  {GRAY}IP:{NC} {C.CY}{ip}{NC}",
    )
    row(
        "  Role: " + role_label, f"  {GRAY}Role:{NC} {role_col}{role_label}{NC}",
        "  Connections: " + str(connections),
        f"  {GRAY}Connections:{NC} {C.BOLD}{connections}{NC}",
    )
    row(
        "  Tunnels: " + str(tunnels),
        f"  {GRAY}Tunnels:{NC} {C.BOLD}{tunnels}{NC}",
        "", "",
    )

    print(GRAY + bottom + NC)
    print()


# ============================================================
#  Simple banner (fallback for small screens)
# ============================================================
def banner(role: str, version: str = None):
    if version is None:
        try:
            from lib.backup import get_version
            version = get_version()
        except Exception:
            version = "unknown"
    clear()
    print(f"{C.CY}{C.BOLD}")
    print("=" * 58)
    print(f"  kcptun-rs Manager  |  Role: {role.upper()}  |  v{version}")
    print("=" * 58)
    print(C.NC)


# ============================================================
#  Prompts
# ============================================================
def prompt(label: str, default: str = "") -> str:
    if default:
        s = f"  {C.BOLD}{label}{C.NC} [{C.G}{default}{C.NC}]: "
        ans = input(s).strip()
        return ans or default
    return input(f"  {C.BOLD}{label}{C.NC}: ").strip()


def confirm(label: str, default: str = "n") -> bool:
    """Single-key y/n — no Enter needed."""
    import sys, tty, termios
    prompt_str = f"  {C.BOLD}{label}{C.NC} (y/n) [{C.G}{default}{C.NC}]: "
    sys.stdout.write(prompt_str); sys.stdout.flush()
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    sys.stdout.write(ch + "\n"); sys.stdout.flush()
    ch = ch.lower()
    if ch in ("y", "n"):
        return ch == "y"
    return default.lower().startswith("y")


def pause():
    print()
    input(f"  {C.DIM}Enter...{C.NC}")


# ============================================================
#  Two-column menu with sections
# ============================================================
def show_server_ip():
    """Print server's public IP (kept for backward compat)."""
    import subprocess
    try:
        ip = subprocess.run(
            ["bash", "-c",
             "curl -4fsS --max-time 2 https://api.ipify.org 2>/dev/null || "
             "curl -4fsS --max-time 2 https://ifconfig.me 2>/dev/null || echo '?'"],
            capture_output=True, text=True, timeout=4
        ).stdout.strip() or "?"
    except Exception:
        ip = "?"
    print(f"  {C.DIM}Server IP: {C.G}{ip}{C.NC}")


def select_from_list(items, prompt_label="Entekhab"):
    """items: list of (display, value). Return chosen value or None."""
    if not items:
        return None
    for i, (disp, _) in enumerate(items, start=1):
        print(f"  {i:>2}) {disp}")
    print("   0) Cancel")
    ch = prompt(prompt_label)
    if ch in ("", "0"):
        return None
    try:
        n = int(ch)
    except ValueError:
        err("Na-mojaz.")
        return None
    if n < 1 or n > len(items):
        err("Na-mojaz.")
        return None
    return items[n - 1][1]


def menu_two_cols(items, txt_w=30):
    """
    items: list of tuples.
      ("__section__", "label")     -> full-width section header
      ("N", "text", color, enabled) -> menu entry
    Items are placed in 2 columns in order.
    """
    NC = C.NC
    D  = C.DIM
    GRAY = C.GRAY

    def render_cell(num, text, color, enabled):
        num_str = f"{num:>2}"
        if enabled:
            return f"{D}[{NC}{color}{num_str}{NC}{D}]{NC} {color}{text}{NC}"
        return f"{D}[{num_str}] {text}{NC}"

    def vis_cell(num, text):
        return 6 + len(text)   # "[NN]  "

    def print_section(label):
        bar = "·" * max(0, 60 - len(label) - 3)
        print(f"  {GRAY}{label}  {bar}{NC}")

    # ---- جدا کردن section ها و entries ----
    # می‌سازیم: [("section", label), ("entry", ...), ("entry", ...), ...]
    # بعد هر دو entry متوالی توی یه ردیف نمایش داده می‌شن
    pending_left = None
    first = True
    for item in items:
        if item[0] == "__section__":
            # اگه یه left پندینگ مونده، تنها چاپش کن
            if pending_left is not None:
                ln, lt, lc, le = pending_left
                print("  " + render_cell(ln, lt, lc, le))
                pending_left = None
            if not first:
                print()
            if item[1]:
                print_section(item[1])
            first = False
            continue

        # entry
        if pending_left is None:
            pending_left = item
        else:
            # چاپ دو تا در یک ردیف
            ln, lt, lc, le = pending_left
            rn, rt, rc, re_ = item
            lcell = render_cell(ln, lt, lc, le)
            rcell = render_cell(rn, rt, rc, re_)
            lvis = vis_cell(ln, lt)
            lpad = max(0, txt_w + 6 - lvis)
            print("  " + lcell + " " * lpad + rcell)
            pending_left = None

    # آخرین entry که جفت نداشت
    if pending_left is not None:
        ln, lt, lc, le = pending_left
        print("  " + render_cell(ln, lt, lc, le))
