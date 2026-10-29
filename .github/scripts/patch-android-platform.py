"""Adapt the pinned SFA platform interface to the current core for VPN testing.

Platform AutoRedirect is not implemented by this pinned client. Explicitly
report false so the core does not attempt to use a missing platform session.
"""
from pathlib import Path


def patch(text):
    anchor = 'interface PlatformInterfaceWrapper : PlatformInterface {\n'
    methods = ('override fun usePlatformAutoRedirect(', 'override fun createAutoRedirect(')
    present = [method in text for method in methods]
    if all(present):
        return text
    if any(present) or text.count(anchor) != 1:
        raise ValueError('SFA platform interface changed; review compatibility patch')
    addition = '''    override fun usePlatformAutoRedirect(): Boolean = false

    override fun createAutoRedirect(
        options: ByteArray?,
        handler: io.nekohasekai.libbox.AutoRedirectHandler?,
    ): io.nekohasekai.libbox.AutoRedirectSession {
        error("android: platform auto-redirect is not supported by this test client")
    }

'''
    return text.replace(anchor, anchor + addition)


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[2]
    path = root / 'clients/android/app/src/main/java/io/nekohasekai/sfa/bg/PlatformInterfaceWrapper.kt'
    original = path.read_text(encoding='utf-8')
    path.write_text(patch(original), encoding='utf-8')
    print('SFA compatibility patch applied: usePlatformAutoRedirect=false, createAutoRedirect=unsupported')
