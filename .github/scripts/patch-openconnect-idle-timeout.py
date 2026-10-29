#!/usr/bin/env python3
"""Patch the pinned dependency in a private copy before building (requires Go)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

MODULE = "github.com/sagernet/sing-openconnect"
OLD = '''		case cstpPacketDisconnect, cstpPacketTerminate:
			reason := renderCSTPDisconnectReason(packetBuffer.Bytes())
			packetBuffer.Release()
			s.terminate(markTerminal(E.New("server disconnected CSTP session: ", reason)))
			return'''
NEW = '''		case cstpPacketDisconnect, cstpPacketTerminate:
			payload := packetBuffer.Bytes()
			idleTimeout := len(payload) > 0 && payload[0] == 0xb0
			reason := renderCSTPDisconnectReason(payload)
			packetBuffer.Release()
			if idleTimeout {
				// Discard the expired session and authenticate again.
				s.terminate(E.Extend(ErrSessionRejected, "server disconnected CSTP session: ", reason))
			} else {
				s.terminate(markTerminal(E.New("server disconnected CSTP session: ", reason)))
			}
			return'''


def main():
    root = Path(__file__).resolve().parents[2]
    info = json.loads(subprocess.check_output(
        ["go", "mod", "download", "-json", MODULE], cwd=root, text=True))
    source = Path(info["Dir"])
    text = (source / "anyconnect_session.go").read_text(encoding="utf-8")
    if text.count(OLD) != 1:
        raise SystemExit("OpenConnect source changed; refusing to apply idle-timeout patch")
    temporary = Path(tempfile.mkdtemp(
        prefix="sing-openconnect-idle-", dir=os.environ.get("RUNNER_TEMP")))
    target = temporary / "sing-openconnect"
    shutil.copytree(source, target)
    patched = target / "anyconnect_session.go"
    patched.chmod(0o644)
    patched.write_text(text.replace(OLD, NEW), encoding="utf-8")
    subprocess.run(["gofmt", "-w", str(patched)], check=True)
    subprocess.run(["go", "mod", "edit", f"-replace={MODULE}={target.as_posix()}"],
                   cwd=root, check=True)
    print(f"Applied OpenConnect idle-timeout recovery patch: {target}")


if __name__ == "__main__":
    main()
