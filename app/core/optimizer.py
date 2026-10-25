from __future__ import annotations

from dataclasses import dataclass

from .adb import AdbClient, AdbError


@dataclass(frozen=True)
class OptimizationResult:
    changed: tuple[str, ...]
    skipped: tuple[str, ...]


class OptimizerError(RuntimeError):
    pass


ANIMATION_KEYS = (
    "window_animation_scale",
    "transition_animation_scale",
    "animator_duration_scale",
)


class TvOptimizer:
    """Conservative, reversible Android TV performance tweaks.

    This deliberately avoids package disabling. TV input, launcher, Wi-Fi,
    tuner and vendor hardware services are therefore left untouched.
    """

    def __init__(self, client: AdbClient) -> None:
        self.client = client

    def read_animation_scales(self) -> dict[str, str]:
        values: dict[str, str] = {}
        for key in ANIMATION_KEYS:
            try:
                value = self.client.shell(f"settings get global {key}")
            except AdbError:
                value = "null"
            values[key] = value.strip() or "null"
        return values

    def apply_fast_ui(self) -> OptimizationResult:
        changed: list[str] = []
        skipped: list[str] = []
        for key in ANIMATION_KEYS:
            try:
                self.client.shell(f"settings put global {key} 0")
                changed.append(f"{key}=0")
            except AdbError as exc:
                skipped.append(f"{key}: {exc}")
        return OptimizationResult(tuple(changed), tuple(skipped))

    def restore_ui(self, values: dict[str, str] | None = None) -> OptimizationResult:
        values = values or {key: "1.0" for key in ANIMATION_KEYS}
        changed: list[str] = []
        skipped: list[str] = []
        for key in ANIMATION_KEYS:
            value = values.get(key, "1.0").strip()
            if value in {"", "null", "None"}:
                value = "1.0"
            try:
                self.client.shell(f"settings put global {key} {value}")
                changed.append(f"{key}={value}")
            except AdbError as exc:
                skipped.append(f"{key}: {exc}")
        return OptimizationResult(tuple(changed), tuple(skipped))

    def trim_caches(self) -> str:
        try:
            return self.client.shell("pm trim-caches 512M")
        except AdbError as exc:
            raise OptimizerError(str(exc)) from exc

    def compile_apps(self) -> str:
        """Ask Android to optimize installed packages using its own compiler."""
        try:
            return self.client.shell("cmd package compile -m speed-profile -a", timeout=180)
        except AdbError as exc:
            raise OptimizerError(str(exc)) from exc

    def optimize(self, compile_apps: bool = True, trim_cache: bool = True) -> list[str]:
        messages: list[str] = []
        result = self.apply_fast_ui()
        messages.extend(result.changed)
        if result.skipped:
            messages.extend(f"SKIPPED: {item}" for item in result.skipped)
        if trim_cache:
            messages.append(self.trim_caches() or "Cache trim completed")
        if compile_apps:
            messages.append(self.compile_apps() or "Package compilation completed")
        return messages
