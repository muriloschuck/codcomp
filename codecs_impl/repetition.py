"""
Codigo de Repeticao Ri

Codificacao de canal por repeticao de bits.

Para cada bit da mensagem original, repete-o Ri vezes.
Na decodificacao, agrupa de Ri em Ri bits e aplica votacao por maioria.

Exemplo (R3):
    Entrada: 5 (binario: 101)
    Codificado: 111 000 111
    Se receber com erro: 110 000 111
    Votacao: 1 0 1 -> 5 (corrigido!)
"""

from codecs_impl.base import BaseCodec


class RepetitionCodec(BaseCodec):
    @property
    def name(self) -> str:
        return "Repeticao"

    @property
    def description(self) -> str:
        return "Codigo de repeticao Ri (correcao de erro por votacao por maioria)."

    def get_params_config(self) -> list[dict]:
        return [
            {
                "name": "ri",
                "label": "Ri (repeticoes por bit)",
                "type": "int",
                "default": 3,
                "min": 3,
                "max": 99,
            }
        ]

    def encode(self, value, **params) -> str:
        """
        Codifica um inteiro em codigo de repeticao.

        1. Converte o inteiro para binario
        2. Repete cada bit Ri vezes
        """
        ri = params.get("ri", 3)

        if isinstance(value, int):
            if value < 0:
                raise ValueError(f"Repeticao requer inteiros >= 0. Recebido: {value}")
            bits = format(value, 'b')
        else:
            # caso receba string binaria diretamente
            bits = str(value)
            if not all(c in '01' for c in bits):
                raise ValueError(f"Entrada invalida para repeticao: '{bits}'")

        # repete cada bit Ri vezes
        return ''.join(bit * ri for bit in bits)

    def decode(self, codeword: str, **params):
        """
        Decodifica um codeword de repeticao usando votacao por maioria.

        1. Agrupa os bits em blocos de tamanho Ri
        2. Para cada bloco, conta 0s e 1s e ve a maioria
        3. Reconstroi o binario original
        4. Converte de volta para inteiro
        """
        ri = params.get("ri", 3)

        # checa se o codeword tem tamanho multiplo de Ri
        if len(codeword) % ri != 0:
            raise ValueError(
                f"Tamanho do codeword ({len(codeword)}) nao e multiplo de Ri ({ri})."
            )

        # votacao por maioria em cada grupo
        bits_corrigidos = []
        for i in range(0, len(codeword), ri):
            grupo = codeword[i:i + ri]
            ones = grupo.count('1')
            if ones > ri // 2:
                bits_corrigidos.append('1')
            else:
                bits_corrigidos.append('0')

        binario_corrigido = ''.join(bits_corrigidos)

        # converte de volta para inteiro
        return int(binario_corrigido, 2)

    def validate_encode_input(self, raw_input: str) -> tuple[bool, str]:
        if not raw_input or not raw_input.strip():
            return False, "Entrada nao pode ser vazia."
        return True, ""

    def validate_decode_input(self, raw_input: str) -> tuple[bool, str]:
        if not raw_input or not raw_input.strip():
            return False, "Entrada nao pode ser vazia."
        tokens = raw_input.strip().split()
        for token in tokens:
            if not all(c in '01' for c in token):
                return False, f"Codeword '{token}' contem caracteres invalidos. Use apenas 0 e 1."
        return True, ""
