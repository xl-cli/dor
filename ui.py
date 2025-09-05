import json
import os
import sys
from datetime import datetime
from api_request import get_otp, submit_otp, save_tokens, get_package, purchase_package, get_addons
from purchase_api import show_multipayment, show_qris_payment, settlement_bounty
from auth_helper import AuthInstance
from util import display_html

# ========== Rich + Theme Setup ==========
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
        print(renderable if isinstance(renderable, str) else "[Panel disabled (rich not installed)]")
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

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    if RICH_OK:
        Prompt.ask("\nTekan Enter untuk lanjut...", console=console)
    else:
        input("\nTekan Enter untuk lanjut...")

def show_banner():
    _print_centered_panel(
        Text("Dor XL by Flyxt9", style=_c("text_title")),
        title="Banner",
        border_style=_c("border_primary")
    )

def show_main_menu(number, balance, balance_expired_at):
    clear_screen()
    expired_at_dt = datetime.fromtimestamp(balance_expired_at).strftime("%Y-%m-%d %H:%M:%S")
    info = (
        f"[{_c('text_key')}]Nomor:[/{_c('text_key')}] [{_c('text_value')}]{number}[/{_c('text_value')}]\n"
        f"[{_c('text_key')}]Pulsa:[/{_c('text_key')}] [{_c('text_money')}]Rp {balance}[/{_c('text_money')}]\n"
        f"[{_c('text_key')}]Masa aktif:[/{_c('text_key')}] [{_c('text_date')}]{expired_at_dt}[/{_c('text_date')}]"
    )
    menu = (
        "[bold underline]Menu:[/]\n"
        "1. Login/Ganti akun\n"
        "2. Lihat Paket Saya\n"
        "3. Beli Paket XUT\n"
        "4. Beli Paket Berdasarkan Family Code\n"
        "5. Ganti Tema\n"
        "99. Tutup aplikasi"
    )
    _print_centered_panel(
        info + "\n\n" + menu,
        title="Main Menu",
        border_style=_c("border_info")
    )

def show_theme_menu():
    clear_screen()
    theme_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(THEMES.keys())])
    _print_centered_panel(Text("Ganti Tema\n\n" + theme_list, style=_c("text_title")), title="Theme Menu", border_style=_c("border_primary"))
    pilihan = Prompt.ask("Pilih nomor tema", console=console) if RICH_OK else input("Pilih nomor tema: ")
    try:
        idx = int(pilihan) - 1
        theme_names = list(THEMES.keys())
        if 0 <= idx < len(theme_names):
            set_theme(theme_names[idx])
            _print_centered_panel(Text(f"Tema diganti ke {theme_names[idx]}", style=_c("text_ok")), border_style=_c("border_success"))
            pause()
        else:
            _print_centered_panel(Text("Pilihan tema tidak valid.", style=_c("text_err")), border_style=_c("border_error"))
            pause()
    except Exception:
        _print_centered_panel(Text("Input tidak valid.", style=_c("text_err")), border_style=_c("border_error"))
        pause()

def show_account_menu():
    clear_screen()
    AuthInstance.load_tokens()
    users = AuthInstance.refresh_tokens
    active_user = AuthInstance.get_active_user()
    in_account_menu = True
    add_user = False
    while in_account_menu:
        clear_screen()
        if AuthInstance.get_active_user() is None or add_user:
            number, refresh_token = login_prompt(AuthInstance.api_key)
            if not refresh_token:
                _print_centered_panel(Text("Gagal menambah akun. Silahkan coba lagi.", style=_c("text_err")), border_style=_c("border_error"))
                pause()
                continue
            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens
            if add_user:
                add_user = False
            continue
        menu = Text("Akun Tersimpan:\n", style=_c("text_sub"))
        if not users or len(users) == 0:
            menu.append("Tidak ada akun tersimpan.\n", style=_c("text_warn"))
        for idx, user in enumerate(users):
            is_active = active_user and user["number"] == active_user["number"]
            active_marker = " (Aktif)" if is_active else ""
            menu.append(f"{idx + 1}. {user['number']}{active_marker}\n", style=_c("text_key"))
        menu.append(
            "\nCommand:\n"
            "0: Tambah Akun\n"
            "00: Kembali ke menu utama\n"
            "99: Hapus Akun aktif\n"
            "Masukan nomor akun untuk berganti."
        , style=_c("text_body"))
        _print_centered_panel(menu, title="Account Menu", border_style=_c("border_primary"))
        input_str = Prompt.ask("Pilihan", console=console) if RICH_OK else input("Pilihan:")
        if input_str == "00":
            in_account_menu = False
            return active_user["number"] if active_user else None
        elif input_str == "0":
            add_user = True
            continue
        elif input_str == "99":
            if not active_user:
                _print_centered_panel(Text("Tidak ada akun aktif untuk dihapus.", style=_c("text_warn")), border_style=_c("border_warning"))
                pause()
                continue
            confirm = Prompt.ask(f"Yakin ingin menghapus akun {active_user['number']}? (y/n):", console=console) if RICH_OK else input(f"Yakin ingin menghapus akun {active_user['number']}? (y/n): ")
            if confirm.lower() == 'y':
                AuthInstance.remove_refresh_token(active_user["number"])
                users = AuthInstance.refresh_tokens
                active_user = AuthInstance.get_active_user()
                _print_centered_panel(Text("Akun berhasil dihapus.", style=_c("text_ok")), border_style=_c("border_success"))
                pause()
            else:
                _print_centered_panel(Text("Penghapusan akun dibatalkan.", style=_c("text_info")), border_style=_c("border_info"))
                pause()
            continue
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            return selected_user['number']
        else:
            _print_centered_panel(Text("Input tidak valid. Silahkan coba lagi.", style=_c("text_err")), border_style=_c("border_error"))
            pause()
            continue

def show_login_menu():
    clear_screen()
    menu = (
        "[bold underline]Login ke MyXL[/]\n"
        "1. Request OTP\n"
        "2. Submit OTP\n"
        "99. Tutup aplikasi"
    )
    _print_centered_panel(menu, title="Login Menu", border_style=_c("border_primary"))

def login_prompt(api_key: str):
    clear_screen()
    _print_centered_panel(
        Text("Masukan nomor XL Prabayar (Contoh 6281234567890):", style=_c("text_body")),
        title="Login ke MyXL",
        border_style=_c("border_primary")
    )
    phone_number = Prompt.ask("Nomor", console=console) if RICH_OK else input("Nomor: ")
    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        _print_centered_panel(Text("Nomor tidak valid. Pastikan nomor diawali dengan '628' dan memiliki panjang yang benar.", style=_c("text_err")), border_style=_c("border_error"))
        return None, None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            return None, None
        _print_centered_panel(Text("OTP Berhasil dikirim ke nomor Anda.", style=_c("text_ok")), border_style=_c("border_success"))
        otp = Prompt.ask("Masukkan OTP yang telah dikirim", console=console) if RICH_OK else input("Masukkan OTP yang telah dikirim: ")
        if not otp.isdigit() or len(otp) != 6:
            _print_centered_panel(Text("OTP tidak valid. Pastikan OTP terdiri dari 6 digit angka.", style=_c("text_err")), border_style=_c("border_error"))
            pause()
            return None, None
        tokens = submit_otp(api_key, phone_number, otp)
        if not tokens:
            _print_centered_panel(Text("Gagal login. Periksa OTP dan coba lagi.", style=_c("text_err")), border_style=_c("border_error"))
            pause()
            return None, None
        _print_centered_panel(Text("Berhasil login!", style=_c("text_ok")), border_style=_c("border_success"))
        return phone_number, tokens["refresh_token"]
    except Exception as e:
        _print_centered_panel(Text("Terjadi kesalahan saat login.", style=_c("text_err")), border_style=_c("border_error"))
        return None, None

def show_package_menu(packages):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        _print_centered_panel(Text("No active user tokens found.", style=_c("text_err")), border_style=_c("border_error"))
        pause()
        return None
    in_package_menu = True
    while in_package_menu:
        clear_screen()
        menu = Text("Paket Tersedia\n", style=_c("text_title"))
        for pkg in packages:
            menu.append(f"{pkg['number']}. {pkg['name']} - Rp {pkg['price']}\n", style=_c("text_key"))
        menu.append("99. Kembali ke menu utama", style=_c("text_body"))
        _print_centered_panel(menu, title="Package Menu", border_style=_c("border_info"))
        pkg_choice = Prompt.ask("Pilih paket (nomor)", console=console) if RICH_OK else input("Pilih paket (nomor): ")
        if pkg_choice == "99":
            in_package_menu = False
            return None
        selected_pkg = next((p for p in packages if str(p["number"]) == pkg_choice), None)
        if not selected_pkg:
            _print_centered_panel(Text("Paket tidak ditemukan. Silakan masukan nomor yang benar.", style=_c("text_err")), border_style=_c("border_error"))
            continue
        is_done = show_package_details(api_key, tokens, selected_pkg["code"])
        if is_done:
            in_package_menu = False
            return None

def show_package_details(api_key, tokens, package_option_code):
    clear_screen()
    package = get_package(api_key, tokens, package_option_code)
    if not package:
        _print_centered_panel(Text("Failed to load package details.", style=_c("text_err")), border_style=_c("border_error"))
        pause()
        return False
    name2 = package.get("package_detail_variant", {}).get("name", "")
    price = package["package_option"]["price"]
    detail = display_html(package["package_option"]["tnc"])
    validity = package["package_option"]["validity"]
    name3 = package.get("package_option", {}).get("name", "")
    name1 = package.get("package_family", {}).get("name", "")
    title = f"{name1} {name2} {name3}".strip()
    item_name = f"{name2} {name3}".strip()
    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]
    benefits = package["package_option"]["benefits"]

    output = Text(f"Detail Paket\n\n", style=_c("text_title"))
    output.append(f"Nama: {title}\n", style=_c("text_key"))
    output.append(f"Harga: Rp {price}\n", style=_c("text_money"))
    output.append(f"Masa Aktif: {validity}\n", style=_c("text_date"))
    if benefits and isinstance(benefits, list):
        output.append("Benefits:\n", style=_c("text_sub"))
        for benefit in benefits:
            output.append(f" Name: {benefit['name']}\n", style=_c("text_key"))
            if "Call" in benefit['name']:
                output.append(f"  Total: {benefit['total']/60} menit\n", style=_c("text_body"))
            else:
                if benefit['total'] > 0:
                    quota = int(benefit['total'])
                    if quota >= 1_000_000_000:
                        quota_gb = quota / (1024 ** 3)
                        output.append(f"  Quota: {quota_gb:.2f} GB\n", style=_c("text_body"))
                    elif quota >= 1_000_000:
                        quota_mb = quota / (1024 ** 2)
                        output.append(f"  Quota: {quota_mb:.2f} MB\n", style=_c("text_body"))
                    elif quota >= 1_000:
                        quota_kb = quota / 1024
                        output.append(f"  Quota: {quota_kb:.2f} KB\n", style=_c("text_body"))
                    else:
                        output.append(f"  Total: {quota}\n", style=_c("text_body"))
    addons = get_addons(api_key, tokens, package_option_code)
    output.append(f"Addons:\n{json.dumps(addons, indent=2)}\n", style=_c("text_info"))
    output.append(f"SnK MyXL:\n{detail}\n", style=_c("text_body"))
    output.append(
        "\n1. Beli dengan Pulsa\n"
        "2. Beli dengan E-Wallet\n"
        "3. Bayar dengan QRIS\n", style=_c("text_ok")
    )
    if payment_for == "REDEEM_VOUCHER":
        output.append("4. Ambil sebagai bonus (jika tersedia)\n", style=_c("text_sub"))
    _print_centered_panel(output, title="Detail Paket", border_style=_c("border_info"))
    choice = Prompt.ask("Pilih metode pembayaran", console=console) if RICH_OK else input("Pilih metode pembayaran: ")
    if choice == '1':
        purchase_package(api_key, tokens, package_option_code)
        _print_centered_panel(Text("Silahkan cek hasil pembelian di aplikasi MyXL.", style=_c("text_ok")), border_style=_c("border_success"))
        pause()
        return True
    elif choice == '2':
        show_multipayment(api_key, tokens, package_option_code, token_confirmation, price, item_name)
        _print_centered_panel(Text("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL.", style=_c("text_ok")), border_style=_c("border_success"))
        pause()
        return True
    elif choice == '3':
        show_qris_payment(api_key, tokens, package_option_code, token_confirmation, price, item_name)
        _print_centered_panel(Text("Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL.", style=_c("text_ok")), border_style=_c("border_success"))
        pause()
        return True
    elif choice == '4':
        settlement_bounty(
            api_key=api_key,
            tokens=tokens,
            token_confirmation=token_confirmation,
            ts_to_sign=ts_to_sign,
            payment_target=package_option_code,
            price=price,
            item_name=name2
        )
        _print_centered_panel(Text("Bonus/voucher berhasil diambil (jika tersedia).", style=_c("text_ok")), border_style=_c("border_success"))
        pause()
        return True
    else:
        _print_centered_panel(Text("Purchase cancelled.", style=_c("text_warn")), border_style=_c("border_warning"))
        return False
    pause()
    sys.exit(0)
