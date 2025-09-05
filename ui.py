import json
import os
import sys
from datetime import datetime
from api_request import get_otp, submit_otp, save_tokens, get_package, purchase_package, get_addons
from purchase_api import show_multipayment, show_qris_payment, settlement_bounty
from auth_helper import AuthInstance
from util import display_html

from rich.console import Console
from rich.theme import Theme
from rich.table import Table
from rich.panel import Panel

# Definisikan tema custom
custom_theme = Theme({
    "banner": "bold magenta",
    "menu": "bold cyan",
    "highlight": "bold yellow",
    "error": "bold red",
    "info": "green",
    "input": "bold white",
})

console = Console(theme=custom_theme)

def clear_screen():
    console.print("clearing screen...", style="info")
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    console.print("\nTekan Enter untuk lanjut...", style="input")
    input()

def show_banner():
    console.print(Panel("[bold magenta]Dor XL by Flyxt9[/bold magenta]", expand=False, style="banner"))

def show_main_menu(number, balance, balance_expired_at):
    clear_screen()
    phone_number = number
    remaining_balance = balance
    expired_at = balance_expired_at
    expired_at_dt = datetime.fromtimestamp(expired_at).strftime("%Y-%m-%d %H:%M:%S")

    console.print(Panel(f"[menu][bold]Informasi Akun[/bold]\nNomor: [highlight]{phone_number}[/]\nPulsa: [highlight]Rp {remaining_balance}[/]\nMasa aktif: [highlight]{expired_at_dt}[/][/menu]", style="menu"))
    menu_text = (
        "[menu]Menu:\n"
        "1. Login/Ganti akun\n"
        "2. Lihat Paket Saya\n"
        "3. Beli Paket XUT\n"
        "4. Beli Paket Berdasarkan Family Code\n"
        "99. Tutup aplikasi[/menu]"
    )
    console.print(Panel(menu_text, style="menu"))

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
                console.print("Gagal menambah akun. Silahkan coba lagi.", style="error")
                pause()
                continue

            AuthInstance.add_refresh_token(int(number), refresh_token)
            AuthInstance.load_tokens()
            users = AuthInstance.refresh_tokens

            if add_user:
                add_user = False
            continue

        console.print("[menu]Akun Tersimpan:[/menu]", style="menu")
        if not users or len(users) == 0:
            console.print("Tidak ada akun tersimpan.", style="info")

        for idx, user in enumerate(users):
            is_active = active_user and user["number"] == active_user["number"]
            active_marker = "[highlight] (Aktif)[/highlight]" if is_active else ""
            console.print(f"{idx + 1}. {user['number']}{active_marker}")

        console.print("[menu]Command:\n0: Tambah Akun\n00: Kembali ke menu utama\n99: Hapus Akun aktif\nMasukan nomor akun untuk berganti.[/menu]", style="menu")
        input_str = console.input("[input]Pilihan: [/input]")
        if input_str == "00":
            in_account_menu = False
            return active_user["number"] if active_user else None
        elif input_str == "0":
            add_user = True
            continue
        elif input_str == "99":
            if not active_user:
                console.print("Tidak ada akun aktif untuk dihapus.", style="error")
                pause()
                continue
            confirm = console.input(f"Yakin ingin menghapus akun {active_user['number']}? (y/n): ")
            if confirm.lower() == 'y':
                AuthInstance.remove_refresh_token(active_user["number"])
                users = AuthInstance.refresh_tokens
                active_user = AuthInstance.get_active_user()
                console.print("Akun berhasil dihapus.", style="info")
                pause()
            else:
                console.print("Penghapusan akun dibatalkan.", style="info")
                pause()
            continue
        elif input_str.isdigit() and 1 <= int(input_str) <= len(users):
            selected_user = users[int(input_str) - 1]
            return selected_user['number']
        else:
            console.print("Input tidak valid. Silahkan coba lagi.", style="error")
            pause()
            continue

def show_login_menu():
    clear_screen()
    show_banner()
    menu_text = (
        "[menu]Login ke MyXL\n"
        "1. Request OTP\n"
        "2. Submit OTP\n"
        "99. Tutup aplikasi[/menu]"
    )
    console.print(Panel(menu_text, style="menu"))

def login_prompt(api_key: str):
    clear_screen()
    show_banner()
    console.print("[menu]Masukan nomor XL Prabayar (Contoh 6281234567890):[/menu]", style="menu")
    phone_number = console.input("[input]Nomor: [/input]")

    if not phone_number.startswith("628") or len(phone_number) < 10 or len(phone_number) > 14:
        console.print("Nomor tidak valid. Pastikan nomor diawali dengan '628' dan memiliki panjang yang benar.", style="error")
        return None

    try:
        subscriber_id = get_otp(phone_number)
        if not subscriber_id:
            return None
        console.print("[info]OTP Berhasil dikirim ke nomor Anda.[/info]", style="info")

        otp = console.input("[input]Masukkan OTP yang telah dikirim: [/input]")
        if not otp.isdigit() or len(otp) != 6:
            console.print("OTP tidak valid. Pastikan OTP terdiri dari 6 digit angka.", style="error")
            pause()
            return None

        tokens = submit_otp(api_key, phone_number, otp)
        if not tokens:
            console.print("Gagal login. Periksa OTP dan coba lagi.", style="error")
            pause()
            return None

        console.print("[info]Berhasil login![/info]", style="info")

        return phone_number, tokens["refresh_token"]
    except Exception as e:
        return None, None

def show_package_menu(packages):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        console.print("No active user tokens found.", style="error")
        pause()
        return None

    in_package_menu = True
    while in_package_menu:
        clear_screen()
        show_banner()
        console.print("[menu]Paket Tersedia[/menu]", style="menu")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Nomor", style="highlight", width=8)
        table.add_column("Nama Paket", style="menu")
        table.add_column("Harga", style="highlight")
        for pkg in packages:
            table.add_row(str(pkg['number']), pkg['name'], f"Rp {pkg['price']}")
        console.print(table)
        console.print("[menu]99. Kembali ke menu utama[/menu]", style="menu")
        pkg_choice = console.input("[input]Pilih paket (nomor): [/input]")
        if pkg_choice == "99":
            in_package_menu = False
            return None
        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)
        if not selected_pkg:
            console.print("Paket tidak ditemukan. Silakan masukan nomor yang benar.", style="error")
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
        console.print("Failed to load package details.", style="error")
        pause()
        return False
    name2 = package.get("package_detail_variant", "").get("name","")
    price = package["package_option"]["price"]
    detail = display_html(package["package_option"]["tnc"])
    validity = package["package_option"]["validity"]

    name3 = package.get("package_option", {}).get("name","")
    name1 = package.get("package_family", {}).get("name","")

    title = f"{name1} {name2} {name3}".strip()
    item_name = f"{name2} {name3}".strip()

    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]

    info_text = (
        f"[highlight]Nama:[/] {title}\n"
        f"[highlight]Harga:[/] Rp {price}\n"
        f"[highlight]Masa Aktif:[/] {validity}\n"
    )
    console.print(Panel(info_text, style="menu"))

    # Benefits dalam box
    benefits = package["package_option"]["benefits"]
    if benefits and isinstance(benefits, list):
        benefits_text = ""
        for benefit in benefits:
            b_text = f"Name: {benefit['name']}\n"
            if "Call" in benefit['name']:
                b_text += f"  Total: {benefit['total']/60} menit\n"
            else:
                if benefit['total'] > 0:
                    quota = int(benefit['total'])
                    if quota >= 1_000_000_000:
                        quota_gb = quota / (1024 ** 3)
                        b_text += f"  Quota: {quota_gb:.2f} GB\n"
                    elif quota >= 1_000_000:
                        quota_mb = quota / (1024 ** 2)
                        b_text += f"  Quota: {quota_mb:.2f} MB\n"
                    elif quota >= 1_000:
                        quota_kb = quota / 1024
                        b_text += f"  Quota: {quota_kb:.2f} KB\n"
                    else:
                        b_text += f"  Total: {quota}\n"
            benefits_text += b_text + "\n"
        console.print(Panel(benefits_text.strip(), title="[menu]Benefits[/menu]", style="menu"))

    addons = get_addons(api_key, tokens, package_option_code)
    console.print(f"[menu]Addons:[/menu]\n{json.dumps(addons, indent=2)}", style="menu")
    console.print(f"[highlight]SnK MyXL:[/highlight]\n{detail}", style="menu")

    payment_text = (
        "[menu]1. Beli dengan Pulsa\n"
        "2. Beli dengan E-Wallet\n"
        "3. Bayar dengan QRIS\n"
    )
    if payment_for == "REDEEM_VOUCHER":
        payment_text += "4. Ambil sebagai bonus (jika tersedia)\n"

    console.print(Panel(payment_text, style="menu"))
    choice = console.input("[input]Pilih metode pembayaran: [/input]")

    if choice == '1':
        purchase_package(api_key, tokens, package_option_code)
        console.print("[info]Silahkan cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.[/info]", style="info")
        input()
        return True
    elif choice == '2':
        show_multipayment(api_key, tokens, package_option_code, token_confirmation, price, item_name)
        console.print("[info]Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.[/info]", style="info")
        input()
        return True
    elif choice == '3':
        show_qris_payment(api_key, tokens, package_option_code, token_confirmation, price, item_name)
        console.print("[info]Silahkan lakukan pembayaran & cek hasil pembelian di aplikasi MyXL. Tekan Enter untuk kembali.[/info]", style="info")
        input()
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
    else:
        console.print("Purchase cancelled.", style="error")
        return False
    pause()
    sys.exit(0)
