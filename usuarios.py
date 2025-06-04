import json
import os
import datetime
from enum import Enum

class Errors(int, Enum):
    
    SUCESSO = 0
    ARQUIVO_NAO_ENCONTRADO_ERRO = 1
    CAMPO_OBRIGATORIO_ERRO = 2
    TIPO_DE_QUANTIDADE_INCORRETO = 3
    TIPO_DE_PRECO_INCORRETO = 4
    TIPO_DE_VALOR_TOTAL_INCORRETO = 5
    FORMATO_INVALIDO_DA_DATA = 6
    USUARIO_NAO_REMOVIDO = 7
    DADO_NAO_REMOVIDO = 8
    USUARIO_NAO_ENCONTRADO = 9
    USUARIO_JA_EXISTE = 10

class Usuarios:
    def __init__(self, arquivo_json: str):
        self._arquivo_json: str = arquivo_json  # Nome do arquivo JSON
        self._usuarios: dict[str, list] = {}
        self.usuario_selecionado: str = ""

        # IMPORTAR USUÁRIOS CASO EXISTA O ARQUIVO
        if os.path.exists(self._arquivo_json):
            self._importar_dados()
            self._usuarios[self.usuario_selecionado].sort(key=lambda x: x["data_negociacao"])
            self._salvar()

    def adicionar(self, nome: str):
        """Adiciona um usuário se ele não existir."""
        if nome and nome not in self._usuarios:
            self._usuarios[nome] = []
            self.usuario_selecionado = nome
            self._salvar()
            return Errors.SUCESSO
        return Errors.USUARIO_JA_EXISTE

    def editar(self, nome: str, novo_nome: str):
        """Renomeia um usuário se o novo nome não existir."""
        if nome in self._usuarios and novo_nome and novo_nome not in self._usuarios:
            aux = {}
            for key, value in self._usuarios.items():
                if key == nome:
                    aux[novo_nome] = value
                else:
                    aux[key] = value
            self._usuarios = aux
            self.usuario_selecionado = novo_nome
            self._salvar()
            return Errors.SUCESSO
        return Errors.USUARIO_JA_EXISTE

    def _importar_dados(self):
        """Carrega os dados do arquivo JSON, convertendo strings de data para datetime."""
        try:
            with open(self._arquivo_json, "r") as file:
                data = json.load(file)

                self._usuarios = data.get("_usuarios", {})
                self.usuario_selecionado = data.get("_usuario_selecionado", "")

                # Convertendo strings de data para datetime
                for usuario, transacoes in self._usuarios.items():
                    for transacao in transacoes:
                        if "data_negociacao" in transacao:
                            transacao["data_negociacao"] = datetime.datetime.strptime(
                                transacao["data_negociacao"], "%d/%m/%Y"
                            )

        except FileNotFoundError:
            return Errors.ARQUIVO_NAO_ENCONTRADO_ERRO

    def inserir_dados(self, nome: str = None, **kwargs):
        """Insere dados no usuário selecionado, garantindo a conversão correta dos tipos e ordenação por data."""
        if self.usuario_selecionado in self._usuarios:

            if nome:
                self.selecionar(nome, salvar=False)

            # Campos esperados e seus tipos
            campos_esperados = {
                "ativo": str,
                "ordem": str,
                "data_negociacao": (str, datetime.datetime),
                "Q": (int, str),
                "P": (float, str),
                "Vtotal": (float, str),
            }

            # Verifica se todos os campos estão presentes
            for campo, tipo in campos_esperados.items():
                if campo not in kwargs:
                    return Errors.CAMPO_OBRIGATORIO_ERRO

            try:
                kwargs["Q"] = int(kwargs["Q"])  # Converte para inteiro
            except (ValueError, TypeError):
                return Errors.TIPO_DE_QUANTIDADE_INCORRETO

            try:
                kwargs["P"] = float(kwargs["P"])  # Converte para float
            except (ValueError, TypeError):
                return Errors.TIPO_DE_PRECO_INCORRETO

            try:
                kwargs["Vtotal"] = float(kwargs["Vtotal"])  # Converte para float
            except (ValueError, TypeError):
                return Errors.TIPO_DE_VALOR_TOTAL_INCORRETO

            try:
                kwargs["data_negociacao"] = datetime.datetime.strptime(kwargs["data_negociacao"], "%d/%m/%Y")
            except ValueError:
                return Errors.FORMATO_INVALIDO_DA_DATA

            # Adiciona a nova transação
            self._usuarios[self.usuario_selecionado].append(kwargs)

            # Ordena as transações pela data mais antiga primeiro
            self._usuarios[self.usuario_selecionado].sort(key=lambda x: x["data_negociacao"])

            self._salvar()

            return Errors.SUCESSO

    def remover(self, nome: str):
        """Remove um usuário pelo nome."""
        if nome in self._usuarios:
            self._usuarios.pop(nome)
            self.usuario_selecionado = next(reversed(self._usuarios), "")
            self._salvar()
            return Errors.SUCESSO
        return Errors.USUARIO_NAO_REMOVIDO

    def remover_dados(self, indice:int, nome:str=None):
        """Remove uma transação pelo índice."""

        if nome: self.selecionar(nome, salvar=False)

        if self.usuario_selecionado in self._usuarios:
            if 0 <= indice < len(self._usuarios[self.usuario_selecionado]):
                self._usuarios[self.usuario_selecionado].pop(indice)
                self._usuarios[self.usuario_selecionado].sort(key=lambda x: x["data_negociacao"])
                self._salvar()
                return Errors.SUCESSO
        return Errors.DADO_NAO_REMOVIDO

    def _salvar(self):
        """Salva os usuários no arquivo JSON, convertendo datetime para string."""

        aux = {
            usuario: [transacao.copy() for transacao in transacoes]
            for usuario, transacoes in self._usuarios.items()
        }

        dados_exportar = {
            "_usuarios": aux,
            "_usuario_selecionado": self.usuario_selecionado,
        }

        # Converter datas datetime para string antes de salvar
        for usuario, transacoes in dados_exportar["_usuarios"].items():
            for transacao in transacoes:
                if "data_negociacao" in transacao and isinstance(transacao["data_negociacao"], datetime.datetime):
                    transacao["data_negociacao"] = transacao["data_negociacao"].strftime("%d/%m/%Y")

        with open(self._arquivo_json, "w") as file:
            json.dump(dados_exportar, file, indent=4)

    def selecionar(self, nome:str, salvar=True):
        """Seleciona um usuário existente."""
        if nome in self._usuarios:
            self.usuario_selecionado = nome
            if salvar: self._salvar()
            return Errors.SUCESSO
        return Errors.USUARIO_NAO_ENCONTRADO

    def listar(self):
        """Retorna o dicionário de usuários."""
        return list(self._usuarios.keys())

    def obter_dados(self):
        """Retorna os dados do usuário selecionado."""
        if self.usuario_selecionado in self._usuarios:
            return self._usuarios[self.usuario_selecionado]
        return Errors.USUARIO_NAO_ENCONTRADO