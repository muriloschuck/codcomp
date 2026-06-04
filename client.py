#!/usr/bin/env python3
"""
Cliente interativo para codificacao e transmissao de codewords.

O cliente codifica a mensagem localmente, opcionalmente insere erro,
e envia os codewords ao servidor para decodificacao.

Uso:
    python client.py [--host HOST] [--port PORT]
"""

import argparse
import random
import socket
import sys

from codecs_impl import AVAILABLE_CODECS, get_codec_by_name, get_codec_names
from protocol import send_message, recv_message


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 65432

# codecs que operam sobre inteiros (vs Huffman que opera sobre strings)
INTEGER_CODECS = {"Golomb", "Elias-Gamma", "Fibonacci"}


def parse_input(raw_input: str, codec_name: str) -> tuple[list, bool]:
    """
    Analisa a entrada do usuario e retorna valores prontos para codificacao.

    Para Huffman:
        Retorna ([raw_input], False) — a string inteira e o valor.

    Para codecs baseados em inteiros (Golomb, Elias-Gamma, Fibonacci):
        1. Tokeniza: virgula > espaco > texto continuo
        2. Se todos os tokens sao inteiros validos -> lista de ints
        3. Se qualquer token nao e int -> converte cada caractere de cada token para ord(c)

    Returns:
        (lista_de_valores, foi_convertido_ascii)
    """
    if codec_name not in INTEGER_CODECS:
        # Huffman: string inteira
        return [raw_input], False

    # Tokenizacao
    if "," in raw_input:
        tokens = [t.strip() for t in raw_input.split(",") if t.strip()]
    elif " " in raw_input:
        tokens = raw_input.split()
    else:
        # texto continuo, token unico
        tokens = [raw_input]

    # Tenta interpretar todos como inteiros
    all_int = True
    int_values = []
    for token in tokens:
        try:
            int_values.append(int(token))
        except ValueError:
            all_int = False
            break

    if all_int:
        return int_values, False

    # Nao e tudo int: converte cada caractere de cada token para ord(c)
    ascii_values = []
    for token in tokens:
        for c in token:
            ascii_values.append(ord(c))

    return ascii_values, True


class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        """Conecta ao servidor."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
        except ConnectionRefusedError:
            print(f"\nErro: Nao foi possivel conectar ao servidor em {self.host}:{self.port}")
            print("Certifique-se de que o servidor esta rodando (python server.py)")
            sys.exit(1)

    def disconnect(self):
        """Desconecta do servidor."""
        if self.sock:
            self.sock.close()
            self.sock = None

    # ─────────────────────────────────────────────
    # Etapas do fluxo
    # ─────────────────────────────────────────────

    def ask_input(self) -> str | None:
        """Pede a entrada do usuario. Retorna None se quiser sair."""
        try:
            raw = input("\nEntrada: ").strip()
            if not raw:
                print("  Entrada nao pode ser vazia.")
                return None
            return raw
        except (KeyboardInterrupt, EOFError):
            return None

    def ask_codec(self) -> str | None:
        """Pede o codec. Retorna nome do codec ou None para sair."""
        codec_names = get_codec_names()

        print("\nMetodo de codificacao:")
        for i, name in enumerate(codec_names, 1):
            print(f"  {i}. {name}")
        print(f"  {len(codec_names) + 1}. Sair")

        while True:
            try:
                choice = input("\nEscolha: ").strip()
                idx = int(choice) - 1
                if idx == len(codec_names):
                    return None  # sair
                if 0 <= idx < len(codec_names):
                    return codec_names[idx]
                print(f"  Opcao invalida. Escolha entre 1 e {len(codec_names) + 1}.")
            except ValueError:
                print("  Digite um numero valido.")
            except (KeyboardInterrupt, EOFError):
                return None

    def ask_params(self, codec_name: str) -> dict | None:
        """Solicita parametros do codec ao usuario."""
        codec = get_codec_by_name(codec_name)
        param_configs = codec.get_params_config()
        params = {}

        if not param_configs:
            return params

        for cfg in param_configs:
            name = cfg["name"]
            label = cfg["label"]
            default = cfg.get("default", "")
            min_val = cfg.get("min")
            max_val = cfg.get("max")

            hint_parts = []
            if min_val is not None:
                hint_parts.append(f"min={min_val}")
            if max_val is not None:
                hint_parts.append(f"max={max_val}")
            hint = f" ({', '.join(hint_parts)})" if hint_parts else ""

            while True:
                try:
                    raw = input(f"{label}{hint} [default={default}]: ").strip()
                    if not raw:
                        raw = str(default)

                    if cfg["type"] == "int":
                        val = int(raw)
                        if min_val is not None and val < min_val:
                            print(f"  Valor deve ser >= {min_val}.")
                            continue
                        if max_val is not None and val > max_val:
                            print(f"  Valor deve ser <= {max_val}.")
                            continue
                        params[name] = val
                    elif cfg["type"] == "float":
                        params[name] = float(raw)
                    else:
                        params[name] = raw
                    break
                except ValueError:
                    print(f"  Valor invalido. Esperado: {cfg['type']}.")
                except (KeyboardInterrupt, EOFError):
                    return None

        return params

    def encode(self, codec_name: str, raw_input: str, params: dict) -> tuple[list[str], bool] | tuple[None, bool]:
        """
        Codifica a entrada localmente.
        Retorna (codewords, foi_convertido_ascii) ou (None, False) se falhar.
        """
        codec = get_codec_by_name(codec_name)

        # parsing inteligente da entrada
        values, was_ascii = parse_input(raw_input, codec_name)

        # exibe conversao ASCII se houve
        if was_ascii:
            print("\n[Conversao ASCII]")
            # reconstroi os tokens para exibir a correspondencia
            if "," in raw_input:
                tokens = [t.strip() for t in raw_input.split(",") if t.strip()]
            elif " " in raw_input:
                tokens = raw_input.split()
            else:
                tokens = [raw_input]
            for token in tokens:
                for c in token:
                    print(f"  '{c}' -> {ord(c)}")

        # validacao do dominio do codec
        if codec_name in INTEGER_CODECS:
            for val in values:
                if codec_name == "Golomb" and val < 0:
                    print(f"  Erro: Golomb requer inteiros >= 0. Valor invalido: {val}")
                    return None, False
                elif codec_name in ("Elias-Gamma", "Fibonacci") and val < 1:
                    print(f"  Erro: {codec_name} requer inteiros >= 1. Valor invalido: {val}")
                    return None, False
        else:
            # Huffman: valida via codec
            valid, msg = codec.validate_encode_input(raw_input)
            if not valid:
                print(f"  Erro de validacao: {msg}")
                return None, False

        # codifica
        try:
            codewords = []

            print("\n[Codificacao]")
            for val in values:
                cw = codec.encode(val, **params)
                codewords.append(cw)
                print(f"  {val} -> {cw} ({len(cw)} bits)")

            return codewords, was_ascii
        except Exception as e:
            print(f"  Erro na codificacao: {e}")
            return None, False

    def ask_error(self, codewords: list[str]) -> list[str]:
        """
        Pergunta ao usuario se quer inserir erro.
        Retorna codewords (originais ou corrompidos).
        """
        full_cw = "".join(codewords)
        total_bits = len(full_cw)

        print("\nInsercao de erro:")
        print("  1. Manual (informar posicoes dos bits)")
        print("  2. Automatica (N bits aleatorios)")
        print("  3. Nenhum (transmitir sem erro)")

        try:
            choice = input("\nEscolha: ").strip()
        except (KeyboardInterrupt, EOFError):
            return codewords

        if choice == "3" or not choice:
            return codewords

        positions = []

        if choice == "1":
            try:
                raw = input("Posicoes dos bits a inverter (0-indexed, virgula-separadas): ").strip()
                if not raw:
                    return codewords
                for token in raw.split(","):
                    token = token.strip()
                    if token:
                        pos = int(token)
                        if pos < 0 or pos >= total_bits:
                            print(f"  Posicao {pos} fora do intervalo [0, {total_bits - 1}]. Cancelando insercao.")
                            return codewords
                        positions.append(pos)
            except ValueError:
                print("  Posicao invalida. Transmitindo sem erro.")
                return codewords
            except (KeyboardInterrupt, EOFError):
                return codewords

        elif choice == "2":
            try:
                n = int(input(f"Quantos bits inverter? (max {total_bits}): ").strip())
                if n < 1 or n > total_bits:
                    print(f"  Valor deve estar entre 1 e {total_bits}. Cancelando insercao.")
                    return codewords
                positions = sorted(random.sample(range(total_bits), n))
            except ValueError:
                print("  Valor invalido. Transmitindo sem erro.")
                return codewords
            except (KeyboardInterrupt, EOFError):
                return codewords
        else:
            print("  Opcao invalida. Transmitindo sem erro.")
            return codewords

        if not positions:
            return codewords

        # aplica flip nos bits
        bits = list(full_cw)
        for pos in positions:
            bits[pos] = '1' if bits[pos] == '0' else '0'
        corrupted_full = ''.join(bits)

        # divide de volta nos tamanhos originais
        corrupted_parts = []
        offset = 0
        for cw in codewords:
            corrupted_parts.append(corrupted_full[offset:offset + len(cw)])
            offset += len(cw)

        return corrupted_parts

    def transmit(self, codec_name: str, params: dict, codewords: list[str]) -> dict | None:
        """Envia codewords ao servidor e retorna a resposta."""
        request = {
            "action": "decode",
            "codec": codec_name,
            "params": params,
            "codewords": codewords,
        }
        try:
            send_message(self.sock, request)
            return recv_message(self.sock)
        except (ConnectionResetError, BrokenPipeError, OSError):
            print("\nErro: Conexao com o servidor foi perdida.")
            return None

    def show_result(self, original_codewords: list[str], sent_codewords: list[str],
                    response: dict, codec_name: str, raw_input: str,
                    was_ascii: bool, original_values: list):
        """Exibe o resumo da transmissao e a resposta do servidor."""

        # posicoes com erro
        original_full = "".join(original_codewords)
        sent_full = "".join(sent_codewords)
        error_positions = [i for i in range(len(original_full))
                          if original_full[i] != sent_full[i]]

        print("\n[Transmissao]")
        print(f"  Codeword original: {' '.join(original_codewords)}")
        print(f"  Codeword enviado:  {' '.join(sent_codewords)}")
        if error_positions:
            print(f"  Posicoes invertidas: {error_positions}")
        else:
            print(f"  Erro inserido: Nenhum")

        # resposta do servidor
        status = response.get("status", "error")

        print("\n[Resposta do Servidor]")

        if status == "error":
            print(f"  Erro: {response.get('message', 'desconhecido')}")
            return

        decoded_values = response.get("decoded_values", [])
        details = response.get("details", [])

        # mostra decodificacao
        decoded_strs = []
        for d in details:
            dec = d.get("decoded")
            if dec is not None:
                decoded_strs.append(str(dec))
            else:
                decoded_strs.append(f"ERRO({d.get('error', '?')})")
        print(f"  Decodificado: {' '.join(decoded_strs)}")

        # se houve conversao ASCII, reconverte para texto
        if was_ascii and decoded_values:
            text_chars = []
            for v in decoded_values:
                if v is not None:
                    try:
                        text_chars.append(chr(int(v)))
                    except (ValueError, OverflowError):
                        text_chars.append("?")
                else:
                    text_chars.append("?")
            print(f"  Texto: {''.join(text_chars)}")

        # comparacao se houve erro
        if error_positions:
            print("\n[Comparacao]")
            original_strs = [str(v) for v in original_values]
            for orig, dec in zip(original_strs, decoded_values):
                if dec is None:
                    print(f"  {orig} -> ERRO DE DECODIFICACAO")
                elif str(orig) != str(dec):
                    print(f"  {orig} -> {dec}  (DIVERGENCIA)")
                else:
                    print(f"  {orig} -> {dec}  (OK)")

    # ─────────────────────────────────────────────
    # Loop principal
    # ─────────────────────────────────────────────

    def run(self):
        """Loop principal do cliente."""
        self.connect()

        print("=" * 50)
        print("  Codificacao e Decodificacao")
        print("=" * 50)
        print(f"  Servidor: {self.host}:{self.port}")

        while True:
            # 1. Entrada
            raw_input = self.ask_input()
            if raw_input is None:
                continue

            # 2. Codec
            codec_name = self.ask_codec()
            if codec_name is None:
                break

            # 3. Parametros
            params = self.ask_params(codec_name)
            if params is None:
                break

            # 4. Codificacao local
            result = self.encode(codec_name, raw_input, params)
            codewords, was_ascii = result
            if codewords is None:
                continue

            # guardar valores originais para comparacao
            original_values, _ = parse_input(raw_input, codec_name)

            # 5. Insercao de erro
            sent_codewords = self.ask_error(codewords)

            # 6. Transmissao
            response = self.transmit(codec_name, params, sent_codewords)
            if response is None:
                break

            # 7. Exibicao
            self.show_result(codewords, sent_codewords, response, codec_name,
                           raw_input, was_ascii, original_values)

        print("\nEncerrando cliente.")
        self.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Cliente de codificacao")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host do servidor (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Porta do servidor (default: {DEFAULT_PORT})")
    args = parser.parse_args()

    client = Client(args.host, args.port)
    client.run()


if __name__ == "__main__":
    main()
