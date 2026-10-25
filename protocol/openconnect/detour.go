package openconnect

import (
	"context"
	"net"

	M "github.com/sagernet/sing/common/metadata"
	N "github.com/sagernet/sing/common/network"
)

// gatewayDialer exposes the VPN gateway, not the physical proxy peer, to
// sing-openconnect. Its authentication and CSTP transports use RemoteAddr to
// pin the authenticated gateway and to derive the DTLS destination.
// A resolving dialer must sit outside this wrapper so destination is an IP.
// Keep this local to OpenConnect: other protocols may need the physical peer.
type gatewayDialer struct {
	N.Dialer
}

func (d *gatewayDialer) DialContext(ctx context.Context, network string, destination M.Socksaddr) (net.Conn, error) {
	conn, err := d.Dialer.DialContext(ctx, network, destination)
	if err != nil {
		return nil, err
	}
	return &gatewayConn{Conn: conn, destination: destination}, nil
}

type gatewayConn struct {
	net.Conn
	destination M.Socksaddr
}

func (c *gatewayConn) RemoteAddr() net.Addr {
	return c.destination
}
