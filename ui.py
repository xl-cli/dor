import json
import os
import sys
from datetime import datetime
from api_request import get_otp, submit_otp, save_tokens, get_package, purchase_package, get_addons
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

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    if RICH_OK:
        console.print("\n[dim]Tekan Enter untuk lanjut...[/]", end="")
        input()
    else:
        input("\nTekan Enter untuk lanjut...")

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

# ... [fungsi lain tetap seperti di file anda] ...

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
    validity = package["package_option"].get("validity", "")

    benefits = package["package_option"].get("benefits", [])
    addons = get_addons(api_key, tokens, package_option_code)

    if RICH_OK:
        info = Table.grid(padding=(0,2))
        info.add_column(justify="right", style=_c("text_sub"))
        info.add_column(style=_c("text_body"))
        info.add_row("Nama", f"[{_c('text_value')}]{title}[/]")
        info.add_row("Harga", f"[{_c('text_money')}]Rp {price:,}[/]")
        info.add_row("Masa Aktif", f"[{_c('text_date')}]{validity}[/]")
        _print_centered_panel(info, title=f"[{_c('text_title')}]Detail Paket[/]", border_style=_c("border_info"))

        _print_centered_panel(Text(detail, style=_c("text_body")), title=f"[{_c('text_title')}]S&K MyXL[/]", border_style=_c("border_primary"))

        # Benefits Rich Table
        if benefits and isinstance(benefits, list):
            benefit_table = Table(box=ROUNDED, show_header=True, header_style=_c("text_sub"), expand=True)
            benefit_table.add_column("Benefit", style=_c("text_body"))
            benefit_table.add_column("Detail", style=_c("text_body"))
            for benefit in benefits:
                name_b = benefit.get("name", "-")
                if "Call" in name_b:
                    value = f"{benefit.get('total',0)/60:.0f} menit"
                else:
                    quota = int(benefit.get("total", 0))
                    if quota >= 1_000_000_000:
                        quota_gb = quota / (1024 ** 3)
                        value = f"{quota_gb:.2f} GB"
                    elif quota >= 1_000_000:
                        quota_mb = quota / (1024 ** 2)
                        value = f"{quota_mb:.2f} MB"
                    elif quota >= 1_000:
                        quota_kb = quota / 1024
                        value = f"{quota_kb:.2f} KB"
                    elif quota > 0:
                        value = f"{quota}"
                    else:
                        value = "-"
                benefit_table.add_row(name_b, value)
            _print_centered_panel(benefit_table, title=f"[{_c('text_title')}]Benefits[/]", border_style=_c("border_success"))

        # Addons Rich Panel
        if addons:
            addon_text = Text(json.dumps(addons, indent=2), style=_c("text_body"))
            _print_centered_panel(addon_text, title=f"[{_c('text_title')}]Addons[/]", border_style=_c("border_primary"))

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
        print(f"Nama: {title}")
        print(f"Harga: Rp {price}")
        print(f"Masa Aktif: {validity}")
        print("--------------------------")
        if benefits and isinstance(benefits, list):
            print("Benefits:")
            for benefit in benefits:
                print("--------------------------")
                print(f" Name: {benefit.get('name', '-')}")
                if "Call" in benefit.get("name", ""):
                    print(f"  Total: {benefit.get('total',0)/60} menit")
                else:
                    quota = int(benefit.get("total", 0))
                    if quota > 0:
                        if quota >= 1_000_000_000:
                            quota_gb = quota / (1024 ** 3)
                            print(f"  Quota: {quota_gb:.2f} GB")
                        elif quota >= 1_000_000:
                            quota_mb = quota / (1024 ** 2)
                            print(f"  Quota: {quota_mb:.2f} MB")
                        elif quota >= 1_000:
                            quota_kb = quota / 1024
                            print(f"  Quota: {quota_kb:.2f} KB")
                        else:
                            print(f"  Total: {quota}")
        print("--------------------------")
        print(f"Addons:\n{json.dumps(addons, indent=2)}")
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

# ... [fungsi lain tetap seperti di file anda] ...
