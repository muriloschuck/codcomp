from codecs_impl.golomb import GolombCodec
from codecs_impl.elias_gamma import EliasGammaCodec
from codecs_impl.fibonacci import FibonacciCodec
from codecs_impl.huffman import HuffmanCodec

# lista de codecs disponiveis
AVAILABLE_CODECS = [
    GolombCodec(),
    EliasGammaCodec(),
    FibonacciCodec(),
    HuffmanCodec(),
]

def get_codec_by_name(name: str):
    for codec in AVAILABLE_CODECS:
        if codec.name == name:
            return codec
    return None


def get_codec_names() -> list[str]:
    return [codec.name for codec in AVAILABLE_CODECS]
