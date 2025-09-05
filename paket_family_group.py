from api_request import get_family
from ui import (
    clear_screen,
    show_package_details,
    pause,
    console,
    _c,
    RICH_OK
)

try:
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.align import Align
    from rich.box import ROUNDED
except ImportError:
    pass

# Struktur: perusahaan -> kode family group
family_codes_grouped = {
    "XL": {
        "1": {"name": "Xta Unlimited Turbo", "code": "08a3b1e6-8e78-4e45-a540-b40f06871cfe"},
        "2": {"name": "Special For You", "code": "6fda76ee-e789-4897-89fb-9114da47b805"},
        "3": {"name": "Edukasi", "code": "5d63dddd-4f90-4f4c-8438-2f005c20151f"},
        "4": {"name": "Xtra Combo Flex", "code": "4a1acab0-da54-462c-84b1-25fd0efa9318"},
        "5": {"name": "Xtra Combo Old", "code": "364d5764-77d3-41b8-9c22-575b555bf9df"},
        "6": {"name": "Bonus XCP", "code": "45c3a622-8c06-4bb1-8e56-bba1f3434600"},
        "7": {"name": "Xtra Combo Plus V1 & V2", "code": "23b71540-8785-4abe-816d-e9b4efa48f95"},
    },
    "AXIS": {
        # Tambahkan kode family AXIS jika ada
        # "1": {"name": "Axis Owsem", "code": "AXIS-CODE-1"},
    },
    # Tambahkan perusahaan/operator lain di sini
}

def show_company_group_menu(api_key: str, tokens: dict):
    in_company_menu = True
    while in_company_menu:
        clear_screen()
        keys = list(family_codes_grouped.keys())
        if RICH_OK:
            table = Table(
                title=f"[{_c('text_title')}]Daftar Operator/Perusahaan[/]",
                show_header=True, header_style=_c("text_sub"), box=ROUNDED
            )
            table.add_column("No", style=_c("text_number"), width=4)
            table.add_column("Perusahaan/Operator", style=_c("text_body"))
            for idx, perusahaan in enumerate(keys, 1):
                table.add_row(str(idx), perusahaan)
            table.add_row("99", f"[{_c('text_err')}]Kembali ke menu utama[/]")
            panel = Panel(
                Align.center(table),
                title=f"[{_c('text_title')}]Pilih Operator[/]",
                border_style=_c("border_primary"),
                box=ROUNDED
            )
            console.print(panel)
            choice = Prompt.ask(f"[{_c('text_sub')}]Pilih operator (nomor)").strip()
        else:
            print("--------------------------")
            print("Daftar Operator/Perusahaan")
            for idx, perusahaan in enumerate(keys, 1):
                print(f"{idx}. {perusahaan}")
            print("99. Kembali ke menu utama")
            print("--------------------------")
            choice = input("Pilih operator (nomor): ").strip()

        if choice == "99":
            in_company_menu = False
            return

        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(keys):
            if RICH_OK:
                console.print(f"[{_c('text_err')}]Operator tidak ditemukan. Silakan pilih nomor yang benar.[/]")
                pause()
            else:
                print("Operator tidak ditemukan. Silakan pilih nomor yang benar.")
                pause()
            continue

        perusahaan = keys[int(choice) - 1]
        show_family_group_menu(api_key, tokens, perusahaan)

def show_family_group_menu(api_key: str, tokens: dict, perusahaan: str):
    in_group_menu = True
    families = family_codes_grouped.get(perusahaan, {})
    while in_group_menu:
        clear_screen()
        if RICH_OK:
            table = Table(
                title=f"[{_c('text_title')}]Family Code Group - {perusahaan}[/]", show_header=True,
                header_style=_c("text_sub"), box=ROUNDED
            )
            table.add_column("No", style=_c("text_number"), width=4)
            table.add_column("Kategori", style=_c("text_body"))
            for key, value in families.items():
                table.add_row(key, value['name'])
            table.add_row("99", f"[{_c('text_err')}]Kembali ke menu operator[/]")
            panel = Panel(
                Align.center(table),
                title=f"[{_c('text_title')}]Pilih Family Code {perusahaan}[/]",
                border_style=_c("border_primary"),
                box=ROUNDED
            )
            console.print(panel)
            choice = Prompt.ask(f"[{_c('text_sub')}]Pilih kategori (nomor)").strip()
        else:
            print("--------------------------")
            print(f"Pilih Kategori Family Code ({perusahaan})")
            for key, value in families.items():
                print(f"{key}. {value['name']}")
            print("99. Kembali ke menu operator")
            print("--------------------------")
            choice = input("Pilih kategori (nomor): ").strip()

        if choice == "99":
            in_group_menu = False
            return

        selected_family = families.get(choice)
        if not selected_family:
            if RICH_OK:
                console.print(f"[{_c('text_err')}]Kategori tidak ditemukan. Silakan pilih nomor yang benar.[/]")
                pause()
            else:
                print("Kategori tidak ditemukan. Silakan pilih nomor yang benar.")
                pause()
            continue

        family_code = selected_family["code"]
        show_packages_by_family(api_key, tokens, family_code, perusahaan)

def show_packages_by_family(api_key: str, tokens: dict, family_code: str, perusahaan: str):
    packages = []
    data = get_family(api_key, tokens, family_code)
    if not data or not isinstance(data, dict):
        if RICH_OK:
            console.print(f"[{_c('text_err')}]Gagal mendapatkan data paket (format data tidak valid).[/]")
            pause()
        else:
            print("Gagal mendapatkan data paket (format data tidak valid).")
            pause()
        return

    package_family = data.get('package_family')
    package_variants = data.get('package_variants')
    if not package_family or not package_variants:
        if RICH_OK:
            console.print(f"[{_c('text_err')}]Respons API tidak mengandung data paket yang diperlukan.[/]")
            pause()
        else:
            print("Respons API tidak mengandung data paket yang diperlukan.")
            pause()
        return

    in_package_menu = True
    while in_package_menu:
        clear_screen()
        family_name = package_family.get("name", "Tidak diketahui")
        if RICH_OK:
            panel_title = f"[{_c('text_title')}]Family Name ({perusahaan}):[/] [{_c('text_ok')}]{family_name}[/{_c('text_ok')}]"
            console.print(Align.center(Panel(panel_title, style=_c("border_info"), box=ROUNDED)))
            table = Table(
                title=f"[{_c('text_title')}]Paket Tersedia[/]", show_header=True,
                header_style=_c("text_sub"), box=ROUNDED
            )
            table.add_column("No", style=_c("text_number"), width=4)
            table.add_column("Nama Paket", style=_c("text_body"))
            table.add_column("Harga", style=_c("text_money"))
        else:
            print("--------------------------")
            print(f"Family Name ({perusahaan}): {family_name}")
            print("Paket Tersedia")
            print("--------------------------")

        packages.clear()
        option_number = 1

        for variant in package_variants:
            for option in variant.get("package_options", []):
                option_name = option.get("name", "Tidak diketahui")
                option_price = option.get("price", "Tidak diketahui")
                option_code = option.get("package_option_code", "")
                packages.append({
                    "number": option_number,
                    "name": option_name,
                    "price": option_price,
                    "code": option_code
                })
                if RICH_OK:
                    table.add_row(str(option_number), option_name, f"Rp {option_price}")
                else:
                    print(f"{option_number}. {option_name} - Rp {option_price}")
                option_number += 1

        if RICH_OK:
            table.add_row("99", f"[{_c('text_err')}]Kembali ke menu sebelumnya[/]", "")
            panel = Panel(
                Align.center(table),
                title=f"[{_c('text_title')}]Daftar Paket {perusahaan}[/]",
                border_style=_c("border_info"),
                box=ROUNDED
            )
            console.print(panel)
            pkg_choice = Prompt.ask(f"[{_c('text_sub')}]Pilih paket (nomor)").strip()
        else:
            print("99. Kembali ke menu sebelumnya")
            pkg_choice = input("Pilih paket (nomor): ").strip()

        if pkg_choice == "99":
            in_package_menu = False
            return

        if not pkg_choice.isdigit():
            if RICH_OK:
                console.print(f"[{_c('text_err')}]Masukan harus berupa angka.[/]")
                pause()
            else:
                print("Masukan harus berupa angka.")
                pause()
            continue

        pkg_choice_int = int(pkg_choice)
        selected_pkg = next((p for p in packages if p["number"] == pkg_choice_int), None)
        if not selected_pkg:
            if RICH_OK:
                console.print(f"[{_c('text_err')}]Paket tidak ditemukan. Silakan masukan nomor yang benar.[/]")
                pause()
            else:
                print("Paket tidak ditemukan. Silakan masukan nomor yang benar.")
                pause()
            continue

        is_done = show_package_details(api_key, tokens, selected_pkg["code"])
        if is_done:
            in_package_menu = False
            return

# Untuk memulai menu, panggil: show_company_group_menu(api_key, tokens)