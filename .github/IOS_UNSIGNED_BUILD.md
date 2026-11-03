# Unsigned iOS test build

## Run

Push the workflow and this file to your fork, then open Actions → Build unsigned
iOS IPA → Run workflow. Select the core branch to build. The Apple client is
checked out at the commit pinned by `clients/apple`, including its submodules;
this deliberately does not follow upstream HEAD.

The macOS runner, Xcode version, and base bundle ID are workflow inputs. The
base bundle ID defaults to `com.cgluwxh.singbox`; set it to an explicit ID that
belongs to your Apple Developer team before building. The build derives the App
Group ID as `group.<base bundle ID>`. The pinned upstream build configuration uses an
`xcode-27` runner: GitHub-hosted images may lag behind its Swift/SDK requirements.
If Swift/SDK APIs are unavailable, use a macOS runner with a compatible Xcode
and select that installed version. Updating the client independently can also
introduce libbox interface mismatches; do not blindly switch to its latest branch.

The build uses this fork's Go version, gomobile tools, iOS CPU feature patch,
OpenConnect recovery patch, and existing Apple feature tags (including
OpenConnect and `with_low_memory`). Only iPhone/iPad arm64 is built, not Simulator.
The current core is compiled into Libbox.xcframework, then linked into SFI.
For this unsigned SFI build, native crash reporting is disabled because its SIGTRAP
handler conflicts with the embedded Go runtime during launch. No configuration files
or VPN credentials are included in the application.

## Download

Artifact `SFI-ios-arm64-unsigned` contains:

- `SFI-ios-arm64-unsigned.ipa`, a Payload ZIP, not App Store exported or signed.
- SHA256SUMS and core/client commits in build-info.txt.
- Matching archive dSYMs in `dSYMs/`, packaged as ZIPs for Windows users to retain
  alongside device `.ips` crash reports.
- Build logs and source entitlement files as a signing reference.

On failure the artifact contains the available logs, not a usable IPA. A separate
Xcode result bundle is uploaded if one was produced. A successful CI build is
not proof of successful installation or VPN operation on a physical device.

## Signing

No Apple account, certificate or provisioning profile is used by CI. The IPA
cannot be installed as-is. Re-sign the host app, its frameworks and all embedded
extensions with compatible bundle identifiers and provisioning profiles.

VPN operation requires the packet-tunnel Network Extension entitlement. Before
signing, create the derived App Group in the Apple Developer portal and enable it
for the host and every embedded extension. For a base ID of `com.example.singbox`,
register profiles for `com.example.singbox`, plus `.extension`, `.intents`,
`.fileprovider`, `.widget`, `.share`, and `.action` suffixes. Use the same
`group.com.example.singbox` entitlement in every matching profile. Keychain groups
and other capabilities must also match the profiles. The source entitlement files
are references, not ready-to-use provisioning. Changing only the host bundle ID or
stripping entitlements can result in an app that installs but cannot start its VPN.
A generic free-account IPA signing service is not guaranteed to support these
capabilities. Confirm support with your signing tool/provider before relying on it.

This is a personal test build of GPL-licensed software; preserve upstream notices
and comply with applicable source-distribution obligations if redistributing.
