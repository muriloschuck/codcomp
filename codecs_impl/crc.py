"""
CRC-4

G(x) = x^4 + x + 1
Gerador binario: 10011

Este codec calcula o CRC de uma mensagem binaria ou de um inteiro,
anexa os bits redundantes e verifica erros na recepcao.
"""

from codecs_impl.base import BaseCodec


class CRCCodec(BaseCodec):
    _GENERATOR = "10011" # 5 bits, grau 4
    _DEGREE = len(_GENERATOR) - 1

    @property
    def name(self) -> str:
        return "CRC-4"

    @property
    def description(self) -> str:
        return "Cyclic Redundancy Check usando gerador x^4 + x + 1 (10011)."

    def get_params_config(self) -> list[dict]:
        return []

    def _to_bits(self, value) -> str:
        if isinstance(value, int):
            if value < 0:
                raise ValueError("CRC-4 requer inteiros >= 0. Recebido: " + str(value))
            return format(value, "b") if value > 0 else "0"

        text = str(value)
        if not text:
            raise ValueError("Entrada vazia para CRC-4.")

        if all(c in "01" for c in text):
            return text

        # Converte texto para binario de 8 bits por caractere.
        return "".join(format(ord(c), "08b") for c in text)

    def _binary_division(self, bits: str) -> str:
        if len(bits) < len(self._GENERATOR):
            raise ValueError("Divisao binaria: codeword menor que o gerador.")

        dividend = list(bits)
        divisor = self._GENERATOR
        n = len(divisor)

        for i in range(len(bits) - n + 1):
            if dividend[i] == "1":
                for j in range(n):
                    dividend[i + j] = "0" if dividend[i + j] == divisor[j] else "1"

        remainder = "".join(dividend[-(n - 1):])
        return remainder

    def encode_with_details(self, value) -> dict:
        data_bits = self._to_bits(value)
        crc_bits = self._binary_division(data_bits + "0" * self._DEGREE)
        codeword = data_bits + crc_bits
        return {
            "data_bits": data_bits,
            "crc_bits": crc_bits,
            "codeword": codeword,
            "total_bits": len(codeword),
        }

    def encode(self, value) -> str:
        bits = self._to_bits(value)
        crc_bits = self._binary_division(bits + "0" * self._DEGREE)
        return bits + crc_bits

    def _bits_to_text(self, bits: str) -> str | None:
        if len(bits) % 8 != 0:
            return None

        chars = []
        for i in range(0, len(bits), 8):
            byte = int(bits[i:i + 8], 2)
            if byte in (9, 10, 13) or 32 <= byte <= 126:
                chars.append(chr(byte))
            else:
                return None

        return "".join(chars)

    def decode_with_details(self, codeword: str) -> dict:
        if not codeword or not all(c in "01" for c in codeword):
            raise ValueError("Codeword deve conter apenas 0 e 1.")
        if len(codeword) <= self._DEGREE:
            raise ValueError(
                f"Codeword muito curto para CRC-4. Deve ter mais de {self._DEGREE} bits."
            )

        remainder = self._binary_division(codeword)
        has_error = any(bit == "1" for bit in remainder)
        data_bits = codeword[:-self._DEGREE]

        decoded_value = None
        if data_bits:
            decoded_value = self._bits_to_text(data_bits)
            if decoded_value is None:
                decoded_value = str(int(data_bits, 2))
        else:
            decoded_value = "0"

        return {
            "codeword": codeword,
            "data_bits": data_bits,
            "crc_remainder": remainder,
            "crc_bits": codeword[-self._DEGREE:],
            "has_error": has_error,
            "decoded_value": decoded_value,
        }

    def decode(self, codeword: str, **params):
        details = self.decode_with_details(codeword, **params)
        if details["has_error"]:
            raise ValueError("CRC invalido: erro detectado na transmissao.")
        return details["decoded_value"]

    def validate_decode_input(self, raw_input: str) -> tuple[bool, str]:
        valid, msg = super().validate_decode_input(raw_input)
        if not valid:
            return valid, msg

        for token in raw_input.strip().split():
            if len(token) <= self._DEGREE:
                return False, (
                    f"Codeword '{token}' tem {len(token)} bits. CRC-4 requer mais de {self._DEGREE} bits."
                )
        return True, ""
