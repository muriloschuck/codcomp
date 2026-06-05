from codecs_impl.golomb import GolombCodec
from codecs_impl.elias_gamma import EliasGammaCodec
from codecs_impl.fibonacci import FibonacciCodec
from codecs_impl.huffman import HuffmanCodec
from codecs_impl.repetition import RepetitionCodec
from codecs_impl.hamming import HammingCodec

# lista de codecs disponiveis
AVAILABLE_CODECS = [
    GolombCodec(),
    EliasGammaCodec(),
    FibonacciCodec(),
    HuffmanCodec(),
    RepetitionCodec(),
    HammingCodec(),
]

def get_codec_by_name(name: str):
    for codec in AVAILABLE_CODECS:
        if codec.name == name:
            return codec
    return None


def get_codec_names():
    return [codec.name for codec in AVAILABLE_CODECS]
