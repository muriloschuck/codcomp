"""
Hamming (7,4)

Organizacao do codeword: D1 D2 D3 D4 P1 P2 P3 (posicoes 1-indexadas)

Os 4 bits de dados ocupam as primeiras posicoes; os 3 bits de paridade
ficam no final (forma sistematica).

Equacoes de paridade (paridade par):
  P1 = D1 ^ D2 ^ D4   (cobre D1, D2, D4, P1)
  P2 = D1 ^ D3 ^ D4   (cobre D1, D3, D4, P2)
  P3 = D2 ^ D3 ^ D4   (cobre D2, D3, D4, P3)

Matriz de verificacao de paridade H (3x7):
         D1  D2  D3  D4  P1  P2  P3
  P1:     1   1   0   1   1   0   0
  P2:     1   0   1   1   0   1   0
  P3:     0   1   1   1   0   0   1

Sindrome S = H * r (mod 2):
  s1 = D1 ^ D2 ^ D4 ^ P1
  s2 = D1 ^ D3 ^ D4 ^ P2
  s3 = D2 ^ D3 ^ D4 ^ P3
  sindrome_int = s1*4 + s2*2 + s3

Mapeamento sindrome_int -> posicao do erro (1-indexado):
  0 -> sem erro
  6 -> pos 1 (D1)   |  5 -> pos 2 (D2)   |  3 -> pos 3 (D3)
  7 -> pos 4 (D4)   |  4 -> pos 5 (P1)   |  2 -> pos 6 (P2)   |  1 -> pos 7 (P3)

Para valores com mais de 4 bits:
  Converte para binario, completa ate multiplo de 4, divide em blocos
  de 4 bits e codifica cada bloco individualmente.
  Codeword final = concatenacao dos blocos de 7 bits.
"""

from codecs_impl.base import BaseCodec


# Mapeamento sindrome (inteiro) -> posicao do bit errado (1-indexada, 0 = sem erro)
_SYNDROME_TO_POS = {
    0: 0,
    6: 1,
    5: 2,
    3: 3,
    7: 4,
    4: 5,
    2: 6,
    1: 7,
}


class HammingCodec(BaseCodec):

    @property
    def name(self):
        return "Hamming"

    @property
    def description(self):
        return "Hamming (7,4): D1 D2 D3 D4 P1 P2 P3 - 4 bits de dados + 3 de paridade. Corrige 1 erro por bloco."

    def get_params_config(self):
        return []

    def _encode_block(self, data4):
        """
        Codifica 4 bits de dados em 7 bits: D1 D2 D3 D4 P1 P2 P3

        P1 = D1 ^ D2 ^ D4
        P2 = D1 ^ D3 ^ D4
        P3 = D2 ^ D3 ^ D4
        """
        if len(data4) != 4 or not all(c in "01" for c in data4):
            raise ValueError(
                "Bloco de dados deve ter exatamente 4 bits binarios. Recebido: " + repr(data4)
            )

        d1 = int(data4[0])
        d2 = int(data4[1])
        d3 = int(data4[2])
        d4 = int(data4[3])

        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p3 = d2 ^ d3 ^ d4

        codeword = str(d1) + str(d2) + str(d3) + str(d4) + str(p1) + str(p2) + str(p3)

        return {
            "data_bits":   data4,
            "p1": p1, "p2": p2, "p3": p3,
            "parity_bits": str(p1) + str(p2) + str(p3),
            "codeword":    codeword,
        }

    def _decode_block(self, block7):
        """
        Decodifica 7 bits com deteccao e correcao de 1 erro.

        Layout esperado: D1 D2 D3 D4 P1 P2 P3
        Calcula sindrome S = H * r (mod 2).
        Usa tabela _SYNDROME_TO_POS para identificar posicao do erro.
        Extrai bits de dados das posicoes 1-4 do bloco corrigido.
        """
        if len(block7) != 7 or not all(c in "01" for c in block7):
            raise ValueError(
                "Bloco deve ter exatamente 7 bits binarios. Recebido: " + repr(block7)
            )

        r = [int(b) for b in block7]
        # r[0]=D1  r[1]=D2  r[2]=D3  r[3]=D4  r[4]=P1  r[5]=P2  r[6]=P3

        s1 = r[0] ^ r[1] ^ r[3] ^ r[4]   # D1, D2, D4, P1
        s2 = r[0] ^ r[2] ^ r[3] ^ r[5]   # D1, D3, D4, P2
        s3 = r[1] ^ r[2] ^ r[3] ^ r[6]   # D2, D3, D4, P3

        syndrome_int = s1 * 4 + s2 * 2 + s3

        error_position = _SYNDROME_TO_POS.get(syndrome_int, 0)

        corrected = list(r)
        if error_position != 0:
            corrected[error_position - 1] ^= 1

        corrected_block = "".join(str(b) for b in corrected)

        # bits de dados estao nas posicoes 1-4 (indices 0-3)
        data_bits = str(corrected[0]) + str(corrected[1]) + str(corrected[2]) + str(corrected[3])

        return {
            "received":        block7,
            "syndrome":        syndrome_int,
            "has_error":       error_position != 0,
            "error_position":  error_position,
            "corrected_block": corrected_block,
            "data_bits":       data_bits,
        }

    def encode(self, value, **params):
        bits = self._to_bits(value)
        codeword = ""
        for i in range(0, len(bits), 4):
            info = self._encode_block(bits[i:i + 4])
            codeword += info["codeword"]
        return codeword

    def encode_with_details(self, value, **params):
        bits = self._to_bits(value)
        blocks = []
        codeword = ""
        for i in range(0, len(bits), 4):
            info = self._encode_block(bits[i:i + 4])
            blocks.append(info)
            codeword += info["codeword"]

        return {
            "input_bits":        bits,
            "blocks":            blocks,
            "codeword":          codeword,
            "total_data_bits":   len(bits),
            "total_parity_bits": len(blocks) * 3,
        }

    def decode(self, codeword, **params):
        self._validate_codeword(codeword)
        all_data = ""
        for i in range(0, len(codeword), 7):
            info = self._decode_block(codeword[i:i + 7])
            all_data += info["data_bits"]
        return int(all_data, 2)

    def decode_with_details(self, codeword, **params):
        self._validate_codeword(codeword)
        blocks = []
        all_data = ""
        corrected_cw = ""
        has_any_error = False

        for i in range(0, len(codeword), 7):
            info = self._decode_block(codeword[i:i + 7])
            blocks.append(info)
            all_data += info["data_bits"]
            corrected_cw += info["corrected_block"]
            if info["has_error"]:
                has_any_error = True

        return {
            "blocks":             blocks,
            "has_any_error":      has_any_error,
            "all_data_bits":      all_data,
            "decoded_value":      int(all_data, 2),
            "corrected_codeword": corrected_cw,
        }

    def validate_encode_input(self, raw_input):
        if not raw_input or not raw_input.strip():
            return False, "Entrada nao pode ser vazia."
        return True, ""

    def validate_decode_input(self, raw_input):
        valid, msg = super().validate_decode_input(raw_input)
        if not valid:
            return valid, msg
        for token in raw_input.strip().split():
            if len(token) % 7 != 0:
                return False, (
                    "Codeword " + repr(token) + " tem " + str(len(token)) + " bits. "
                    "Hamming (7,4) requer multiplo de 7 bits por codeword."
                )
        return True, ""

    def _to_bits(self, value):
        if isinstance(value, int):
            if value < 0:
                raise ValueError("Hamming requer inteiros >= 0. Recebido: " + str(value))
            bits = format(value, "b") if value > 0 else "0"
        elif isinstance(value, str):
            bits = value
            if not all(c in "01" for c in bits):
                raise ValueError("Entrada invalida para Hamming: " + repr(bits))
        else:
            raise ValueError("Tipo de entrada invalido para Hamming: " + str(type(value)))

        remainder = len(bits) % 4
        if remainder:
            bits = bits.zfill(len(bits) + (4 - remainder))
        return bits

    def _validate_codeword(self, codeword):
        if not codeword or not all(c in "01" for c in codeword):
            raise ValueError("Codeword deve conter apenas 0 e 1.")
        if len(codeword) % 7 != 0:
            raise ValueError(
                "Tamanho do codeword (" + str(len(codeword)) + " bits) nao e multiplo de 7. "
                "Hamming (7,4) requer blocos de 7 bits."
            )
