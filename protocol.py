"""
Protocolo de comunicacao TCP para o sistema de codificacao/decodificacao.

Formato das mensagens:
    [4 bytes big-endian: tamanho do payload][payload JSON em UTF-8]

Funcoes:
    send_message(sock, data) - envia um dict como mensagem JSON
    recv_message(sock) - recebe e retorna um dict da mensagem JSON
"""

import json
import struct
import socket


HEADER_FORMAT = ">I"  # unsigned int, 4 bytes, big-endian
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


def send_message(sock: socket.socket, data: dict) -> None:
    """
    Serializa um dicionario como JSON e envia pelo socket com length-prefix.

    Args:
        sock: Socket TCP conectado.
        data: Dicionario a ser enviado.
    """
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    header = struct.pack(HEADER_FORMAT, len(payload))
    sock.sendall(header + payload)


def recv_message(sock: socket.socket) -> dict | None:
    """
    Recebe uma mensagem com length-prefix do socket e retorna como dicionario.

    Args:
        sock: Socket TCP conectado.

    Returns:
        Dicionario com os dados recebidos, ou None se a conexao foi fechada.
    """
    # le o header (4 bytes)
    header_data = _recv_exact(sock, HEADER_SIZE)
    if header_data is None:
        return None

    payload_size = struct.unpack(HEADER_FORMAT, header_data)[0]

    # le o payload
    payload_data = _recv_exact(sock, payload_size)
    if payload_data is None:
        return None

    return json.loads(payload_data.decode("utf-8"))


def _recv_exact(sock: socket.socket, num_bytes: int) -> bytes | None:
    """
    Recebe exatamente num_bytes do socket.

    Returns:
        bytes recebidos, ou None se a conexao foi fechada.
    """
    data = b""
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:
            return None
        data += chunk
    return data
