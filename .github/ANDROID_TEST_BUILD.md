# Android test APK

Run **Actions → Build Android test APK → Run workflow** on the patched branch.
No local SDK, release signing secrets, or configuration credentials are required.

The workflow builds the current core (including the OpenConnect fix) for
Android arm64 only, prepares libbox.aar, checks out the pinned clients/android submodule,
and runs `:app:assembleOtherDebug`. Download the final artifact named
`SFA-android-debug-openconnect-fix`, not the intermediate libbox artifacts.
Only an arm64-v8a APK is generated; other ABI splits and the universal APK are disabled.
Minimum supported Android version is 7.0 (API 24).

APKs use Gradle's debug signing configuration and the upstream application ID.
They cannot replace an officially signed SFA installation. Back up configuration
before uninstalling the official app. No user configuration or VPN credentials
are embedded in these APKs.

The debug keystore is reused via Actions cache under
`sfa-test-debug-keystore-v1`. Cache eviction, branch cache visibility or deletion
can cause a new certificate to be generated, preventing upgrades over a previous
test build. This is convenient test signing, not durable release signing. For
long-term updates, keep a fixed keystore in GitHub Secrets instead. Debug APKs
are debuggable: use them for testing only.

Only manual workflow_dispatch is enabled. Windows build workflows are unchanged.
Actual Go/Android compilation and APK installation must be verified in Actions
and on a device; local validation only checks workflow structure.
