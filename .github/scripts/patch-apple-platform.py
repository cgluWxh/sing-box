#!/usr/bin/env python3
"""Adapt the pinned Apple client to the current libbox platform protocol."""
import sys
from pathlib import Path

ANCHOR = "    public func usePlatformBridge() -> Bool {"
SIDEBAR_PAGE_CONTENT = "    private func sidebarPageContent(for page: NavigationPage, remoteControlInToolbar: Bool) -> some View {"
SIDEBAR_PAGE_CONTENT_AVAILABLE = "    @available(iOS 16.0, *)\n" + SIDEBAR_PAGE_CONTENT
PATCH = '''    // Compatibility with the current core: platform AutoRedirect is Linux-only.
    public func usePlatformAutoRedirect() -> Bool {
        return false
    }

    public func createAutoRedirect(
        _ options: Data?, handler: (any LibboxAutoRedirectHandlerProtocol)?
    ) throws -> any LibboxAutoRedirectSessionProtocol {
        throw NSError(domain: "ExtensionPlatformInterface", code: -1, userInfo: [
            NSLocalizedDescriptionKey: "auto redirect is not supported on Apple platforms",
        ])
    }

'''


def patch_source(text: str) -> str:
    methods = ("func usePlatformAutoRedirect(", "func createAutoRedirect(")
    if PATCH in text:
        return text
    if any(method in text for method in methods):
        raise ValueError("Apple AutoRedirect implementation changed; review patch")
    if text.count(ANCHOR) != 1:
        raise ValueError("Apple platform interface changed; expected one bridge anchor")
    return text.replace(ANCHOR, PATCH + ANCHOR)


def patch_main_view(text: str) -> str:
    if SIDEBAR_PAGE_CONTENT_AVAILABLE in text:
        return text
    if text.count(SIDEBAR_PAGE_CONTENT) != 1:
        raise ValueError("Apple MainView changed; expected one sidebarPageContent declaration")
    return text.replace(SIDEBAR_PAGE_CONTENT, SIDEBAR_PAGE_CONTENT_AVAILABLE)


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("clients/apple")
    path = root / "Library/Network/ExtensionPlatformInterface.swift"
    text = path.read_text(encoding="utf-8")
    result = patch_source(text)
    if result != text:
        path.write_text(result, encoding="utf-8")

    main_view_path = root / "SFI/MainView.swift"
    text = main_view_path.read_text(encoding="utf-8")
    result = patch_main_view(text)
    if result != text:
        main_view_path.write_text(result, encoding="utf-8")
    print("Apple platform interface and iOS availability compatibility ready")


if __name__ == "__main__":
    main()
