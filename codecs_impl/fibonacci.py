from codecs_impl.base import BaseCodec


class FibonacciCodec(BaseCodec):
    @property
    def name(self) -> str:
        return "Fibonacci"

    @property
    def description(self) -> str:
        return ""

    def get_params_config(self) -> list[dict]:
        return []

    # TODO: implementar validate_encode_input() e parse_encode_input()
    #       parse_decode_input(), encode() e decode()

    def encode(self, value: int, **params) -> str:
        raise NotImplementedError(
            "O algoritmo Fibonacci/Zeckendorf ainda nao foi implementado. "
        )

    def decode(self, codeword: str, **params):
        raise NotImplementedError(
            "O algoritmo Fibonacci/Zeckendorf ainda nao foi implementado. "
        )
