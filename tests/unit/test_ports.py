import socket

from src.services import ports


def _occupy_port() -> tuple[socket.socket, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    return sock, sock.getsockname()[1]


def test_probe_ports_marks_conflict_when_port_in_use():
    sock, port = _occupy_port()
    try:
        mapping = ports.probe_ports([port], host="127.0.0.1")[0]
        assert mapping.status == "CONFLICT"
        assert mapping.local_port == port
    finally:
        sock.close()


def test_suggest_remap_finds_new_block_when_default_conflicts():
    sockets: list[socket.socket] = []
    base_port = 40000
    for offset in range(3):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", base_port + offset))
        sock.listen(1)
        sockets.append(sock)

    try:
        mappings = ports.suggest_remap([base_port, base_port + 1, base_port + 2], host="127.0.0.1", step=1, attempts=50)
        assert mappings, "expected a remap suggestion"
        assert all(mapping.status == "MAPPED" for mapping in mappings)
        # Ensure we moved away from the blocked base ports
        assert all(mapping.local_port >= base_port + 1 for mapping in mappings)
    finally:
        for sock in sockets:
            sock.close()


def test_all_available_reports_false_on_conflict():
    sock, port = _occupy_port()
    try:
        mappings = ports.probe_ports([port, port + 1], host="127.0.0.1")
        assert not ports.all_available(mappings)
    finally:
        sock.close()
