# OpenConnect uses the proxy server address as the CSTP gateway when using a VLESS detour

## Summary

An AnyConnect endpoint connects successfully with `DIRECT`, but fails when its `detour` selects a VLESS outbound. Authentication and Duo Push complete. The subsequent CSTP TLS handshake fails.

The problem is an address-handling mismatch between OpenConnect and the proxy dialer. OpenConnect treats `net.Conn.RemoteAddr()` as the VPN gateway address. A VLESS connection can expose the physical proxy server address instead of the logical VPN destination.

## Versions and environment

- Reproduced with sing-box **1.14.4** on Windows.
- VPN: `https://vpn.ucsd.edu`, AnyConnect protocol.
- Authentication group: `4. 2-step secured-allthru`, with Duo Push.
- Detour: selector choosing either `DIRECT` or VLESS over TCP with Reality and `xtls-rprx-vision`.
- Fix developed on the `testing` branch, based on **v1.15.0-alpha.13**. Local source before the fix: `a6952ccf6`.
- Current fork revision: `990458fa222fe802a433a6365d54ee1d82405b4b`.
- Build toolchain: **Go 1.26.10**, GitHub Actions, Windows amd64 target.
- OpenConnect dependency in 1.14.4: `github.com/sagernet/sing-openconnect v0.1.1-0.20260929151225-cbd68c45de58`.
- OpenConnect dependency in the patched testing tree: `github.com/sagernet/sing-openconnect v0.1.1-0.20260929151226-29757281a247`.

## Reproduction

1. Configure an OpenConnect endpoint for the VPN and set its `detour` to a selector.
2. Select `DIRECT`. Complete Duo authentication. The VPN connects, including when the server redirects to a numbered gateway such as `vpn-4.ucsd.edu`.
3. Restart with the selector set to the VLESS outbound. Complete Duo authentication again.
4. Observe repeated CSTP TLS handshake failures. Setting `no_udp: true` does not resolve them.

```text
outbound/vless[LAX-ZGO]: outbound connection to 154.21.199.196:443
endpoint/openconnect[UCSD-AnyConnect]: tunnel connection failed; retrying in 1s: handshake AnyConnect CSTP TLS: remote error: tls: internal error
```

`154.21.199.196` is the VLESS server, not a UCSD VPN gateway. The VPN redirected to `137.110.0.73` in this test. The VLESS server normally listens on port `16384`; the logged `:443` is the incorrect inner connection destination.

## Cause

In `sing-openconnect`:

1. `anyconnect_auth.go` records the authenticated gateway address from `info.Conn.RemoteAddr()` in the HTTP connection trace.
2. `cstp_client.go` uses that address for the next TCP connection when it is valid and dynamic DNS is not enabled.
3. With this VLESS detour, the recorded address belongs to the proxy server. CSTP therefore connects through the proxy to the proxy server's own IP, rather than to the VPN gateway.

The failure occurs during the TLS handshake, before the CSTP CONNECT request. It is not a DTLS failure or a rejected Duo challenge. Redirection alone is not the cause: the DIRECT connection also redirects and succeeds.

## Fix

The patch stays within `protocol/openconnect`. It does not change VLESS globally.

- Resolve VPN hostnames before dialing through the detour. This includes redirected gateway hostnames.
- Wrap the detour connection in `gatewayConn`.
- Make `gatewayConn.RemoteAddr()` return the selected logical gateway IP and port, not the physical proxy peer.
- Keep the underlying connection and its I/O unchanged.
- Leave the non-detour path unchanged.

This lets OpenConnect pin the correct authenticated gateway address for CSTP. It also prevents the proxy peer address from becoming the derived DTLS destination. The patch does not hard-code a VPN gateway IP or disable certificate verification.

Changed files:

- `protocol/openconnect/client.go`
- `protocol/openconnect/detour.go`
- `protocol/openconnect/detour_test.go`

The regression tests check IPv4 and IPv6 logical gateway addresses, unchanged dial destinations and local addresses, and propagation of dial errors.

## Validation

**The patched build has been tested successfully on Windows with the VLESS detour.** The UCSD VPN connection works with `no_udp: true`, using CSTP over TLS.

DTLS remains disabled in this test configuration. This result confirms the CSTP detour fix; it does not establish DTLS interoperability. Android runtime testing is separate from the Windows result.
