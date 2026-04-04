"""

Dado n e divisor k:
- q = n // k  (quociente)
- r = n % k   (resto)
- Parte unitaria: q zeros seguidos de 1 (ex: q=3 -> '0001')
- Parte binaria (truncated binary):
    - b = ceil(log2(m))
    - Se m e potencia de 2: r em binario com b bits
    - Senao:
        - cutoff = 2^b - m
        - Se r < cutoff: r em binario com (b-1) bits
        - Se r >= cutoff: (r + cutoff) em binario com b bits
- Codeword = parte_unitaria + parte_binaria
"""

import math
from codecs_impl.base import BaseCodec

class GolombCodec(BaseCodec):
    @property
    def name(self) -> str:
        return "Golomb"

    @property
    def description(self) -> str:
        return "Codificacao Golomb para inteiros nao-negativos com divisor k."

    def get_params_config(self) -> list[dict]:
        return [
            {
                "name": "k",
                "label": "Divisor (k)",
                "type": "int",
                "default": 4,
                "min": 1,
            }
        ]

    def validate_encode_input(self, raw_input: str) -> tuple[bool, str]:
        valid, msg = super().validate_encode_input(raw_input)
        if not valid:
            return valid, msg

        tokens = raw_input.strip().split()
        for token in tokens:
            try:
                val = int(token)
            except ValueError:
                return False, f"'{token}' nao e um inteiro valido."
            if val < 0:
                return False, f"Golomb requer inteiros nao-negativos (>= 0). Valor invalido: {val}"
        return True, ""

    def parse_encode_input(self, raw_input: str) -> list[int]:
        return [int(x) for x in raw_input.strip().split()]

    def encode(self, value: int, **params) -> str:
        """
        codifica um inteiro nao-negativo usando Golomb com divisor k.

        Args:
            value: Inteiro >= 0 a ser codificado.
            **params: Deve conter 'k' (int >= 1), o divisor Golomb.

        Returns:
            String de bits representando a codeword Golomb.

        Raises:
            ValueError: Se value < 0 ou k < 1.
        """
        m = params.get("k", 4)
        if not isinstance(m, int) or m < 1:
            raise ValueError(f"Divisor k deve ser inteiro >= 1. Recebido: {m}")
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"Valor deve ser inteiro nao-negativo. Recebido: {value}")

        q = value // m
        r = value % m

        # Parte unitaria: q zeros + '1'
        unary = '0' * q + '1'

        # Parte binaria (truncated binary encoding do resto r)
        binary = self._truncated_binary_encode(r, m)

        return unary + binary

    def decode(self, codeword: str, **params) -> int:
        """
        decodifica uma codeword Golomb e retorna o inteiro original.

        Args:
            codeword: String de bits (ex: '00110').
            **params: Deve conter 'k' (int >= 1), o divisor Golomb.

        Returns:
            Inteiro nao-negativo decodificado.

        Raises:
            ValueError: Se a codeword for invalida.
        """
        m = params.get("k", 4)
        if not isinstance(m, int) or m < 1:
            raise ValueError(f"Divisor k deve ser inteiro >= 1. Recebido: {m}")

        if not codeword or not all(c in '01' for c in codeword):
            raise ValueError(f"Codeword invalida: '{codeword}'. Deve conter apenas 0 e 1.")

        # unitaria: contar zeros ate encontrar '1'
        q = 0
        pos = 0
        while pos < len(codeword) and codeword[pos] == '0':
            q += 1
            pos += 1

        if pos >= len(codeword):
            raise ValueError("Codeword invalida: nao encontrou '1' terminador da parte unaria.")

        # pula o stop bit '1'
        pos += 1

        # binaria (truncated binary decoding)
        r, bits_consumed = self._truncated_binary_decode(codeword[pos:], m)

        total_bits = pos + bits_consumed
        if total_bits != len(codeword):
            raise ValueError(
                f"Codeword tem {len(codeword)} bits mas apenas {total_bits} foram consumidos. "
                f"Verifique se a codeword esta correta para k={m}."
            )

        return q * m + r

    def _truncated_binary_encode(self, r: int, m: int) -> str:
        """
        quando m e potencia de 2, eh simplesmente binario com log2(m) bits.
        caso contrario, usa o truncated binary.
        """
        if m == 1:
            # resto 0, nenhum bit necessario
            return ""

        b = math.ceil(math.log2(m))

        if (m & (m - 1)) == 0:
            # se eh potencia de 2, binario simples com b bits
            return format(r, f'0{b}b')

        # truncated binary encoding
        cutoff = (1 << b) - m  # 2^b - m

        if r < cutoff:
            # Usa b-1 bits
            return format(r, f'0{b - 1}b')
        else:
            # Usa b bits, codificando r + cutoff
            return format(r + cutoff, f'0{b}b')

    def _truncated_binary_decode(self, bits: str, m: int) -> tuple[int, int]:
        """
        decodifica usando truncated binary decoding.

        Returns:
            Tupla (resto, bits_consumidos).
        """
        if m == 1:
            return 0, 0

        b = math.ceil(math.log2(m))

        # se eh potencia de 2, le b bits diretamente
        if (m & (m - 1)) == 0:
            if len(bits) < b:
                raise ValueError(
                    f"Bits insuficientes para decodificar resto. "
                    f"Esperado {b} bits, disponivel {len(bits)}."
                )
            r = int(bits[:b], 2)
            return r, b

        # truncated binary decoding
        cutoff = (1 << b) - m

        if len(bits) < b - 1:
            raise ValueError(
                f"Bits insuficientes para decodificar resto. "
                f"Esperado pelo menos {b - 1} bits, disponivel {len(bits)}."
            )

        # le b-1 bits primeiro
        prefix_val = int(bits[:b - 1], 2)

        if prefix_val < cutoff:
            # O valor e o resto, consumiu b-1 bits
            return prefix_val, b - 1
        else:
            # Precisa ler mais 1 bit (total b bits)
            if len(bits) < b:
                raise ValueError(
                    f"Bits insuficientes para decodificar resto. "
                    f"Esperado {b} bits, disponivel {len(bits)}."
                )
            full_val = int(bits[:b], 2)
            r = full_val - cutoff
            return r, b
