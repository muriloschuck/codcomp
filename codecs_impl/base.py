"""
para um novo codec:
1. crie uma classe que herda de BaseCodec
2. implemente os metodos: encode, decode
3. sobrescreva validate_encode_input e validate_decode_input se necessario
4. defina get_params_config() para parametros extras da GUI
5. adicione o codec em codecs_impl/__init__.py
"""

from abc import ABC, abstractmethod

class BaseCodec(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        # nome do codec para exibicao na GUI
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        # descricao curta do codec para exibicao na GUI
        ...

    @abstractmethod
    def encode(self, value, **params) -> str:
        """
        codifica um valor e retorna a representacao binaria como string.

        Args:
            value: O valor a ser codificado (tipo depende do codec).
            **params: Parametros adicionais do codec (ex: divisor m para Golomb).

        Returns:
            String de bits (ex: '01101').

        Raises:
            ValueError: Se o valor for invalido para este codec.
            NotImplementedError: Se o codec ainda nao foi implementado.
        """
        ...

    @abstractmethod
    def decode(self, codeword: str, **params):
        """
        decodifica uma codeword binaria e retorna o valor original.

        Args:
            codeword: String de bits (ex: '01101').
            **params: Parametros adicionais do codec (ex: divisor m para Golomb).

        Returns:
            O valor decodificado (tipo depende do codec).

        Raises:
            ValueError: Se a codeword for invalida para este codec.
            NotImplementedError: Se o codec ainda nao foi implementado.
        """
        ...

    def validate_encode_input(self, raw_input: str) -> tuple[bool, str]:
        """
        valida a entrada do usuario para codificacao.

        Args:
            raw_input: String inserida pelo usuario.

        Returns:
            Tupla (valido: bool, mensagem_erro: str).
        """
        if not raw_input or not raw_input.strip():
            return False, "Entrada nao pode ser vazia."
        return True, ""

    def validate_decode_input(self, raw_input: str) -> tuple[bool, str]:
        """
        valida a entrada do usuario para decodificacao.

        Args:
            raw_input: String de bits inserida pelo usuario.

        Returns:
            Tupla (valido: bool, mensagem_erro: str).
        """
        if not raw_input or not raw_input.strip():
            return False, "Entrada nao pode ser vazia."
        # Verifica se contem apenas 0s e 1s (ignorando espacos)
        tokens = raw_input.strip().split()
        for token in tokens:
            if not all(c in '01' for c in token):
                return False, f"Codeword '{token}' contem caracteres invalidos. Use apenas 0 e 1."
        return True, ""

    def get_params_config(self) -> list[dict]:
        """
        retorna configuracao de parametros extras para a GUI.

        Cada parametro e um dicionario com:
            - 'name': str - nome do parametro (usado como chave em **params)
            - 'label': str - label para exibicao na GUI
            - 'type': str - tipo do parametro ('int', 'float', 'str')
            - 'default': any - valor padrao
            - 'min': (opcional) valor minimo
            - 'max': (opcional) valor maximo

        Returns:
            Lista de dicionarios com a configuracao dos parametros.
        """
        return []

    def parse_encode_input(self, raw_input: str) -> list:
        """
        converte a entrada do usuario em uma lista de valores para codificacao.
        implementacao padrao: separa por espacos e retorna strings.
        subclasses podem sobrescrever para converter tipos (ex: int).

        Args:
            raw_input: String inserida pelo usuario.

        Returns:
            Lista de valores prontos para codificacao.
        """
        return raw_input.strip().split()

    def parse_decode_input(self, raw_input: str) -> list[str]:
        """
        converte a entrada do usuario em uma lista de codewords para decodificacao.
        implementacao padrao: separa por espacos.

        Args:
            raw_input: String inserida pelo usuario.

        Returns:
            Lista de strings de bits.
        """
        return raw_input.strip().split()
