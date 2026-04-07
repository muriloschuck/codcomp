"""
Codificacao Elias-Gamma para inteiros positivos (>= 1).

Dado n >= 1:
  - k = floor(log2(n))   (numero de bits em n menos 1)
  - Prefixo unario: k zeros
  - Sufixo binario: representacao binaria de n com k+1 bits
  - Codeword = k zeros + binario(n)

Exemplos:
  1  -> '1'          (k=0)
  2  -> '010'        (k=1)
  3  -> '011'        (k=1)
  4  -> '00100'      (k=2)
  7  -> '00111'      (k=2)
  8  -> '0001000'    (k=3)
"""

import math
from codecs_impl.base import BaseCodec


class EliasGammaCodec(BaseCodec):
    @property
    def name(self) -> str:
        return "Elias-Gamma"

    @property
    def description(self) -> str:
        return "Codificacao Elias-Gamma para inteiros positivos (>= 1)."

    def get_params_config(self) -> list[dict]:
        return []

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
            if val < 1:
                return False, f"Elias-Gamma requer inteiros positivos (>= 1). Valor invalido: {val}"
        return True, ""

    def parse_encode_input(self, raw_input: str) -> list[int]:
        return [int(x) for x in raw_input.strip().split()]

    def encode(self, value: int, **params) -> str:
        """
        Codifica um inteiro positivo usando Elias-Gamma.

        Args:
            value: Inteiro >= 1 a ser codificado.

        Returns:
            String de bits representando a codeword Elias-Gamma.

        Raises:
            ValueError: Se value < 1.
        """
        if not isinstance(value, int) or value < 1:
            raise ValueError(f"Elias-Gamma requer inteiros positivos (>= 1). Recebido: {value}")

        k = int(math.log2(value))          # floor(log2(n))
        prefix = '0' * k                   # k zeros
        suffix = format(value, f'0{k+1}b') # n em binario com k+1 bits
        return prefix + suffix

    def decode(self, codeword: str, **params) -> int:
        """
        Decodifica uma codeword Elias-Gamma e retorna o inteiro original.

        Args:
            codeword: String de bits (ex: '00101').

        Returns:
            Inteiro positivo decodificado.

        Raises:
            ValueError: Se a codeword for invalida.
        """
        if not codeword or not all(c in '01' for c in codeword):
            raise ValueError(f"Codeword invalida: '{codeword}'. Deve conter apenas 0 e 1.")

        # conta zeros iniciais -> k
        k = 0
        while k < len(codeword) and codeword[k] == '0':
            k += 1

        # precisa de k+1 bits de sufixo
        suffix_start = k
        suffix_end = k + (k + 1)
        if suffix_end > len(codeword):
            raise ValueError(
                f"Codeword muito curta: esperados {k} zeros + {k+1} bits de sufixo, "
                f"mas so ha {len(codeword)} bits no total."
            )
        if suffix_end != len(codeword):
            raise ValueError(
                f"Codeword tem {len(codeword)} bits mas apenas {suffix_end} foram consumidos "
                f"(k={k}). Verifique se a codeword esta correta."
            )

        suffix = codeword[suffix_start:suffix_end]
        value = int(suffix, 2)

        if value < 1:
            raise ValueError("Codeword invalida: o valor decodificado deve ser >= 1.")

        return value
