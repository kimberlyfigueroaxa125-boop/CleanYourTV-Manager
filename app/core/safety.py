from __future__ import annotations

# Packages commonly involved in TV input / tuner functionality on the target
# MediaTek firmware. This is a conservative protection list, not a universal
# package map. Device-specific verification is still required.
PROTECTED_PACKAGES = frozenset(
    {
        "com.mediatek.tvinput",
        "com.mediatek.wwtv.setupwizard",
        "com.mediatek.wwtv.webview",
        "com.mediatek.wwtv.tvcenter",
    }
)


def is_protected(package_name: str) -> bool:
    return package_name.strip() in PROTECTED_PACKAGES


def validate_disable_request(package_name: str) -> None:
    package = package_name.strip()
    if not package:
        raise ValueError("Package name cannot be empty")
    if is_protected(package):
        raise PermissionError(
            f"Refusing to disable protected TV package: {package}. "
            "Live TV / tuner functionality must be preserved by default."
        )
