"""
Codificacao Huffman para strings baseada na frequencia dos simbolos.

A codificacao de Huffman constroi uma arvore binaria onde os caracteres 
mais frequentes possuem os menores caminhos (menos bits).

Como o decodificador precisa da arvore/tabela original para reverter o 
processo, este codec anexa o dicionario de codigos junto a codeword, 
utilizando o separador '|'. Para evitar problemas com caracteres especiais, 
os caracteres sao serializados usando seu valor numerico (ASCII/Unicode).

Exemplo de codificacao:
  Entrada: "banana"
  Frequencias: b:1, a:3, n:2
  Codigos gerados: a:1, n:01, b:00
  Parte Binaria (banana): 100110110
  Tabela Serializada (ASCII): 97:0,98:10,110:11
  Codeword Final: '100110110|97:0,98:10,110:11'
"""

from collections import Counter
import heapq
from codecs_impl.base import BaseCodec


class _HuffmanNode:
    def __init__(self, char=None, freq=0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

class HuffmanCodec(BaseCodec):
    @property
    def name(self) -> str:
        return "Huffman"

    @property
    def description(self) -> str:
        return "Codificacao Huffman para strings baseada na frequencia dos simbolos."

    def get_params_config(self) -> list[dict]:
        return []

    def validate_encode_input(self, raw_input: str) -> tuple[bool, str]:
        valid, msg = super().validate_encode_input(raw_input)
        if not valid:
            return valid, msg
        return True, ""

    def validate_decode_input(self, raw_input: str) -> tuple[bool, str]:
        """
        Sobrescreve a validacao padrao pois a codeword do Huffman
        inclui a tabela serializada e caracteres alem de 0 e 1.
        """
        if not raw_input or not raw_input.strip():
            return False, "Entrada nao pode ser vazia."
        
        if "|" not in raw_input:
            return False, "Formato invalido. Esperado separador '|' entre a codeword e a tabela."
            
        bits, _ = raw_input.split("|", 1)
        if not all(c in '01' for c in bits):
            return False, "A parte da codeword (antes do '|') deve conter apenas 0 e 1."
            
        return True, ""

    def parse_encode_input(self, raw_input: str) -> list[str]:
        # Para Huffman, tratamos a string inteira como um unico valor
        return [raw_input]

    def parse_decode_input(self, raw_input: str) -> list[str]:
        # Retorna a string inteira, pois ela contem os bits e a tabela
        return [raw_input]

    # ------------------------
    # HUFFMAN CORE
    # ------------------------

    def _build_tree(self, text: str):
        freq = Counter(text)

        heap = []
        for char, f in freq.items():
            heapq.heappush(heap, _HuffmanNode(char, f))

        if len(heap) == 1:
            # Caso especial: apenas 1 simbolo
            node = heapq.heappop(heap)
            root = _HuffmanNode()
            root.left = node
            return root

        while len(heap) > 1:
            n1 = heapq.heappop(heap)
            n2 = heapq.heappop(heap)

            merged = _HuffmanNode(freq=n1.freq + n2.freq)
            merged.left = n1
            merged.right = n2

            heapq.heappush(heap, merged)

        return heap[0]

    def _generate_codes(self, node, prefix="", code_map=None):
        if code_map is None:
            code_map = {}

        if node is None:
            return code_map

        if node.char is not None:
            code_map[node.char] = prefix or "0"
            return code_map

        self._generate_codes(node.left, prefix + "0", code_map)
        self._generate_codes(node.right, prefix + "1", code_map)

        return code_map

    # ------------------------
    # ENCODE / DECODE
    # ------------------------

    def encode(self, value: str, **params) -> str:
        """
        Codifica uma string usando Huffman.

        Retorna:
            codeword + '|' + tabela serializada

        Exemplo:
            banana -> 010011...|98:00,97:1,110:01
        """
        if not isinstance(value, str) or not value:
            raise ValueError("Huffman requer uma string nao vazia.")

        root = self._build_tree(value)
        code_map = self._generate_codes(root)

        encoded = ''.join(code_map[c] for c in value)

        # serializa tabela usando ord() para evitar colisoes com ':', ',' ou '|'
        table = ",".join(f"{ord(c)}:{code_map[c]}" for c in code_map)

        return f"{encoded}|{table}"

    def decode(self, codeword: str, **params):
        """
        Decodifica uma string Huffman no formato:
            bits|ascii:code,ascii:code,...

        Retorna:
            string original
        """
        if "|" not in codeword:
            raise ValueError(
                "Formato invalido. Esperado: bits|tabela (ex: 0101|97:0,98:1)"
            )

        bits, table_str = codeword.split("|", 1)

        if not bits or not all(c in '01' for c in bits):
            raise ValueError("Codeword invalida: deve conter apenas 0 e 1 na parte binaria.")

        # reconstroi mapa reverso
        reverse_map = {}
        entries = table_str.split(",")

        for entry in entries:
            if ":" not in entry:
                raise ValueError(f"Entrada invalida na tabela: '{entry}'")

            char_ascii, code = entry.split(":", 1)
            try:
                # Usa chr() para reverter o codigo ASCII para caractere
                reverse_map[code] = chr(int(char_ascii))
            except ValueError:
                raise ValueError(f"Codigo de caractere invalido na tabela: '{char_ascii}'")

        decoded = []
        buffer = ""

        for bit in bits:
            buffer += bit
            if buffer in reverse_map:
                decoded.append(reverse_map[buffer])
                buffer = ""

        if buffer:
            raise ValueError("Codeword incompleta ou tabela invalida (sobraram bits).")

        return "".join(decoded)