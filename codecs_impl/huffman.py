from codecs_impl.base import BaseCodec


class HuffmanCodec(BaseCodec):
    @property
    def name(self) -> str:
        return "Huffman"

    @property
    def description(self) -> str:
        return ""

    def get_params_config(self) -> list[dict]:
        return []

    # TODO: implementar validate_encode_input(), parse_encode_input(),
    #       parse_decode_input(), encode() e decode()

    def encode(self, value: str, **params) -> str:
        raise NotImplementedError(
            "O algoritmo Huffman ainda nao foi implementado. "
        )

    def decode(self, codeword: str, **params):
        raise NotImplementedError(
            "O algoritmo Huffman ainda nao foi implementado. "
        )
