#!/usr/bin/env python3
"""
Servidor TCP para decodificacao de codewords.

Recebe codewords do cliente, decodifica usando o codec especificado,
e retorna o resultado.

Uso:
    python server.py [--host HOST] [--port PORT]
"""

import argparse
import socket
import threading
from datetime import datetime

from codecs_impl import get_codec_by_name, get_codec_names
from protocol import send_message, recv_message


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 65432


def log(msg: str):
    """Imprime mensagem com timestamp no terminal do servidor."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")


def handle_decode(request: dict) -> dict:
    """
    Decodifica os codewords recebidos.

    Espera:
        request["codec"]: nome do codec
        request["params"]: parametros do codec (ex: {"k": 4})
        request["codewords"]: lista de codewords binarios
    """
    codec_name = request.get("codec")
    params = request.get("params", {})
    codewords = request.get("codewords", [])

    if not codec_name:
        return {"status": "error", "message": "Campo 'codec' e obrigatorio."}

    codec = get_codec_by_name(codec_name)
    if codec is None:
        return {
            "status": "error",
            "message": f"Codec '{codec_name}' nao encontrado. Disponiveis: {get_codec_names()}",
        }

    if not codewords:
        return {"status": "error", "message": "Nenhum codeword recebido."}

    decoded_values = []
    details = []
    has_errors = False

    for cw in codewords:
        try:
            # Hamming: usa decode_with_details para obter sindrome e correcao
            if codec_name == "Hamming":
                hamming_info = codec.decode_with_details(cw)
                value = hamming_info["decoded_value"]
            elif codec_name == "CRC-4":
                crc_info = codec.decode_with_details(cw)
                if crc_info["has_error"]:
                    raise ValueError("CRC invalido: erro detectado na transmissao.")
                value = crc_info["decoded_value"]
            else:
                value = codec.decode(cw, **params)

            detail = {
                "codeword": cw,
                "decoded": str(value),
                "bits": len(cw),
            }

            # info extra para CRC-4
            if codec_name == "CRC-4":
                detail["data_bits"] = crc_info["data_bits"]
                detail["crc_bits"] = crc_info["crc_bits"]
                detail["crc_remainder"] = crc_info["crc_remainder"]
                detail["erro_detectado"] = crc_info["has_error"]

            # info extra para codigo de repeticao
            if codec_name == "Repeticao":
                ri = params.get("ri", 3)
                grupos_com_divergencia = []
                bits_corrigidos = []
                for i in range(0, len(cw), ri):
                    grupo = cw[i:i + ri]
                    ones = grupo.count('1')
                    bit_resultado = '1' if ones > ri // 2 else '0'
                    bits_corrigidos.append(bit_resultado)
                    # se nao foi unanime, houve possivel erro
                    if ones != 0 and ones != ri:
                        grupos_com_divergencia.append(i // ri)

                detail["bits_corrigidos"] = ''.join(bits_corrigidos)
                detail["grupos_com_divergencia"] = grupos_com_divergencia
                detail["erro_detectado"] = len(grupos_com_divergencia) > 0

            # info extra para Hamming
            if codec_name == "Hamming":
                detail["hamming_blocks"]     = hamming_info["blocks"]
                detail["has_any_error"]      = hamming_info["has_any_error"]
                detail["corrected_codeword"] = hamming_info["corrected_codeword"]
                detail["all_data_bits"]      = hamming_info["all_data_bits"]

            decoded_values.append(str(value))
            details.append(detail)
        except Exception as e:
            decoded_values.append(None)
            details.append({
                "codeword": cw,
                "decoded": None,
                "error": str(e),
                "bits": len(cw),
            })
            has_errors = True

    status = "partial" if has_errors else "ok"
    return {
        "status": status,
        "decoded_values": decoded_values,
        "details": details,
    }


def handle_client(client_sock: socket.socket, client_addr: tuple):
    """Trata a conexao de um cliente em uma thread separada."""
    log(f"Cliente conectado: {client_addr[0]}:{client_addr[1]}")

    try:
        while True:
            request = recv_message(client_sock)
            if request is None:
                break

            action = request.get("action", "")

            if action == "decode":
                response = handle_decode(request)
                # log detalhado
                codec_name = request.get("codec", "?")
                codewords = request.get("codewords", [])
                decoded = response.get("decoded_values", [])
                log(f"Recebido: codec={codec_name}, {len(codewords)} codewords")
                log(f"  Decodificado: {decoded}")
                # log extra para Hamming
                if codec_name == "Hamming":
                    for d in response.get("details", []):
                        for j, blk in enumerate(d.get("hamming_blocks", []), 1):
                            if blk["has_error"]:
                                log(
                                    f"  [Hamming] bloco {j}: recebido={blk['received']} | "
                                    f"sindrome={blk['syndrome']} | "
                                    f"erro na posicao {blk['error_position']} (1-indexado) | "
                                    f"corrigido={blk['corrected_block']}"
                                )
                            else:
                                log(
                                    f"  [Hamming] bloco {j}: recebido={blk['received']} | "
                                    f"sindrome={blk['syndrome']} | sem erro"
                                )
                # log extra para CRC-4
                if codec_name == "CRC-4":
                    for d in response.get("details", []):
                        if d.get("erro_detectado"):
                            log(f"  [CRC-4] codeword={d['codeword']} | erro detectado | resto={d['crc_remainder']}")
                        else:
                            log(f"  [CRC-4] codeword={d['codeword']} | sem erro | dados={d['data_bits']}")

            else:
                response = {
                    "status": "error",
                    "message": f"Acao desconhecida: '{action}'. Acao valida: decode",
                }

            send_message(client_sock, response)

    except (ConnectionResetError, BrokenPipeError):
        log(f"Conexao perdida: {client_addr[0]}:{client_addr[1]}")
    except Exception as e:
        log(f"Erro com cliente {client_addr[0]}:{client_addr[1]}: {e}")
    finally:
        client_sock.close()
        log(f"Cliente desconectado: {client_addr[0]}:{client_addr[1]}")


def main():
    parser = argparse.ArgumentParser(description="Servidor de decodificacao")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Porta (default: {DEFAULT_PORT})")
    args = parser.parse_args()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((args.host, args.port))
    server_sock.listen(5)

    print("=" * 50)
    print("  Servidor de Decodificacao")
    print("=" * 50)
    log(f"Escutando em {args.host}:{args.port}")
    print("Pressione Ctrl+C para encerrar.\n")

    try:
        while True:
            client_sock, client_addr = server_sock.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(client_sock, client_addr),
                daemon=True,
            )
            thread.start()
    except KeyboardInterrupt:
        print("\n")
        log("Servidor encerrado.")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()
