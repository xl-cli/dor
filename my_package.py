from api_request import get_package, send_api_request
from ui import clear_screen, pause, console, _c, RICH_OK
from auth_helper import AuthInstance

try:
    from rich.panel import Panel
    from rich.box import ROUNDED
except ImportError:
    Panel = None
    ROUNDED = None
    RICH_OK = False

def fetch_my_packages():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        if RICH_OK and console:
            console.print(f"[{_c('text_err')}]No active user tokens found.[/]")
        else:
            print("=" * 32)
            print("No active user tokens found.")
            print("=" * 32)
        pause()
        return None

    id_token = tokens.get("id_token")
    path = "api/v8/packages/quota-details"
    payload = {
        "is_enterprise": False,
        "lang": "en",
        "family_member_id": ""
    }

    clear_screen()
    # Judul "My Packages" dalam box/panel
    if RICH_OK and Panel and ROUNDED and console:
        console.print(
            Panel(
                "Daftar paket milik Anda.",
                title="My Packages",
                border_style=_c("border_info"),
                box=ROUNDED
            )
        )
    else:
        print("=" * 32)
        print("      My Packages")
        print("=" * 32)

    res = send_api_request(api_key, path, payload, id_token, "POST")
    if res.get("status") != "SUCCESS":
        if RICH_OK and console:
            console.print(f"[{_c('text_err')}]Failed to fetch packages[/]")
            console.print(f"[{_c('text_warn')}]Response: {res}[/]")
        else:
            print("=" * 32)
            print("Failed to fetch packages")
            print("Response:", res)
            print("=" * 32)
        pause()
        return None

    quotas = res.get("data", {}).get("quotas", [])
    if not quotas:
        if RICH_OK and console:
            console.print(f"[{_c('text_warn')}]No packages found.[/]")
        else:
            print("=" * 32)
            print("No packages found.")
            print("=" * 32)
        pause()
        return None

    for num, quota in enumerate(quotas, 1):
        quota_code = quota.get("quota_code", "N/A")
        group_code = quota.get("group_code", "N/A")
        name = quota.get("name", "N/A")
        family_code = "N/A"

        if RICH_OK and console:
            console.print(f"[{_c('text_sub')}]Fetching package no. {num} details...[/]")
        else:
            print("=" * 32)
            print(f"Fetching package no. {num} details...")
            print("=" * 32)

        package_details = get_package(api_key, tokens, quota_code)
        if isinstance(package_details, dict) and "package_family" in package_details:
            family_obj = package_details["package_family"]
            family_code = family_obj.get("package_family_code", "N/A")
        else:
            family_code = "N/A"

        text = (
            f"Package {num}\n"
            f"Name        : {name}\n"
            f"Quota Code  : {quota_code}\n"
            f"Group Code  : {group_code}\n"
            f"Family Code : {family_code}"
        )

        if RICH_OK and Panel and ROUNDED and console:
            console.print(Panel(text, title=f"Paket {num}", border_style=_c("border_info"), box=ROUNDED))
        else:
            print("=" * 32)
            print(text)
            print("=" * 32)

    pause()