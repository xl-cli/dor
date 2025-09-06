import json
import os
import sys
from datetime import datetime
from api_request import get_otp, submit_otp, save_tokens, get_package, purchase_package
from purchase_api import show_multipayment, show_qris_payment, settlement_bounty
from auth_helper import AuthInstance

# ========== Rich Setup ==========
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.align import Align
    from rich.box import ROUNDED, HEAVY, DOUBLE
    from rich.text import Text
    from rich.rule import Rule
    from rich.prompt import Prompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_OK = True
except Exception:
    RICH_OK = False

console = Console() if RICH_OK else None

# ========= Theme presets + persist =========
_THEME_FILE = "theme.json"

THEMES = {
    "dark_neon": {
        "border_primary": "#7C3AED",
        "border_info": "#06B6D4",
        "border_success": "#10B981",
        "border_warning": "#F59E0B",
        "border_error": "#EF4444",
        "text_title": "bold #E5E7EB",
        "text_sub": "bold #22D3EE",
        "text_ok": "bold #34D399",
        "text_warn": "bold #FBBF24",
        "text_err": "bold #F87171",
        "text_body": "#D1D5DB",
        "text_key": "#A78BFA",
        "text_value": "bold #F3F4F6",
        "text_money": "bold #34D399",
        "text_date": "bold #FBBF24",
        "text_number": "#C084FC",
        "gradient_start": "#22D3EE",
        "gradient_end": "#A78BFA",
    },
    "default": {
        "border_primary": "magenta",
        "border_info": "cyan",
        "border_success": "green",
        "border_warning": "yellow",
        "border_error": "red",
        "text_title": "bold white",
        "text_sub": "bold cyan",
        "text_ok": "bold green",
        "text_warn": "bold yellow",
        "text_err": "bold red",
        "text_body": "white",
        "text_key": "magenta",
        "text_value": "bold white",
        "text_money": "bold green",
        "text_date": "bold yellow",
        "text_number": "magenta",
        "gradient_start": "#8A2BE2",
        "gradient_end": "#00FFFF",
    },
    "red_black": {
        "border_primary": "#EF4444",
        "border_info": "#F87171",
        "border_success": "#22C55E",
        "border_warning": "#F59E0B",
        "border_error": "#DC2626",
        "text_title": "bold #F3F4F6",
        "text_sub": "bold #EF4444",
        "text_ok": "bold #22C55E",
        "text_warn": "bold #F59E0B",
        "text_err": "bold #F87171",
        "text_body": "#E5E7EB",
        "text_key": "#F87171",
        "text_value": "bold #F3F4F6",
        "text_money": "bold #22C55E",
        "text_date": "bold #FBBF24",
        "text_number": "#EF4444",
        "gradient_start": "#DC2626",
        "gradient_end": "#F59E0B",
    },
    "emerald_glass": {
        "border_primary": "#10B981",
        "border_info": "#34D399",
        "border_success": "#059669",
        "border_warning": "#A3E635",
        "border_error": "#EF4444",
        "text_title": "bold #ECFDF5",
        "text_sub": "bold #34D399",
        "text_ok": "bold #22C55E",
        "text_warn": "bold #A3E635",
        "text_err": "bold #F87171",
        "text_body": "#D1FAE5",
        "text_key": "#6EE7B7",
        "text_value": "bold #F0FDFA",
        "text_money": "bold #22C55E",
        "text_date": "bold #A3E635",
        "text_number": "#10B981",
        "gradient_start": "#34D399",
        "gradient_end": "#A7F3D0",
    },
}

# THEME aktif (load dari file jika ada)
def _load_theme_name():
    try:
        if os.path.exists(_THEME_FILE):
            with open(_THEME_FILE, "r", encoding="utf8") as f:
                return json.load(f).get("name", "dark_neon")
    except Exception:
        pass
    return "dark_neon"

def _save_theme_name(name: str):
    try:
        with open(_THEME_FILE, "w", encoding="utf8") as f:
            json.dump({"name": name}, f)
    except Exception:
        pass

_theme_name = _load_theme_name()
THEME = THEMES.get(_theme_name, THEMES["dark_neon"]).copy()

def set_theme(name: str):
    global THEME, _theme_name
    if name in THEMES:
        THEME = THEMES[name].copy()
        _theme_name = name
        _save_theme_name(name)
        return True
    return False

def _c(key: str) -> str:
    return THEME.get(key, "white")

# ========= Phone-friendly width & centered helpers =========
def _term_width(default=80):
    if not RICH_OK:
        return default
    try:
        return console.size.width
    except Exception:
        return default

def _target_width(pct=0.9, min_w=38, max_w=None):
    w = _term_width()
    tw = int(w * pct)
    if max_w is not None:
        tw = min(tw, max_w)
    tw = max(min_w, min(tw, w - 2))
    return tw

def _print_centered_panel(renderable, *, title=None, border_style=None, box=ROUNDED, padding=(1,1), width=None):
    if not RICH_OK:
        print("--------------------------")
        if isinstance(renderable, str):
            print(renderable)
        else:
            print("[Panel disabled (rich not installed)]")
        print("--------------------------")
        return
    panel = Panel(
        renderable,
        title=title,
        border_style=border_style,
        box=box,
        padding=padding,
        width=width or _target_width()
    )
    console.print(Align.center(panel))

# --- Gradient manual (kompatibel rich lama) ---
def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)

def _lerp(a, b, t):
    return int(a + (b - a) * t)

def _gradient_colors(start_hex, end_hex, n):
    try:
        r1,g1,b1 = _hex_to_rgb(start_hex)
        r2,g2,b2 = _hex_to_rgb(end_hex)
        if n <= 1:
            return [start_hex]
        colors = []
        for i in range(n):
            t = i / (n - 1)
            r = _lerp(r1, r2, t)
            g = _lerp(g1, g2, t)
            b = _lerp(b1, b2, t)
            colors.append(_rgb_to_hex((r,g,b)))
        return colors
    except Exception:
        return [start_hex] * max(1, n)

def _print_gradient_title(text="Dor XL by Flyxt9"):
    if not RICH_OK:
        print("Dor XL by Flyxt9")
        return
    try:
        s = str(text)
        colors = _gradient_colors(_c("gradient_start"), _c("gradient_end"), len(s))
        t = Text(justify="center")
        for ch, col in zip(s, colors):
            t.append(ch, style=f"bold {col}")
        console.print(Align.center(t))
    except Exception:
        t = Text(str(text), style=_c("text_title"))
        console.print(Align.center(t))

# ========= Old helpers =========
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    if RICH_OK:
        console.print("\n[dim]Tekan Enter untuk lanjut...[/]", end="")
        input()
    else:
        input("\nTekan Enter untuk lanjut...")

# ========= Banner =========
def show_banner():
    clear_screen()
    if RICH_OK:
        header = Panel.fit(
            Align.center(Text.assemble(
                ("✦ ", _c("text_key")),
                ("Panel Dor Paket ©2025", _c("text_title")),
                (" by ", "dim"),
                ("Barbex_ID", _c("text_sub")),
                (" ✦", _c("text_key"))
            )),
            title=f"[{_c('text_title')}]SELAMAT DATANG[/]",
            subtitle="[dim]Powered by dratx1[/]",
            border_style=_c("border_primary"),
            box=DOUBLE,
            padding=(1, 2)
        )
        console.print(Align.center(header))
        _print_gradient_title("Tembak Paket Internet Murah")
        console.print(Align.center(Rule(style=_c("border_primary"))))
    else:
        print("--------------------------")
        print("")
        print("--------------------------")

# ========= Main Menu =========
def show_main_menu(number, balance, balance_expired_at):
    show_banner()

    phone_number = number
    remaining_balance = balance
    expired_at_dt = datetime.fromtimestamp(balance_expired_at).strftime("%Y-%m-%d %H:%M:%S")

    if RICH_OK:
        info = Table.grid(padding=(0, 2))
        info.add_column(justify="right", style=_c("text_sub"))
        info.add_column(style=_c("text_body"))
        info.add_row("Nomor", f"[{_c('text_value')}]{phone_number}[/]")
        info.add_row("Pulsa", f"[{_c('text_money')}]Rp {remaining_balance:,}[/]")
        info.add_row("Masa aktif", f"[{_c('text_date')}]{expired_at_dt}[/]")
        _print_centered_panel(info, title=f"[{_c('text_title')}]Informasi Akun[/]", border_style=_c("border_info"))

        menu = Table(show_header=False, box=ROUNDED, padding=(0,1), expand=True)
        menu.add_column("key", justify="right", style=_c("text_number"), no_wrap=True, width=4)
        menu.add_column("desc", style=_c("text_body"))
        menu.add_row("[bold]1[/]", "Login/Ganti akun")
        menu.add_row("[bold]2[/]", "Lihat Paket Saya")
        menu.add_row("[bold]3[/]", "Dor Paket XUT")
        menu.add_row("[bold]4[/]", "Dor Paket Masa Aktif")
        menu.add_row("[bold]5[/]", "Dor Paket Lainnya..")
        menu.add_row("[bold]6[/]", "Input Family Code Sendiri")
        menu.add_row("[bold]7[/]", f"[{_c('text_sub')}]Ganti Tema[/]")
        menu.add_row("[bold]99[/]", f"[{_c('text_err')}]Tutup aplikasi[/]")
        _print_centered_panel(menu, title=f"[{_c('text_title')}]Menu[/]", border_style=_c("border_primary"))
    else:
        print("--------------------------")
        print("Informasi Akun")
        print(f"Nomor: {phone_number}")
        print(f"Pulsa: Rp {remaining_balance}")
        print(f"Masa aktif: {expired_at_dt}")
        print("--------------------------")
        print("Menu:")
        print("1. Login/Ganti akun")
        print("2. Lihat Paket Saya")
        print("3. Dor Paket XUT")
        print("4. Dor Paket Masa Aktif")
        print("5. Dor Paket Lainnya..")
        print("6. Input Family Code Sendiri")
        print("7. Ganti Tema")
        print("99. Tutup aplikasi")
        print("--------------------------")

# ========= Menu Ganti Tema =========
def change_theme_menu():
    if not RICH_OK:
        print("Fitur tema butuh paket 'rich'. Jalankan: pip install rich")
        pause()
        return

    show_banner()

    table = Table(box=ROUNDED, show_header=True, header_style=_c("text_sub"), expand=True)
    table.add_column("No", justify="right", style=_c("text_number"), width=4, no_wrap=True)
    table.add_column("Nama Tema", style=_c("text_body"))
    table.add_column("Preview", style=_c("text_body"))

    keys = list(THEMES.keys())
    previews = {
        "dark_neon": "Neon gelap (violet/cyan)",
        "default": "Magenta/Cyan klasik",
        "red_black": "Merah-Hitam kontras",
        "emerald_glass": "Emerald soft/glass",
    }
    for i, k in enumerate(keys, start=1):
        table.add_row(str(i), k, previews.get(k, "-"))

    _print_centered_panel(table, title=f"[{_c('text_title')}]Pilih Tema[/]", border_style=_c("border_info"))
    choice = Prompt.ask(f"[{_c('text_sub')}]Masukkan nomor tema", default="1")

    if not choice.isdigit() or not (1 <= int(choice) <= len(keys)):
        _print_centered_panel("Pilihan tidak valid.", border_style=_c("border_error"))
        pause()
        return

    name = keys[int(choice) - 1]
    set_theme(name)
    _print_centered_panel(f"Tema diganti ke: [bold]{name}[/]", border_style=_c("border_success"))
    pause()

# ========= Account Menu =========
def show_account_menu():
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()

    in_account_menu = True
    add_user = False
    while in_account_menu:
        clear_screen()
        show_banner()

        if AuthInstance.get_active_user() is None or add_user:
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                _print_centered_panel("[bold]Gagal menambah akun. Silahkan coba lagi.[/]", border_style=_c("border_error"))
                pause()
                continue

            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens

            if add_user:
                add_user = False
            continue

        if RICH_OK:
            table = Table(box=ROUNDED, show_header=True, header_style=_c("text_sub"), expand=True)
            table.add_column("No", justify="right", style=_c("text_number"), width=4)
            table.add_column("Nomor", style=_c("text_body"))
            table.add_column("Status", style=_c("text_body"))
            if not users or len(users) == 0:
                table.add_row("-", "Tidak ada akun tersimpan.", "-")
            else:
                for idx, user in enumerate(users):
                    is_active = active_user and user["number"] == active_user["number"]
                    status = f"[{_c('text_ok')}]Aktif[/]" if is_active else "[dim]-[/]"
                    table.add_row(str(idx + 1), str(user["number"]), status)

            _print_centered_panel(table, title=f"[{_c('text_title')}]Akun Tersimpan[/]", border_style=_c("border_info"))

            cmd = Table.grid(padding=(0,2), expand=True)
            cmd.add_column(justify="right", style=_c("text_number"), no_wrap=True, width=6)
            cmd.add_column(style=_c("text_body"))
            cmd.add_row("[bold]0[/]", "Tambah Akun")
            cmd.add_row("[bold]00[/]", "Kembali ke menu utama")
            cmd.add_row("[bold]99[/]", f"[{_c('text_err')}]Hapus Akun aktif[/]")
            cmd.add_row("", "Masukan nomor akun (No) untuk berganti")
            _print_centered_panel(cmd, title=f"[{_c('text_title')}]Command[/]", border_style=_c("border_primary"))

            input_str = Prompt.ask(f"[{_c('text_sub')}]Pilihan[/]")
        else:
            print("--------------------------")
            if not users or len(users) == 0:
                print("Tidak ada akun tersimpan.")
            else:
                print("Akun Tersimpan:")
                for idx, user in enumerate(users):
                    is_active = active_user and user["number"] == active_user["number"]
                    active_marker = " (Aktif)" if is_active else ""
                    print(f"{idx + 1}. {user['number']}{active_marker}")
            print("Command:")
            print("0: Tambah Akun")
            print("00: Kembali ke menu utama")
            print("99: Hapus Akun aktif")
            print("Masukan nomor akun untuk berganti.")
            input_str = input("Pilihan:")

        if input_str == "00":
            in_account_menu = False
            return active_user["number"] if active_user else None
        elif input_str == "0":
            add_user = True
            continue
        elif input_str == "99":
            if not active_user:
                _print_centered_panel("Tidak ada akun aktif untuk dihapus.", border_style=_c("border_warning"))
                pause()
                continue
            confirm = (input(f"Yakin ingin menghapus akun {active_user['number']}? (y/n): ").lower() == 'y')
            if confirm:
                AuthInstance.remove_refresh_token(active_user["number"])
                users = AuthInstance.refresh_tokens
                active_user = AuthInstance.get_active_user()
                _print_centered_panel("Akun berhasil dihapus.", border_style=_c("border_success"))
                pause()
            else:
                _print_centered_panel("Penghapusan akun dibatalkan.", border_style=_c("border_info"))
                pause()
            continue
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            return selected_user['number']
        else:
            _print_centered_panel("Input tidak valid. Silahkan coba lagi.", border_style=_c("border_error"))
            pause()
            continue

# ========= Login Menu (opsional) =========
def show_login_menu():
    clear_screen()
    show_banner()
    if RICH_OK:
        menu = Table(box=ROUNDED, show_header=False, padding=(0,1), expand=True)
        menu.add_column("key", justify="right", style=_c("text_number"), no_wrap=True, width=4)
        menu.add_column("desc", style=_c("text_body"))
        menu.add_row("[bold]1[/]", "Request OTP")
        menu.add_row("[bold]2[/]", "Submit OTP")
        menu.add_row("[bold]99[/]", f"[{_c('text_err')}]Tutup aplikasi[/]")
        _print_centered_panel(menu, title=f"[{_c('text_title')}]Login ke MyXL[/]", border_style=_c("border_info"))
    else:
        print("--------------------------")
        print("Login ke MyXL")
        print("--------------------------")
        print("1. Request OTP")
        print("2. Submit OTP")
        print("99. Tutup aplikasi")
        print("--------------------------")

# ========= Login Prompt =========
def login_prompt(api_key: str):
    clear_screen()
    show_banner()
    if RICH_OK:
        _print_centered_panel(f"[{_c('text_sub')}]Masukan nomor XL Prabayar (Contoh 6281234567890)",
                              title=f"[{_c('text_title')}]Login ke MyXL[/]", border_style=_c("border_info"))
        phone_number = Prompt.ask(f"[{_c('text_sub')}]Nomor[/]")
    else:
        print("--------------------------")
        print("Login ke MyXL")
        print("--------------------------")
        print("Masukan nomor XL Prabayar (Contoh 6281234567890):")
        phone_number = input("Nomor: ")

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        _print_centered_panel("Nomor tidak valid. Pastikan nomor diawali '628' dan panjang benar.", border_style=_c("border_error"))
        return None, None

    try:
        if RICH_OK:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                progress.add_task(description="Mengirim OTP...", total=None)
                subscriber_id = get_otp(phone_number)
        else:
            subscriber_id = get_otp(phone_number)

        if not subscriber_id:
            _print_centered_panel("Gagal meminta OTP.", border_style=_c("border_error"))
            return None, None

        _print_centered_panel("OTP berhasil dikirim ke nomor Anda.", border_style=_c("border_success"))

        otp = (Prompt.ask(f"[{_c('text_sub')}]Masukkan OTP (6 digit)") if RICH_OK else input("Masukkan OTP yang telah dikirim: "))
        if not otp.isdigit() or len(otp) != 6:
            _print_centered_panel("OTP tidak valid. Pastikan 6 digit angka.", border_style=_c("border_error"))
            pause()
            return None, None

        tokens = submit_otp(api_key, phone_number, otp)
        if not tokens:
            _print_centered_panel("Gagal login. Periksa OTP dan coba lagi.", border_style=_c("border_error"))
            pause()
            return None, None

        _print_centered_panel("Berhasil login!", border_style=_c("border_success"))
        return phone_number, tokens["refresh_token"]

    except Exception:
        _print_centered_panel("Terjadi kesalahan saat login.", border_style=_c("border_error"))
        return None, None

# ========= Packages =========
def show_package_menu(packages):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        _print_centered_panel("No active user tokens found.", border_style=_c("border_error"))
        pause()
        return None

    in_package_menu = True
    while in_package_menu:
        clear_screen()
        show_banner()

        if RICH_OK:
            table = Table(box=HEAVY, show_header=True, header_style=_c("text_sub"), expand=True)
            table.add_column("No", justify="right", style=_c("text_number"), width=4, no_wrap=True)
            table.add_column("Nama Paket", style=_c("text_body"))
            table.add_column("Harga", justify="right", style=_c("text_money"))
            for pkg in packages:
                table.add_row(str(pkg['number']), pkg['name'], f"Rp {pkg['price']:,}")

            _print_centered_panel(table, title=f"[{_c('text_title')}]Paket Tersedia[/]", border_style=_c("border_info"))
            _print_centered_panel(f"[{_c('text_sub')}]99. Kembali ke menu utama", border_style=_c("border_primary"))
            pkg_choice = Prompt.ask(f"[{_c('text_sub')}]Pilih paket (nomor)")
        else:
            print("--------------------------")
            print("Paket Tersedia")
            print("--------------------------")
            for pkg in packages:
                print(f"{pkg['number']}. {pkg['name']} - Rp {pkg['price']}")
            print("99. Kembali ke menu utama")
            print("--------------------------")
            pkg_choice = input("Pilih paket (nomor): ")

        if pkg_choice == "99":
            in_package_menu = False
            return None

        if not pkg_choice.isdigit():
            _print_centered_panel("Input harus angka.", border_style=_c("border_error"))
            pause()
            continue

        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)
        if not selected_pkg:
            _print_centered_panel("Paket tidak ditemukan. Silakan masukan nomor yang benar.", border_style=_c("border_error"))
            pause()
            continue

        is_done = show_package_details(api_key, tokens, selected_pkg["code"])
        if is_done:
            in_package_menu = False
            return None

def show_package_details(api_key, tokens, package_option_code):
    clear_screen()
    show_banner()

    package = get_package(api_key, tokens, package_option_code)
    if not package:
        _print_centered_panel("Failed to load package details.", border_style=_c("border_error"))
        pause()
        return False

    name2 = package.get("package_detail_variant", {}).get("name","")
    price = package["package_option"]["price"]
    detail = package["package_option"]["tnc"]
    detail = (detail.replace("<p>", "").replace("</p>", "")
                    .replace("<strong>", "").replace("</strong>", "")
                    .replace("<br>", "").replace("<br />", "").strip())
    name3 = package.get("package_option", {}).get("name","")
    name1 = package.get("package_family", {}).get("name","")
    title = f"{name1} {name2} {name3}".strip()

    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]

    if RICH_OK:
        info = Table.grid(padding=(0,2))
        info.add_column(justify="right", style=_c("text_sub"))
        info.add_column(style=_c("text_body"))
        info.add_row("Nama", f"[{_c('text_value')}]{title}[/]")
        info.add_row("Harga", f"[{_c('text_money')}]Rp {price:,}[/]")
        _print_centered_panel(info, title=f"[{_c('text_title')}]Detail Paket[/]", border_style=_c("border_info"))

        _print_centered_panel(Text(detail, style=_c("text_body")), title=f"[{_c('text_title')}]S&K MyXL[/]", border_style=_c("border_primary"))

        menu = Table(box=ROUNDED, show_header=False, padding=(0,1), expand=True)
        menu.add_column("key", justify="right", style=_c("text_number"), no_wrap=True, width=4)
        menu.add_column("desc", style=_c("text_body"))
        menu.add_row("[bold]1[/]", "Beli dengan Pulsa")
        menu.add_row("[bold]2[/]", "Beli dengan E-Wallet")
        menu.add_row("[bold]3[/]", "Bayar dengan QRIS")
        if payment_for == "REDEEM_VOUCHER":
            menu.add_row("[bold]4[/]", "Ambil sebagai bonus (jika tersedia)")
        _print_centered_panel(menu, title=f"[{_c('text_title')}]Metode Pembayaran[/]", border_style=_c("border_info"))

        choice = Prompt.ask(f"[{_c('text_sub')}]Pilih metode pembayaran")
    else:
        print("--------------------------")
        print("Detail Paket")
        print("--------------------------")
        print(f"Nama: {title}")
        print(f"Harga: Rp {price}")
        print(f"SnK MyXL:\n{detail}")
        print("--------------------------")
        print("1. Beli dengan Pulsa")
        print("2. Beli dengan E-Wallet")
        print("3. Bayar dengan QRIS")
        if payment_for == "REDEEM_VOUCHER":
            print("4. Ambil sebagai bonus (jika tersedia)")
        choice = input("Pilih metode pembayaran: ")

    if choice == '1':
        purchase_package(api_key, tokens, package_option_code)
        _print_centered_panel("Silahkan cek hasil pembelian di aplikasi MyXL.", border_style=_c("border_info"))
        pause()
        return True
    elif choice == '2':
        show_multipayment(api_key, tokens, package_option_code, token_confirmation, price)
        _print_centered_panel("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL.", border_style=_c("border_info"))
        pause()
        return True
    elif choice == '3':
        show_qris_payment(api_key, tokens, package_option_code, token_confirmation, price)
        _print_centered_panel("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL.", border_style=_c("border_info"))
        pause()
        return True
    elif choice == '4' and payment_for == "REDEEM_VOUCHER":
        settlement_bounty(
            api_key=api_key,
            tokens=tokens,
            token_confirmation=token_confirmation,
            ts_to_sign=ts_to_sign,
            payment_target=package_option_code,
            price=price,
            item_name=name2
        )
        _print_centered_panel("Redeem/bonus diproses. Cek aplikasi MyXL.", border_style=_c("border_success"))
        pause()
        return True
    else:
        _print_centered_panel("Purchase dibatalkan.", border_style=_c("border_warning"))
        return False
