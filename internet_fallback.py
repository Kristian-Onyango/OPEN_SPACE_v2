"""
Layer 6 — Internet Egress & Fallback Gateway
===========================================

Responsibilities:
- Transparent internet egress
- Automatic fallback routing
- Session-aware forwarding
- No user interaction
- No persistence logic

Consumes:
- Layer 3 (resolution / services)
- Layer 4 (delivery attempt / messaging)
- Layer 5 (authoritative snapshots, policies)

This layer MAY touch the public internet.
"""

import socket
import threading
import time
from typing import Dict, Tuple, Optional

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443

SOCKET_TIMEOUT = 5.0
MAX_RETRIES = 2

BUFFER_SIZE = 8192

# ---------------------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------------------

class GatewaySession:
    """
    Tracks a single client → internet session.
    """

    def __init__(self, client_addr: Tuple[str, int], target: Tuple[str, int]):
        self.client_addr = client_addr
        self.target = target
        self.created_at = time.time()
        self.last_activity = time.time()
        self.bytes_up = 0
        self.bytes_down = 0

# ---------------------------------------------------------------------
# GATEWAY CORE
# ---------------------------------------------------------------------


class InternetGateway:
    """
    Layer 6 Gateway Core.

    Listens locally, forwards externally.
    Acts as a transparent proxy / NAT-equivalent.
    """

    def __init__(self, listen_ip:str = "0.0.0.0", listen_port: int = 8080):
        self.listen_ip = listen_ip
        self.listen_port = listen_port

        self.sessions: Dict[Tuple[str, int], GatewaySession] = {}
        self._lock = threading.Lock()

        self.running = False


    # -----------------------------------------------------------------
    # START / STOP
    # -----------------------------------------------------------------

    def start(self):
        """
        Start the gateway listener.
        """
        self.running = True
        thread = threading.Thread(target=self._listen_loop, daemon=True)
        thread.start()

        print(f"[L6] Gateway listening on {self.listen_ip}:{self.listen_port}")

    def stop(self):
        self.running = False

# -----------------------------------------------------------------
# LISTENER
# -----------------------------------------------------------------
    def _listen_loop(self):
        """
        Accept incoming client connections.
        """
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((self.listen_ip, self.listen_port))
        server_sock.listen(128)

        while self.running:
            try:
                client_sock, client_addr = server_sock.accept()
                handler = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True
                )
                handler.start()
            except Exception as e:
                print(f"[L6] Listener error: {e}")



# -----------------------------------------------------------------
# CLIENT HANDLING
# -----------------------------------------------------------------

    def _handle_client(self, client_sock: socket.socket, client_addr):
        """
        Handle one client connection.
        """
        client_sock.settimeout(SOCKET_TIMEOUT) # the socket will raise a timeout exception instead of blocking forever If the client stops responding

        try:
            initial_data = client_sock.recv(BUFFER_SIZE)
            if not initial_data:
                client_sock.close()
                return

            #Resolve destination (VERY naive MVP)
            target = self._extract_target(initial_data)
            if not target:
                client_sock.close()
                return

            session = GatewaySession(client_addr, target)

            with self._lock:
                self.sessions[client_addr] = session

            self._forward_session(client_sock, session, initial_data)

        except Exception as e:
            print(f"[L6] Client error {client_addr}: {e}")

        finally:
            client_sock.close()
            with self._lock:
                self.sessions.pop(client_addr, None)

# -----------------------------------------------------------------
# FORWARDING
# -----------------------------------------------------------------

    def _forward_session(
            self,
            client_sock: socket.socket,
            session: GatewaySession,
            first_payload: bytes
    ):
        """
        Forward traffic between client and internet.
        """
        target_ip, target_port = session.target

        try:
            upstream = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            upstream.settimeout(SOCKET_TIMEOUT)
            upstream.connect((target_ip, target_port))

            # Send initial payload
            upstream.sendall(first_payload)

            # Bidirectional relay
            threading.Thread(
                target=self._relay,
                args=(client_sock, upstream, session, True),
                daemon=True
            ).start()

            self._relay(upstream, client_sock, session, False)

        except Exception as e:
            print(f"[L6] Upstream error {session.target}: {e}")


    def _relay(
            self,
            source: socket.socket,
            destination: socket.socket,
            session: GatewaySession,
            upstream: bool
    ):
        """
        Relay bytes between sockets.
        """
        try:
            while True:
                data = source.recv(BUFFER_SIZE)
                if not data:
                    break

                destination.sendall(data)

                session.last_activity = time.time()
                if upstream:
                    session.bytes_up += len(data)
                else:
                    session.bytes_down += len(data)

        except Exception:
            pass

# -----------------------------------------------------------------
# TARGET RESOLUTION (MVP)
# -----------------------------------------------------------------

    def _extract_target(self, payload: bytes) -> Optional[Tuple[str, int]]:
        """
        Extract target host from HTTP payload.
        This is intentionally naive and will be replaced later.
        """
        try:
            text = payload.decode(errors="ignore")
            for line in text.split("\r\n"):
                if line.lower().startswith("host:"):
                    host = line.split(":", 1)[1].strip()
                    if ":" in host:
                        h, p = host.split(":")
                        return h, int(p)
                    return host, DEFAULT_HTTP_PORT
        except Exception:
            return None

        return None