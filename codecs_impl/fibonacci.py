from codecs_impl.base import BaseCodec


class FibonacciCodec(BaseCodec):
    @property
    def name(self) -> str:
        return "Fibonacci"

    @property
    def description(self) -> str:
        return "Codificacao Fibonacci/Zeckendorf para inteiros positivos (>= 1)."

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
                return False, f"Fibonacci requer inteiros positivos (>= 1). Valor invalido: {val}"
        return True, ""

    def parse_encode_input(self, raw_input: str) -> list[int]:
        return [int(x) for x in raw_input.strip().split()]

    def parse_decode_input(self, raw_input: str) -> list[str]:
        return [raw_input.strip()]

    def encode(self, value: int, **params) -> str:
        if not isinstance(value, int) or value < 1:
            raise ValueError(f"Fibonacci requer inteiros positivos (>= 1). Recebido: {value}")

        # Generate fibs starting from F2=1
        fibs = [1]
        a, b = 1, 2
        while b <= value:
            fibs.append(b)
            a, b = b, a + b

        # Get used fibs
        used = set()
        n = value
        for f in reversed(fibs):
            if n >= f:
                used.add(f)
                n -= f

        # Build code
        code = []
        for f in fibs:
            if f in used:
                code.append('1')
            else:
                code.append('0')
        code.append('1')
        return ''.join(code)

    def decode(self, codeword: str, **params) -> int:
        if not codeword or not all(c in '01' for c in codeword) or not codeword.endswith('1'):
            raise ValueError(f"Codeword invalida: '{codeword}'. Deve ser uma string de 0s e 1s terminando com 1.")

        bits = codeword[:-1]

        # Generate fibs
        fibs = []
        a, b = 1, 1
        for _ in range(len(bits)):
            fibs.append(b)
            a, b = b, a + b

        value = 0
        for i, bit in enumerate(bits):
            if bit == '1':
                value += fibs[i]

        return value
