import sys

from api_request import *
from ui import *
from paket_xut import get_package_xut
from paket_mastif import get_package_mastif
from paket_family_group import show_company_group_menu
from my_package import fetch_my_packages
from paket_custom_family import get_packages_by_family
from auth_helper import AuthInstance

show_menu = True

def main():
    while True:
        active_user = AuthInstance.get_active_user()

        # Logged in
        if active_user is not None:
            balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
            balance_remaining = balance.get("remaining")
            balance_expired_at = balance.get("expired_at")
           
            show_main_menu(active_user["number"], balance_remaining, balance_expired_at)
            
            choice = input("Pilih menu: ").strip()
            if choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                else:
                    print("No user selected or failed to load user.")
                continue
            elif choice == "2":
                fetch_my_packages()
                continue
            elif choice == "3":
                # XUT 
                packages = get_package_xut()
                show_package_menu(packages)
                continue
            elif choice == "4":
                # mastif 
                packages = get_package_mastif()
                show_package_menu(packages)
                continue
            elif choice == "5":
                # multi operator
                show_company_group_menu(AuthInstance.api_key, active_user["tokens"])
                continue
            elif choice == "6":
                family_code = input("Enter family code (or '99' to cancel): ").strip()
                if family_code == "99":
                    continue
                get_packages_by_family(family_code)
                continue
            elif choice == "7":
                # <<< Tambahan: Ganti Tema >>>
                change_theme_menu()
                continue
            elif choice == "99":
                print("Exiting the application.")
                sys.exit(0)
            else:
                print("Invalid choice. Please try again.")
                pause()
        else:
            # Not logged in
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                print("No user selected or failed to load user.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting the application.")
    except Exception as e:
        print(f"An error occurred: {e}")