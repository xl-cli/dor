from api_request import get_family
from auth_helper import AuthInstance
from ui import pause

FAMILY_CODES = [
    "6bcc96f4-f196-4e8f-969f-e45a121d21bd",
    "4889cc43-55c9-47dd-8f7e-d3ac9fae6022",
    # "kode-family-3",
]

def get_package_mastif():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        print("No active user tokens found.")
        pause()
        return None

    packages = []
    counter = 1

    for family_code in FAMILY_CODES:
        data = get_family(api_key, tokens, family_code)
        for variant in data.get("package_variants", []):
            for option in variant.get("package_options", []):
                packages.append({
                    "number": counter,
                    "name": option.get("name"),
                    "price": option.get("price"),
                    "code": option.get("package_option_code"),
                    "family_code": family_code
                })
                counter += 1
    return packages