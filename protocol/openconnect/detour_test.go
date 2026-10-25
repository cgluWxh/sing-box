package openconnect

import (
	"context"
	"errors"
	"net"
	"testing"

	M "github.com/sagernet/sing/common/metadata"
)

type testProxyDialer struct {
	conn net.Conn
	err error
	destination M.Socksaddr
}

func (d *testProxyDialer) DialContext(_ context.Context, _ string, destination M.Socksaddr) (net.Conn, error) {
	d.destination = destination
	return d.conn, d.err
}

func (d *testProxyDialer) ListenPacket(context.Context, M.Socksaddr) (net.PacketConn, error) {
	return nil, errors.New("not implemented")
}

type testProxyConn struct {
	net.Conn
}

func (c *testProxyConn) RemoteAddr() net.Addr {
	return &net.TCPAddr{IP: net.ParseIP("154.21.199.196"), Port: 16384}
}

func TestGatewayDialerRemoteAddress(t *testing.T) {
	for _, address := range []string{"137.110.0.73:443", "[2001:db8::1]:443"} {
		t.Run(address, func(t *testing.T) {
			client, server := net.Pipe()
			defer server.Close()
			proxy := &testProxyDialer{conn: &testProxyConn{Conn: client}}
			d := &gatewayDialer{Dialer: proxy}
			destination := M.ParseSocksaddr(address)
			conn, err := d.DialContext(context.Background(), "tcp", destination)
			if err != nil {
				t.Fatal(err)
			}
			defer conn.Close()
			if conn.RemoteAddr().String() != address {
				t.Fatalf("gateway address = %s; want %s", conn.RemoteAddr(), address)
			}
			if proxy.destination != destination {
				t.Fatalf("dial destination was changed: %s", proxy.destination)
			}
			// This mirrors the address pinning performed after authentication.
			host, _, err := net.SplitHostPort(conn.RemoteAddr().String())
			if err != nil || net.ParseIP(host) == nil {
				t.Fatalf("gateway cannot be pinned: %s, %v", host, err)
			}
			if conn.LocalAddr().String() != client.LocalAddr().String() {
				t.Fatal("local address was changed")
			}
		})
	}
}

func TestGatewayDialerError(t *testing.T) {
	want := errors.New("proxy dial failed")
	d := &gatewayDialer{Dialer: &testProxyDialer{err: want}}
	conn, err := d.DialContext(context.Background(), "tcp", M.ParseSocksaddr("137.110.0.73:443"))
	if conn != nil || !errors.Is(err, want) {
		t.Fatalf("got %v, %v; want nil, original error", conn, err)
	}
}
