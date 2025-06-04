import flet as ft
import usuarios
import datetime
import tickers
import os
import json
import yfinance as yf
import re
import webbrowser
from dateutil.relativedelta import relativedelta
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException,UnexpectedAlertPresentException
import time

class App:
    def __init__(self, pagina:ft.Page):
        self.pagina = pagina
        self.pagina.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.pagina.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.pagina.locale_configuration = ft.LocaleConfiguration(
            current_locale=ft.Locale("pt", "BR"),
            supported_locales=[ft.Locale("pt", "BR")]
        )
        self.botao_de_tema = ft.IconButton(icon=ft.Icons.LIGHT_MODE if self.pagina.theme_mode == ft.ThemeMode.LIGHT else ft.Icons.DARK_MODE, icon_color= ft.Colors.BLACK, on_click= lambda e: self.mudar_tema("Next"))

        self.pagina.bgcolor = ft.Colors.SURFACE
        self.configuracao = {
            "tema": 0
        }
        
        if not os.path.exists("configuracao.json"):
            with open("configuracao.json", "w") as arquivo:
                json.dump(self.configuracao, arquivo, indent=4)
        else:
            with open("configuracao.json", "r") as arquivo:
                self.configuracao = json.load(arquivo)

        self.mudar_tema(self.configuracao["tema"])

        # COLUNA PRINCIPAL
        self.coluna_principal = ft.Column(expand=True, scroll="auto")

        # DEFININDO USUÁRIOS
        self.usuarios = usuarios.Usuarios("lancamentos_do_usuario.json")

        # GUARDA OS ATIVOS DO USUÁRIO SELECIONADO POR TICKER
        self.ativos = {}

        self.historico_proventos = {}

        self.valor_aplicado_spinner = ft.ProgressRing(color=ft.Colors.GREY, height=15, width=15)
        self.valor_liquido_spinner = ft.ProgressRing(color=ft.Colors.GREY, height=15, width=15)
        self.variacao_total_spinner = ft.ProgressRing(color=ft.Colors.GREY, height=15, width=15)
        self.tabela_proventos_spinner = ft.ProgressRing(color=ft.Colors.ON_SURFACE_VARIANT, height=20, width=20)
        self.tabela_historico_proventos_spinner = ft.ProgressRing(color=ft.Colors.ON_SURFACE_VARIANT, height=20, width=20)
        self.tabela_resumo_spinner = ft.ProgressRing(color=ft.Colors.ON_SURFACE_VARIANT, height=20, width=20)
        self.grafico_evolucao_patrimonial_spinner = ft.ProgressRing(color=ft.Colors.ON_SURFACE_VARIANT, height=20, width=20)
        self.grafico_porcetagem_na_carteira_spinner = ft.ProgressRing(color=ft.Colors.ON_SURFACE_VARIANT, height=20, width=20)

        self.mudar_visibilidade_dos_spinners(False)

        # SPINNER DE CARREGAMENTO
        self.spinner = ft.ProgressRing(color=ft.Colors.ON_SURFACE_VARIANT, visible=True)
        self.pagina.add(self.spinner)

        # CARREGAR OS TICKERS
        if not os.path.exists("tickers.json"):
            self.tickers = tickers.obter_tikers()
            with open("tickers.json", "w") as arquivo:
                json.dump(self.tickers, arquivo, indent=4)
        else:
            with open("tickers.json", "r") as arquivo:
                self.tickers = json.load(arquivo)

        self.dialogo_de_alerta = ft.AlertDialog(
            actions=[
                ft.TextButton(
                    "Ok", on_click=lambda e: self.pagina.close(self.dialogo_de_alerta)
                ),
            ]
        )

        self.dialogo_de_confirmar = ft.AlertDialog(
            on_dismiss=self.on_dimiss,
            actions=[
                ft.TextButton(
                    "Cancelar", on_click=lambda e: self.pagina.close(self.dialogo_de_confirmar)
                ),
                ft.TextButton(
                    "Confirmar"
                ),
            ]
        )

        self.carregar_cabecalho()
        self.carregar_abas()
        self.carregar_aba_resumo()
        self.carregar_aba_proventos()
        self.carregar_aba_graficos()
        self.carregar_aba_lancamentos()
        self.carregar_aba_configuracao()
        self.carregar_carteiras()
        self.carregar_lancamentos()
        self.spinner.visible = False

        self.pagina.add(
            self.coluna_principal
        )

    def on_dimiss(self, e):
        self.pagina.on_keyboard_event = None

    # ADICIONA CABEÇALHO A PÁGINA
    def carregar_cabecalho(self):

        self.valor_aplicado_text = ft.Text(color="#293038", weight=ft.FontWeight.BOLD, size=17)
        self.valor_liquido_text = ft.Text(color="#293038", weight=ft.FontWeight.BOLD, size=17)
        self.variacao_total_text = ft.Text(color="#293038", weight=ft.FontWeight.BOLD, size=17)

        self.carteira_selecionada_text = ft.Text(self.usuarios.usuario_selecionado[:20], color=ft.Colors.BLACK)
        self.menu_de_carteiras = ft.PopupMenuButton(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Carteiras",color=ft.Colors.BLACK, weight=ft.FontWeight.W_900, size=18),
                            ft.Icon(ft.Icons.ARROW_DROP_DOWN, color="#333333")
                        ]
                    ),
                    self.carteira_selecionada_text,
                ]
            ),
            col={"sm": 6, "md": 4, "xl": 2}
        )

        self.coluna_principal.controls.append(
            ft.Container(
                bgcolor=ft.Colors.WHITE,
                padding=10,
                border_radius=ft.border_radius.all(20),
                content=ft.Row(
                    controls=[
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.Text("Carteira", color="#293038", weight=ft.FontWeight.BOLD, size=25),
                                ft.Stack(
                                    controls=[
                                        ft.Container(
                                            content=ft.Icon(name=ft.Icons.CIRCLE_OUTLINED, size=36, color="#293038"),
                                            alignment=ft.alignment.center,
                                        ),
                                        ft.Container(
                                            content=ft.Icon(name=ft.Icons.SHOW_CHART, size=46, color="#D3B583"),
                                            alignment=ft.alignment.center,
                                            margin=ft.margin.only(left=-5, top=2),
                                        ),
                                        ft.Container(
                                            content=ft.Text("1", size=38, weight=ft.FontWeight.W_500, color="#D3B583"),
                                            alignment=ft.alignment.bottom_left,
                                            margin=ft.margin.only(left=-1, top=-5),
                                        ),
                                    ],
                                    width=58,
                                    height=46,
                                )
                            ] 
                        ),
                        ft.Container(
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        ft.Icon(ft.Icons.ATTACH_MONEY_OUTLINED, size=20, color="#293038"),
                                        bgcolor="#CECECE",
                                        border_radius=ft.border_radius.all(5),
                                        padding=5,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text("Valor Aplicado", color="#293038", size=15),
                                            ft.Row(
                                                controls=[
                                                    self.valor_aplicado_text,
                                                    self.valor_aplicado_spinner
                                                ]
                                            )
                                        ],
                                        spacing=0.5,
                                    )
                                ]
                            ),
                        ),
                        ft.Container(
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        ft.Icon(ft.Icons.ATTACH_MONEY_OUTLINED, size=20, color="#293038"),
                                        bgcolor="#CECECE",
                                        border_radius=ft.border_radius.all(5),
                                        padding=5,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text("Saldo Líquido", color="#293038", size=15),
                                            ft.Row(
                                                controls=[
                                                    self.valor_liquido_text,
                                                    self.valor_liquido_spinner
                                                ]
                                            )
                                        ],
                                        spacing=0.5,
                                    )
                                ]
                            ),
                        ),
                        ft.Container(
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        ft.Icon(ft.Icons.ATTACH_MONEY_OUTLINED, size=20, color="#293038"),
                                        bgcolor="#CECECE",
                                        border_radius=ft.border_radius.all(5),
                                        padding=5,
                                    ),
                                    ft.Column(
                                        controls=[
                                            ft.Text("Variação", color="#293038", size=15),
                                            ft.Row(
                                                controls=[
                                                    self.variacao_total_text,
                                                    self.variacao_total_spinner
                                                ]
                                            )
                                        ],
                                        spacing=0.5,
                                    )
                                ]
                            ),
                        ),
                        self.menu_de_carteiras,
                        self.botao_de_tema,
                        ft.ElevatedButton(
                            text="NOVA CARTEIRA",
                            bgcolor="#333333",
                            icon=ft.Icons.ADD,
                            color=ft.Colors.WHITE,
                            icon_color="#D3B583",
                            on_click= lambda e: self.adicionar_carteira()
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            )
        )

    def mudar_visibilidade_dos_spinners(self, visivel:bool):
        
        opacidade = 1 if visivel else 0

        self.valor_aplicado_spinner.opacity = opacidade
        self.valor_liquido_spinner.opacity = opacidade
        self.variacao_total_spinner.opacity = opacidade
        self.tabela_proventos_spinner.opacity = opacidade
        self.tabela_historico_proventos_spinner.opacity = opacidade
        self.tabela_resumo_spinner.opacity = opacidade
        self.grafico_evolucao_patrimonial_spinner.opacity = opacidade
        self.grafico_porcetagem_na_carteira_spinner.opacity = opacidade

    def recarregar_dados(self, visivel:bool=False):

        if visivel:
            self.mudar_visibilidade_dos_spinners(True)
        else:
            self.spinner.visible = True
            self.coluna_principal.visible = False
        self.pagina.update()

        self.carregar_lancamentos()

        if visivel:
            self.mudar_visibilidade_dos_spinners(False)
        else:
            self.spinner.visible = False
            self.coluna_principal.visible = True
        self.pagina.update()

    def mudar_tema(self, tema:str|int):

        temas = tuple(ft.ThemeMode)
        
        if tema == "Next":
            self.configuracao["tema"] = (self.configuracao["tema"] + 1) % 3
            self.pagina.theme_mode = temas[self.configuracao["tema"]]
        else:
            self.pagina.theme_mode = temas[self.configuracao["tema"]]

        match temas[self.configuracao["tema"]]:
            case ft.ThemeMode.SYSTEM:
                self.botao_de_tema.icon = ft.Icons.SETTINGS_BRIGHTNESS
                match self.pagina.platform_brightness:
                    case ft.Brightness.LIGHT:
                        self.pagina.bgcolor = ft.Colors.GREY_400
                    case ft.Brightness.DARK:
                        self.pagina.bgcolor = None

            case ft.ThemeMode.LIGHT:
                self.botao_de_tema.icon = ft.Icons.LIGHT_MODE
                self.pagina.bgcolor = ft.Colors.GREY_400
            case ft.ThemeMode.DARK:
                self.botao_de_tema.icon = ft.Icons.DARK_MODE
                self.pagina.bgcolor = None
        
        with open("configuracao.json", "w") as arquivo: json.dump(self.configuracao, arquivo, indent=4)

        self.pagina.update()

    def adicionar_carteira(self):

        def salvar():
            if self.adicionar_carteira_dialogo.open:
                resposta = self.usuarios.adicionar(caixa_de_texto.value)

                self.pagina.close(self.adicionar_carteira_dialogo)
                if resposta == usuarios.Errors.USUARIO_JA_EXISTE:
                    self.dialogo_de_alerta.content = ft.Text("Usuário já existe", size=16, weight=ft.FontWeight.W_500)
                    self.pagina.open(self.dialogo_de_alerta)
                    self.pagina.on_keyboard_event = lambda e: self.pagina.close(self.dialogo_de_alerta) if e.key == "Enter" else None
                else:
                    self.menu_de_carteiras.items.append(
                        ft.MenuItemButton(
                            data=self.usuarios.usuario_selecionado,
                            on_click=self.selecionar_carteira,
                            content=ft.Text(self.usuarios.usuario_selecionado)
                        )
                    )
                    self.carteira_selecionada_text.value = self.usuarios.usuario_selecionado[:20]
                    self.caixa_texto_configuracao.value = self.usuarios.usuario_selecionado


                self.recarregar_dados(True)

        # CRIAÇÃO DO CAMPO DE TEXTO PARA INSERIR NOVA CARTEIRA
        caixa_de_texto = ft.TextField(label="Nome da Carteira")

        # CRIAÇÃO DO DIALOGO COM AS OPÇÕES "Salvar" E "Cancelar"
        self.adicionar_carteira_dialogo = ft.AlertDialog(
            actions=[
                ft.TextButton(
                    "Cancelar", on_click=lambda e: self.pagina.close(self.adicionar_carteira_dialogo)
                ),
                ft.TextButton(
                    "Salvar", on_click=lambda e: salvar()
                ),
            ],
            content=caixa_de_texto,
        )
        self.pagina.open(self.adicionar_carteira_dialogo)
        caixa_de_texto.focus()
        self.pagina.on_keyboard_event = lambda e: salvar() if e.key == "Enter" else None
        self.pagina.update()
    
    def selecionar_carteira(self, e:ft.ControlEvent):

        self.usuarios.selecionar(e.control.data)
        self.carteira_selecionada_text.value = self.usuarios.usuario_selecionado[:20]
        self.caixa_texto_configuracao.value = self.usuarios.usuario_selecionado
        self.recarregar_dados()

    def carregar_carteiras(self):
        
        self.menu_de_carteiras.items = []

        for nome in self.usuarios.listar():
            self.menu_de_carteiras.items.append(
                ft.MenuItemButton(
                    data=nome,
                    on_click=self.selecionar_carteira,
                    content=ft.Text(nome)
                )
            )
    
    def editar_carteira(self):

        resposta = self.usuarios.editar(self.usuarios.usuario_selecionado, self.caixa_texto_configuracao.value)

        if resposta == usuarios.Errors.USUARIO_JA_EXISTE:
            self.dialogo_de_alerta.content = ft.Text("Usuário já existe" if self.usuarios.usuario_selecionado else "Selecione um usuário", size=16, weight=ft.FontWeight.W_500)
            self.pagina.open(self.dialogo_de_alerta)
            self.caixa_texto_configuracao.value = self.usuarios.usuario_selecionado
            self.pagina.on_keyboard_event = lambda e: self.pagina.close(self.dialogo_de_alerta) if e.key == "Enter" else None
            self.pagina.update()

        else:
            self.carteira_selecionada_text.value = self.usuarios.usuario_selecionado[:20]
            self.carregar_carteiras()
        self.pagina.update()

    def remover_carteira(self):

        def remover():
            if self.dialogo_de_confirmar.open:
                self.usuarios.remover(self.usuarios.usuario_selecionado)
                self.carteira_selecionada_text.value = self.usuarios.usuario_selecionado
                self.caixa_texto_configuracao.value = self.usuarios.usuario_selecionado
                self.carregar_carteiras()
                self.pagina.close(self.dialogo_de_confirmar)
                self.recarregar_dados()

        self.dialogo_de_confirmar.content = ft.Text(f"Você tem certeza que quer deletar {self.usuarios.usuario_selecionado}?" if self.usuarios.usuario_selecionado else "Não há usuário para ser removido", size=16, weight=ft.FontWeight.W_500)
        self.dialogo_de_confirmar.actions[1].on_click = lambda e: remover()
        self.pagina.open(self.dialogo_de_confirmar)
        self.pagina.on_keyboard_event = lambda e: remover() if e.key == "Enter" else None
        self.pagina.update()

    # CRIA AS ABAS DO PROGRAMA
    def carregar_abas(self):

        self.abas_widget = ft.Tabs(
            tabs=[
                ft.Tab(text="Resumo"),
                ft.Tab(text="Proventos"),
                ft.Tab(text="Gráficos"),
                ft.Tab(text="Lançamentos"),
                ft.Tab(text="Configuração")
            ],
        )
        
        self.coluna_principal.controls.append(
            ft.Column(
                expand=True,
                controls=[
                    ft.Container(
                        content=self.abas_widget,
                        padding=20,
                    )
                ]
            )
        ) 

    # ABA RESUMO
    def carregar_aba_resumo(self):

        self.tabela_resumo = ft.DataTable(
            bgcolor= ft.Colors.ON_INVERSE_SURFACE,
            border_radius= 10,
            expand=True,
            vertical_lines= ft.BorderSide(0.7),
            columns=[
                ft.DataColumn(ft.Text('ATIVO')),
                ft.DataColumn(ft.Text('QUANTIDADE')),
                ft.DataColumn(ft.Text('PREÇO MÉDIO')),
                ft.DataColumn(ft.Text('PREÇO ATUAL')),
                ft.DataColumn(ft.Text('VARIAÇÃO %')),
                ft.DataColumn(ft.Text('SALDO')),
                ft.DataColumn(ft.Text('% CARTEIRA')),
            ],
        )

        self.abas_widget.tabs[0].content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # Centraliza a coluna
            expand=True,
            controls=[
                ft.Container(height=20),
                ft.Row(
                    expand=True,
                    scroll=True,
                    controls=[
                        ft.Container(
                            border=ft.border.all(0.5, color=ft.Colors.ON_SURFACE),
                            border_radius=ft.border_radius.all(10),
                            expand=True,
                            margin=20,
                            padding=20,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                controls=[
                                    ft.Column(
                                        scroll=True,
                                        controls=[
                                            ft.Row(
                                                controls=[
                                                    ft.Text("Resumo", size=20, weight=ft.FontWeight.W_500),
                                                    ft.IconButton(ft.Icons.SYNC, icon_color=ft.Colors.ON_SURFACE, on_click=lambda e: self.recarregar_dados(True)),
                                                    self.tabela_resumo_spinner
                                                ]
                                            ),
                                            self.tabela_resumo,
                                        ]
                                    ),
                                ],
                            )
                        ),
                    ]
                )
            ]
        )
    
    def carregar_tabela_resumo(self):

        def ver_informacoes_do_ativo(e: ft.ControlEvent):
            webbrowser.open(rf"https://investidor10.com.br/fiis/{e.control.text}/")

        # Limpa as linhas da tabela
        self.tabela_resumo.rows = []

        VaplicadoTotal = 0
        VliquidoTotal = 0

        # Primeiro loop: atualiza os dados de cada ativo e acumula os totais
        for ativo, dados in self.resumo_ativos.items():
            # Calcula o preço médio (PM) e a quantidade (Q)
            dados["PM"] = dados["Vtotal"] / (dados["Qcompra"] or 1)
            dados["Q"] = dados["Qcompra"] - dados["Qvenda"]

            # Atualiza o preço atual (PA) e calcula saldo e variação
            dados["PA"] = self.obter_cotacao(ativo) or 0
            pct = dados["PA"] / (dados["PM"] or 1)
            dados["saldo"] = dados["PM"] * dados["Q"] * pct
            dados["variacao"] = (pct - 1) * 100

            # Soma os totais
            VaplicadoTotal += dados["PM"] * dados["Q"]
            VliquidoTotal += dados["saldo"]

        # Segundo loop: cria as linhas da tabela somente para ativos com quantidade positiva
        for ativo, dados in self.resumo_ativos.items():
            if dados["Q"] > 0:
                # Calcula a porcentagem relativa do saldo do ativo
                dados["porcentagem"] = (dados["saldo"] / (VliquidoTotal or 1)) * 100

                datarow = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.TextButton(ativo, on_click=ver_informacoes_do_ativo)),
                        ft.DataCell(ft.Text(dados["Q"])),
                        ft.DataCell(ft.Text(f'R$ {dados["PM"]:,.2f}')),
                        ft.DataCell(ft.Text(f'R$ {dados["PA"]:,.2f}')),
                        ft.DataCell(
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.ARROW_DROP_DOWN if dados["variacao"] < 0 else ft.Icons.ARROW_DROP_UP, color=ft.Colors.RED if dados["variacao"] < 0 else ft.Colors.GREEN),
                                    ft.Text(f'{dados["variacao"]:,.2f} %')
                                ]
                            )
                        ),
                        ft.DataCell(ft.Text(f'R$ {dados["saldo"]:,.2f}')),
                        ft.DataCell(ft.Text(f'{dados["porcentagem"]:.2f} %')),
                    ]
                )
                self.tabela_resumo.rows.append(datarow)

        # Atualiza os textos dos totais
        self.valor_aplicado_text.value = f"R$ {VaplicadoTotal:,.2f}"
        self.valor_liquido_text.value = f"R$ {VliquidoTotal:,.2f}"

        variacao_total = ((VliquidoTotal - VaplicadoTotal) / (VaplicadoTotal or 1)) * 100
        self.variacao_total_text.color = (
            ft.Colors.GREEN if variacao_total > 0 else
            ft.Colors.RED if variacao_total < 0 else
            "#293038"
        )
        self.variacao_total_text.value = f"{variacao_total:.2f} %"


    def carregar_aba_proventos(self):
        self.tabela_proventos = ft.DataTable(
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_radius=10,
            expand=True,
            vertical_lines=ft.BorderSide(0.7),
            columns=[
                ft.DataColumn(ft.Text('ANO')),
                ft.DataColumn(ft.Text('JAN')),
                ft.DataColumn(ft.Text('FEV')),
                ft.DataColumn(ft.Text('MAR')),
                ft.DataColumn(ft.Text('ABR')),
                ft.DataColumn(ft.Text('MAI')),
                ft.DataColumn(ft.Text('JUN')),
                ft.DataColumn(ft.Text('JUL')),
                ft.DataColumn(ft.Text('AGO')),
                ft.DataColumn(ft.Text('SET')),
                ft.DataColumn(ft.Text('OUT')),
                ft.DataColumn(ft.Text('NOV')),
                ft.DataColumn(ft.Text('DEC')),
                ft.DataColumn(ft.Text('TOTAL')),
                ft.DataColumn(ft.Text('MÉDIA')),
            ],
        )

        self.tabela_historico_proventos = ft.DataTable(
            bgcolor=ft.Colors.ON_INVERSE_SURFACE,
            border_radius=10,
            expand=True,
            vertical_lines=ft.BorderSide(0.7),
            columns=[
                ft.DataColumn(ft.Text('ATIVO')),
                ft.DataColumn(ft.Text('QUANTIDADE')),
                ft.DataColumn(ft.Text('DATA COM')),
                ft.DataColumn(ft.Text('DATA PAGAMENTO')),
                ft.DataColumn(ft.Text('VALOR DO DIVIDENDO')),
                ft.DataColumn(ft.Text('TOTAL')),
            ],
        )

        self.grafico_evolucao_dividendos = ft.BarChart(
            border=ft.border.all(1, ft.Colors.GREY_600),
            bottom_axis=ft.ChartAxis(labels_size=40),
            left_axis=ft.ChartAxis(
                labels_size=40, title=ft.Text("Dinheiro"), title_size=40
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.Colors.ON_SURFACE, width=1, dash_pattern=[3, 3]
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(1, ft.Colors.ON_SURFACE),
            max_y=110,
            interactive=True,
            # expand removido aqui para evitar quebra de layout
        )

        self.soma_total_proventos = ft.Text("Total: R$ 0.00", size=17, weight=ft.FontWeight.W_600)

        self.abas_widget.tabs[1].content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            controls=[
                ft.Container(height=20),
                ft.Container(
                    border=ft.border.all(0.5, color=ft.Colors.ON_SURFACE),
                    border_radius=ft.border_radius.all(10),
                    margin=20,
                    padding=20,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Proventos", size=20, weight=ft.FontWeight.W_500),
                                    self.tabela_proventos_spinner,
                                ]
                            ),
                            ft.Container(height=10),
                            ft.Row(
                                scroll=True,
                                controls=[
                                    ft.Column(
                                        horizontal_alignment=ft.CrossAxisAlignment.END,
                                        expand=True,
                                        scroll=True,
                                        controls=[
                                            self.tabela_proventos,
                                        ]
                                    ),
                                ]
                            ),
                            ft.Container(height=10),
                            ft.Container(
                                alignment=ft.Alignment(1,0.5),
                                content=self.soma_total_proventos,
                            ),
                            ft.Container(height=30),
                            self.grafico_evolucao_dividendos,
                        ]
                    ),
                ),
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Row(
                        expand=True,
                        scroll=True,
                        controls=[
                            ft.Container(
                                border=ft.border.all(0.5, color=ft.Colors.ON_SURFACE),
                                border_radius=ft.border_radius.all(10),
                                expand=True,
                                padding=20,
                                content=ft.Column(
                                    expand=True,
                                    scroll=True,
                                    height=400,
                                    controls=[
                                        ft.Row(
                                            controls=[
                                                ft.Text("Histórico", size=20, weight=ft.FontWeight.W_500),
                                                self.tabela_historico_proventos_spinner
                                            ]
                                        ),
                                        self.tabela_historico_proventos,
                                    ]
                                )
                            )
                        ]
                    )
                )
            ]
        )

    def carregando_tabela_proventos_mais_grafico(self):
        self.tabela_proventos.rows = []
        self.grafico_evolucao_dividendos.bar_groups = []
        self.grafico_evolucao_dividendos.bottom_axis.labels = []
        lancamentos = self.usuarios.obter_dados()

        if lancamentos and not isinstance(lancamentos, usuarios.Errors):

            ano_inicial = lancamentos[0]['data_negociacao'].year
            ano_final = datetime.datetime.today().year + 1

            # print(len(self.historico_proventos), self.historico_proventos)

            proventos_por_mes = {}
            for ano in range(ano_inicial, ano_final):
                proventos_por_mes[str(ano)] = {}
                for j in range(1, 13):
                    proventos_por_mes[str(ano)][f"{j:02d}"] = 0.0
                proventos_por_mes[str(ano)]["total"] = 0.0
                proventos_por_mes[str(ano)]["media"] = 0.0

            for data in self.historico_proventos:
                for ativo in self.historico_proventos[data]:
                    if "data_pagamento" in self.historico_proventos[data][ativo] and float(self.historico_proventos[data][ativo]["Q"]) > 0:
                        mes, ano = self.historico_proventos[data][ativo]["data_pagamento"][3:].split("/")
                        dados = self.historico_proventos[data][ativo]

                        proventos_por_mes[ano][mes] += float(dados["Q"]) * float(dados.get("valor_por_cota", 0))

            total_total = 0.0
            for ano in proventos_por_mes:
                total = 0.0
                for mes in proventos_por_mes[ano]:
                    total += proventos_por_mes[ano][mes]

                proventos_por_mes[ano]["total"] = total
                proventos_por_mes[ano]["media"] = total / 12
                total_total += total

            for ano in proventos_por_mes:
                datarow = ft.DataRow(
                    cells=[ft.DataCell(ft.Text(ano))]
                )
                for mes in proventos_por_mes[ano]:

                    datarow.cells.append(ft.DataCell(ft.Text(f"{proventos_por_mes[ano][mes]:,.2f}")))

                self.tabela_proventos.rows.append(datarow)

            data_atual = datetime.datetime.today() - relativedelta(months=11)
            um_mes = relativedelta(months=1)

            valor_max = 0

            for i in range(12):
                mes, ano = data_atual.strftime("%m/%Y").split("/")
                if (ano in proventos_por_mes and mes in proventos_por_mes[ano]):
                    self.grafico_evolucao_dividendos.bar_groups.append(
                        ft.BarChartGroup(
                            x=i,
                            bar_rods=[
                                ft.BarChartRod(
                                    from_y=0,
                                    to_y=proventos_por_mes[ano][mes],
                                    width=40,
                                    color=ft.Colors.BLUE_800,
                                    tooltip=f"R$ {proventos_por_mes[ano][mes]:.2f}",
                                    border_radius=ft.border_radius.only(top_left=4, top_right=4),
                                ),
                            ],
                        )
                    )
                    self.grafico_evolucao_dividendos.bottom_axis.labels.append(
                        ft.ChartAxisLabel(
                            value=i,
                            label=ft.Container(ft.Text(f"{mes}/{ano}"), padding=10),
                        )
                    )
                    valor_max = proventos_por_mes[ano][mes] if proventos_por_mes[ano][mes] > valor_max else valor_max
                data_atual += um_mes

            self.grafico_evolucao_dividendos.max_y = valor_max * 1.1
            self.soma_total_proventos.value = f"Total: R$ {total_total:,.2f}"

    def carregar_tabela_historico_de_proventos(self):

        lancamentos = self.usuarios.obter_dados()
        self.tabela_historico_proventos.rows = []

        self.historico_proventos = {}
        um_mes = relativedelta(months=1)

        if not isinstance(lancamentos, usuarios.Errors) and lancamentos: 
            for lancamento in lancamentos:

                ativo = lancamento["ativo"]
                proventos = self.pegar_proventos_fiis(ativo)

                if not proventos.empty:
                    data_com = proventos["Data Com"]
                    filtro = (lancamento["data_negociacao"] < data_com) | (lancamento["data_negociacao"] == data_com)
                    proventos_filtrados = proventos[filtro]
                    Q = lancamento["Q"]

                    if not proventos_filtrados.empty:
                        data_pagamento = proventos_filtrados["Pagamento"].iloc[-1]
                        mes_ano_pagamento = data_pagamento.strftime("%m/%Y")
                        self.historico_proventos.setdefault(mes_ano_pagamento, {})
                        if not ativo in self.historico_proventos[mes_ano_pagamento]:
                            self.historico_proventos[mes_ano_pagamento].setdefault(
                                ativo, {
                                    "Q": Q if lancamento["ordem"] == "Compra" else -Q,
                                }
                            )
                        else:
                            self.historico_proventos[mes_ano_pagamento][ativo]["Q"] += Q if lancamento["ordem"] == "Compra" else -Q

            data_atual = lancamentos[0]["data_negociacao"]
            quantidade_de_meses = self.diferenca_meses(data_atual)
            for _ in range(quantidade_de_meses):
                mes_ano = data_atual.strftime("%m/%Y")
                proximo_mes_ano = (data_atual + um_mes).strftime("%m/%Y")
                self.historico_proventos.setdefault(mes_ano, {})
                self.historico_proventos.setdefault(proximo_mes_ano, {})

                for ativo in self.historico_proventos[mes_ano]:

                    Q = self.historico_proventos[mes_ano][ativo]["Q"]

                    self.historico_proventos.setdefault(proximo_mes_ano, {}).setdefault(ativo, {"Q": 0})
                    self.historico_proventos[proximo_mes_ano][ativo]["Q"] += Q

            
                data_atual += um_mes

            data_atual = datetime.datetime.today()
            for _ in range(quantidade_de_meses):
                mes_ano = data_atual.strftime("%m/%Y")

                for ativo in self.historico_proventos[mes_ano]:
                    proventos = self.pegar_proventos_fiis(ativo)

                    if not proventos.empty:

                        data_com = proventos["Pagamento"]
                        filtro = (data_com.dt.month == data_atual.month) & (data_com.dt.year == data_atual.year)
                        proventos_filtrados = proventos[filtro]

                        if not proventos_filtrados.empty:

                            if self.historico_proventos[mes_ano][ativo]["Q"] > 0:

                                self.historico_proventos[mes_ano][ativo]["data_com"] = proventos_filtrados["Data Com"].iloc[0].strftime("%d/%m/%Y")
                                self.historico_proventos[mes_ano][ativo]["data_pagamento"] = proventos_filtrados["Pagamento"].iloc[0].strftime("%d/%m/%Y")
                                self.historico_proventos[mes_ano][ativo]["valor_por_cota"] = proventos_filtrados['Valor'].iloc[0]
                                
                                datarow = ft.DataRow(
                                    cells=[
                                        ft.DataCell(ft.Text(ativo)),
                                        ft.DataCell(ft.Text(self.historico_proventos[mes_ano][ativo]["Q"])),
                                        ft.DataCell(ft.Text(self.historico_proventos[mes_ano][ativo]["data_com"])),
                                        ft.DataCell(ft.Text(self.historico_proventos[mes_ano][ativo]["data_pagamento"])),
                                        ft.DataCell(ft.Text(f"R$ {self.historico_proventos[mes_ano][ativo]['valor_por_cota']:,.2f}")),
                                        ft.DataCell(ft.Text(f"R$ {(self.historico_proventos[mes_ano][ativo]['Q'] * self.historico_proventos[mes_ano][ativo]['valor_por_cota']):,.2f}")),
                                    ]
                                )
                                self.tabela_historico_proventos.rows.append(datarow)

                data_atual -= um_mes
            # print(self.historico_proventos)

    def pegar_proventos_fiis(self, ticker: str, retry: int = 3, timeout_seconds: int = 60) -> pd.DataFrame:
        """
        Obtém o histórico de proventos de um FII pelo ticker.
        Retorna um DataFrame com colunas: Data Com, Pagamento e Valor (float).
        Usa cache em JSON e atualiza no máximo a cada 24 horas.
        Executa o navegador em modo headless para não mostrar a janela.
        """
        cache_dir = "proventos"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{ticker}.json")

        # Decide se precisa refazer raspagem
        need_refresh = True
        dados_limpos = []
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                j = json.load(f)
            last = datetime.datetime.fromisoformat(j.get("last_updated"))
            if datetime.datetime.now() - last < datetime.timedelta(hours=24):
                need_refresh = False
                dados_limpos = j.get("data", [])

        if need_refresh:
            # Função para limpar HTML/SVG em cada célula
            def clean_html(text: str) -> str:
                return re.sub(r'<[^>]+>', '', text).strip()

            # Prepara Selenium em modo headless e carregamento eager
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.page_load_strategy = 'eager'
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(timeout_seconds)

            # Carrega a página com tentativas
            for attempt in range(retry):
                try:
                    driver.get(f"https://investidor10.com.br/fiis/{ticker}/")
                    break
                except TimeoutException:
                    if attempt < retry - 1:
                        time.sleep(2)
                        continue
                    else:
                        driver.quit()
                        raise

            wait = WebDriverWait(driver, 20)
            # Espera tabela aparecer
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#table-dividends-history")))
            # Espera plugin DataTable estar pronto
            wait.until(lambda d: d.execute_script("return typeof jQuery !== 'undefined' && typeof jQuery.fn.DataTable === 'function';"))

            # Suprime alertas de DataTables
            driver.execute_script("window.alert = function(){}; window.confirm = function(){return true;};")

            # Ajusta para exibir todas as linhas
            try:
                driver.execute_script("""
                var dt = jQuery('#table-dividends-history').DataTable();
                dt.page.len(dt.rows().count()).draw(false);
            """)
            except UnexpectedAlertPresentException:
                pass

            time.sleep(2)

            # Extrai todos os dados
            raw = driver.execute_script("""
            var dt = jQuery('#table-dividends-history').DataTable();
            return dt.rows().data().toArray();
            """)
            driver.quit()

            # Limpa e estrutura
            dados_limpos = []
            for row in raw:
                tipo, data_base, data_pag, valor_html = row
                m = re.search(r"\d+[\.,]\d+", valor_html)
                val = m.group(0) if m else clean_html(valor_html)
                dados_limpos.append({
                    "Data Com": clean_html(data_base),
                    "Pagamento": clean_html(data_pag),
                    "Valor": val
                })

            # Grava cache
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({"last_updated": datetime.datetime.now().isoformat(), "data": dados_limpos},
                        f, ensure_ascii=False)

        # Converte para DataFrame e tipos
        df = pd.DataFrame(dados_limpos)
        df['Data Com'] = pd.to_datetime(df['Data Com'], dayfirst=True)
        df['Pagamento'] = pd.to_datetime(df['Pagamento'], dayfirst=True)
        df['Valor'] = df['Valor'].str.replace(',', '.').astype(float)
        return df[['Data Com', 'Pagamento', 'Valor']]

    
    # ABA GRÁFICOS
    def carregar_aba_graficos(self):

        self.grafico_evolucao_patrimonial = ft.BarChart(
            border=ft.border.all(1, ft.Colors.GREY_600),
            bottom_axis=ft.ChartAxis(labels_size=40),
            left_axis=ft.ChartAxis(
                labels_size=40, title=ft.Text("Dinheiro"), title_size=40
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.Colors.ON_SURFACE, width=1, dash_pattern=[3, 3]
            ),
            tooltip_bgcolor=ft.Colors.with_opacity(1, ft.Colors.ON_SURFACE),
            max_y=110,
            interactive=True,
            expand=True,
        )

        self.grafico_porcetagem_na_carteira = ft.PieChart(
            sections_space=2,
            center_space_radius=80,
            expand=True,
        )
        self.container_porcentagem_na_carteira = ft.Column()
        
        self.layout_graficos = ft.Column(
            controls=[
                ft.Container(
                    border=ft.border.all(0.5, color=ft.Colors.ON_SURFACE),
                    border_radius=ft.border_radius.all(10),
                    margin=20,
                    padding=20,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text("Evolução Patrimonial (12 meses)", size=20, weight=ft.FontWeight.W_500),
                                    self.grafico_evolucao_patrimonial_spinner,
                                ]
                            ),
                            ft.Container(height=10),
                            self.grafico_evolucao_patrimonial,
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Container(bgcolor=ft.Colors.GREEN_800, border_radius=10, height=20, width=40),
                                            ft.Text("Valor Aplicado", weight=ft.FontWeight.W_600)
                                        ]
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Container(bgcolor=ft.Colors.GREEN_600, border_radius=10, height=20, width=40),
                                            ft.Text("Valor Líquido", weight=ft.FontWeight.W_600)
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),
                ),
                ft.Container(
                    border=ft.border.all(0.5, color=ft.Colors.ON_SURFACE),
                    border_radius=ft.border_radius.all(10),
                    margin=20,
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Row(
                                controls=[
                                    ft.Text("Posição Atual na Carteira", size=20, weight=ft.FontWeight.W_500),
                                    self.grafico_porcetagem_na_carteira_spinner,
                                ]
                            ),
                            ft.Row(
                                spacing=0,
                                controls=[
                                    self.grafico_porcetagem_na_carteira,
                                    ft.Container(
                                        border=ft.border.all(0.5, color=ft.Colors.ON_SURFACE),
                                        border_radius=ft.border_radius.all(10),
                                        margin=20,
                                        padding=20,
                                        content=ft.Column(
                                            controls=[
                                                ft.Text("% Carteira", size=20, weight=ft.FontWeight.W_500),
                                                self.container_porcentagem_na_carteira
                                            ]
                                        )
                                    )
                                ]
                            )
                        ]
                    ),
                )
            ]
        )
        self.abas_widget.tabs[2].content = self.layout_graficos

    def diferenca_meses(self, data:datetime.datetime) -> int:
        """Calcula a diferença em meses entre duas datas no formato 'dd/mm/yyyy'."""
        
        d1 = data
        d2 = datetime.datetime.today()

        diferenca = (d2.year - d1.year) * 12 + (d2.month - d1.month)
        
        return abs(diferenca) + 1

    def carregar_graficos(self):
        # Pré-definição de estilos e constantes para evitar recomputações
        normal_radius = 60
        hover_radius = 70
        normal_title_style = ft.TextStyle(
            size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD
        )
        hover_title_style = ft.TextStyle(
            size=22,
            color=ft.Colors.WHITE,
            weight=ft.FontWeight.BOLD,
            shadow=ft.BoxShadow(blur_radius=2, color=ft.Colors.BLACK54),
        )

        # Define o event handler usando os estilos pré-definidos
        def on_chart_event(e: ft.PieChartEvent):
            for idx, section in enumerate(self.grafico_porcetagem_na_carteira.sections):
                if idx == e.section_index:
                    section.radius = hover_radius
                    section.title_style = hover_title_style
                else:
                    section.radius = normal_radius
                    section.title_style = normal_title_style
            self.grafico_porcetagem_na_carteira.update()

        self.grafico_porcetagem_na_carteira.on_chart_event = on_chart_event
        self.grafico_evolucao_patrimonial.bar_groups = []
        self.grafico_porcetagem_na_carteira.sections = []
        self.container_porcentagem_na_carteira.controls = []

        valorMaximo = 0

        # Cache dos dados do usuário para evitar múltiplas chamadas
        dados_usuarios = self.usuarios.obter_dados()
        if dados_usuarios and not isinstance(dados_usuarios, usuarios.Errors):
            data_inicial = dados_usuarios[0]["data_negociacao"] - relativedelta(months=1)
            quantidade_de_meses = self.diferenca_meses(data_inicial)
            evolucao_patrimonial = {ativo: {"Q": 0} for ativo in self.ativos}
            cotacoes_mensais = {}

            # Obtém as cotações mensais de cada ativo e guarda no dicionário
            for ativo in self.ativos:
                cotacoes = self.obter_cotacoes_mensais(ativo, data_inicial, datetime.datetime.today())
                if cotacoes:
                    # Se a chave esperada não existir, utiliza a primeira disponível
                    key = ativo + ".SA"
                    if key not in cotacoes:
                        key, value = next(iter(cotacoes.items()))
                        cotacoes_mensais[key] = value
                    else:
                        cotacoes_mensais[key] = cotacoes[key]

            # Processa os dados para o gráfico de barras (Evolução Patrimonial)
            for i in range(quantidade_de_meses):
                current_date = data_inicial + relativedelta(months=i)
                data_str = current_date.strftime("%m/%Y")
                VtotalAplicadoAcumulado = 0
                VtotalLiquidoAcumulado = 0

                for ativo in self.ativos:
                    ativo_data = self.ativos[ativo].get(data_str)
                    if ativo_data:
                        # Calcula a variação de quantidade com sum comprehensions
                        compras = sum(item["Q"] for item in ativo_data.get("Compra", {}).values())
                        vendas = sum(item["Q"] for item in ativo_data.get("Venda", {}).values())
                        evolucao_patrimonial[ativo]["Q"] += (compras - vendas)

                    VtotalAplicadoAcumulado += evolucao_patrimonial[ativo]["Q"] * self.resumo_ativos[ativo]["PM"]
                    VtotalLiquidoAcumulado += evolucao_patrimonial[ativo]["Q"] * cotacoes_mensais.get(ativo + ".SA", {}).get(data_str, 0)
                    # print(cotacoes_mensais.get(ativo + ".SA", {}).get(data_str, 0), data_str)

                valorMaximo = max(valorMaximo, VtotalAplicadoAcumulado, VtotalLiquidoAcumulado)
                # print(VtotalLiquidoAcumulado)

                # Exibe apenas os últimos 12 meses no gráfico
                if quantidade_de_meses - i < 13:
                    self.grafico_evolucao_patrimonial.bar_groups.append(
                        ft.BarChartGroup(
                            x=i,
                            bar_rods=[
                                ft.BarChartRod(
                                    from_y=0,
                                    to_y=VtotalAplicadoAcumulado,
                                    width=25,
                                    color=ft.Colors.GREEN_800,
                                    tooltip=f"R$ {VtotalAplicadoAcumulado:.2f}",
                                    border_radius=ft.border_radius.only(top_left=4, top_right=4),
                                ),
                                ft.BarChartRod(
                                    from_y=0,
                                    to_y=VtotalLiquidoAcumulado,
                                    width=25,
                                    color=ft.Colors.GREEN_600,
                                    tooltip=f"R$ {VtotalLiquidoAcumulado:.2f}",
                                    border_radius=ft.border_radius.only(top_left=4, top_right=4),
                                ),
                            ],
                        )
                    )
                    self.grafico_evolucao_patrimonial.bottom_axis.labels.append(
                        ft.ChartAxisLabel(
                            value=i,
                            label=ft.Container(ft.Text(data_str), padding=10),
                        )
                    )

            self.grafico_evolucao_patrimonial.max_y = valorMaximo * 1.1

            # Processa os dados para o gráfico de pizza (Porcentagem na Carteira)
            colors_tuple = tuple(ft.Colors)
            i = 0
            counter = 0
            
            dados: dict = {}
            for chave, valor in self.resumo_ativos.items():
                if valor["Q"] > 0:
                    dados[chave] = valor["porcentagem"]

            dados = sorted(dados.items(), key=lambda item: item[1], reverse=True)

            for chave, valor in dados:
                # Seleciona a cor com base no índice (garantindo que esteja dentro do tamanho da tupla)
                cor = colors_tuple[((i % 286) * 11 + counter + 45) % len(colors_tuple)]
                self.grafico_porcetagem_na_carteira.sections.append(
                    ft.PieChartSection(
                        valor,
                        title=f"{valor:.2f} %" if valor >= 4.5 else "",
                        title_style=normal_title_style,
                        color=cor,
                        radius=normal_radius,
                    )
                )
                self.container_porcentagem_na_carteira.controls.append(
                    ft.Row(
                        controls=[
                            ft.Container(bgcolor=cor, border_radius=10, height=20, width=3 * valor),
                            ft.Text(f"{chave}   ({valor:.2f} %)", weight=ft.FontWeight.W_500)
                        ]
                    )
                )
                i += 1
                counter = i // 285


    # ABA LANÇAMENTOS
    def carregar_aba_lancamentos(self):
        
        # ELEMENTOS DA TABELA DO HISTÓRICO DE LANÇAMENTOS
        self.tabela_lancamentos = ft.DataTable(
            bgcolor= ft.Colors.ON_INVERSE_SURFACE,
            border_radius= 10,
            expand=True,
            vertical_lines= ft.BorderSide(0.7),
            columns=[
                ft.DataColumn(ft.Text('TIPO DE INVESTIMENTO')),
                ft.DataColumn(ft.Text('ATIVO')),
                ft.DataColumn(ft.Text('TIPO DE ORDEM')),
                ft.DataColumn(ft.Text('DATA DE NEGOCIAÇÃO')),
                ft.DataColumn(ft.Text('QUANTIDADE')),
                ft.DataColumn(ft.Text('PREÇO')),
                ft.DataColumn(ft.Text('VALOR TOTAL')),
                ft.DataColumn(ft.Text(''))
            ],
        )

        self.abas_widget.tabs[3].content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # Centraliza a coluna
            controls=[
                ft.Container(height=20),
                ft.ElevatedButton("Adicionar Lançamento", on_click=lambda e: self.adicionar_lancamento()),
                ft.Row(
                    expand=True,
                    scroll=True,
                    controls=[
                        ft.Container(
                            border=ft.border.all(0.5, color=ft.Colors.ON_SURFACE),
                            border_radius=ft.border_radius.all(10),
                            expand=True,
                            margin=20,
                            padding=20,
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                controls=[
                                    ft.Column(
                                        height=600,
                                        scroll=True,
                                        controls=[
                                            ft.Text("Lançamentos", size=20, weight=ft.FontWeight.W_500),
                                            self.tabela_lancamentos,
                                        ]
                                    ),
                                ],
                            )
                        ),
                    ]
                )
            ]
        )

    def obter_cotacao(self, ativo:str, fim:str=None, intervalo:int=15):
        ativo += ".SA"

        um_dia = datetime.timedelta(days=1)
        if fim is not None:
            fim = datetime.datetime.strptime(fim, "%d/%m/%Y") + um_dia
        else:
            fim = datetime.datetime.today() + um_dia
        inicio = fim - datetime.timedelta(days=intervalo)

        historico = yf.Ticker(ativo).history(start=inicio.strftime("%Y-%m-%d"), end=fim.strftime("%Y-%m-%d"))

        if not historico.empty:
            return historico["Close"].iloc[-1]


    def obter_cotacoes_mensais(self, ticker: str, data_inicio: datetime.datetime, data_fim: datetime.datetime) -> dict:
        """
        Obtém a última cotação de fechamento de cada mês para um ativo (FII/Ação) usando o Yahoo Finance.
        
        Parâmetros:
            ticker (str): Código do ativo (exemplo: "HGLG11.SA").
            data_inicio (str): Data inicial no formato "YYYY-MM-DD".
            data_fim (str): Data final no formato "YYYY-MM-DD".
        
        Retorno:
            dict: Dicionário no formato {"MM/YYYY": cotação}
        """

        # Baixar os dados históricos
        dados = yf.download(ticker + ".SA", start=data_inicio, end=data_fim, interval="1d")
        

        if dados.empty:
            print(f"Nenhum dado encontrado para {ticker} no período especificado.")
            return {}

        # Converter o índice para datetime (caso não esteja)
        dados.index = pd.to_datetime(dados.index)

        # Criar uma coluna "Ano-Mês" para agrupamento
        dados["Ano-Mes"] = dados.index.to_period("M")

        # Obter a última cotação de cada mês
        ultima_cotacao_mes = dados.groupby("Ano-Mes").tail(1)[["Close"]]

        # Converter o índice "Ano-Mes" para formato MM/YYYY e criar um dicionário
        cotacoes_dict = ultima_cotacao_mes["Close"].rename(lambda x: x.strftime("%m/%Y")).to_dict()
        
        if not f"{data_fim.month:02d}/{data_fim.year}" in cotacoes_dict:
            mes_anterior = data_fim - relativedelta(months=1)
            ativo = next(iter(cotacoes_dict))
            cotacoes_dict[ativo][f"{data_fim.month:02d}/{data_fim.year}"] = cotacoes_dict[ativo][f"{mes_anterior.month:02d}/{mes_anterior.year}"]

        return cotacoes_dict


    def adicionar_lancamento(self):

        def selecionar_data(e:ft.ControlEvent):
            self.data_negociacao_datepicker.controls[0].text = e.control.value.strftime('%d/%m/%Y')

            if self.ativo_autocomplete.selected_index is not None:
                cotacao = self.obter_cotacao(self.tickers[self.ativo_autocomplete.selected_index], self.data_negociacao_datepicker.controls[0].text)

                if cotacao != None:
                    self.preco_textfield.value = f"{cotacao:,.2f}"
                    self.valor_tempo_real_text.value = f"R$ {(int(self.quantidade_textfield.value) * float(self.preco_textfield.value) + float(self.outros_custos_textfield.value)):,.2f}"
                    self.pagina.update()

            self.pagina.update()

        def mudanca_de_ativo(e:ft.AutoCompleteSelectEvent):

            if self.data_negociacao_datepicker.controls[0].text.upper() == "DATA DE NEGOCIAÇÃO":
                cotacao = self.obter_cotacao(e.selection.value)
            else:
                cotacao = self.obter_cotacao(e.selection.value, self.data_negociacao_datepicker.controls[0].text)

            if cotacao != None:
                self.preco_textfield.value = f"{cotacao:,.2f}"
                self.valor_tempo_real_text.value = f"R$ {(int(self.quantidade_textfield.value) * float(self.preco_textfield.value) + float(self.outros_custos_textfield.value)):,.2f}"
                self.pagina.update()

        def textfield_on_change(e:ft.ControlEvent):

            valor = int(re.sub(r"[^\d]", "", e.data or "0"))
            if e.control.data == float:
                e.control.value = f"{valor/100:,.2f}"
            else:
                e.control.value = f"{valor:.0f}"
                
            compra_ou_venda = "Compra" if self.compra_ou_venda_radiobutton.selected_index == 0 else "Venda"
            outros_custos = float(self.outros_custos_textfield.value.replace(",", ""))

            self.valor_tempo_real_text.value = f"R$ {(int(self.quantidade_textfield.value) * float(self.preco_textfield.value) + (outros_custos if compra_ou_venda == "Compra" else - outros_custos)):,.2f}"
            self.pagina.update()
            

        def salvar():

            any_error = False

            if self.ativo_autocomplete.selected_index is None:
                any_error = True
                self.ativo_autocomplete_container.border = ft.border.all(1, ft.Colors.RED)
            else:
                self.ativo_autocomplete_container.border = ft.border.all(1, ft.Colors.ON_SURFACE)
                
            try:
                datetime.datetime.strptime(self.data_negociacao_datepicker.controls[0].text, "%d/%m/%Y")
                self.data_negociacao_datepicker.controls[0].bgcolor = ft.Colors.ON_SURFACE
            except:
                any_error = True
                self.data_negociacao_datepicker.controls[0].bgcolor = ft.Colors.RED

            try:
                int(self.quantidade_textfield.value)
                self.quantidade_textfield.border_color = ft.Colors.ON_SURFACE
            except:
                any_error = True
                self.quantidade_textfield.border_color = ft.Colors.RED

            try:
                float(self.preco_textfield.value.replace(",", ""))
                self.preco_textfield.border_color = ft.Colors.ON_SURFACE
            except:
                any_error = True
                self.preco_textfield.border_color = ft.Colors.RED

            try:
                float(self.outros_custos_textfield.value.replace(",", ""))
                self.outros_custos_textfield.border_color = ft.Colors.ON_SURFACE
            except:
                any_error = True
                self.outros_custos_textfield.border_color = ft.Colors.RED
            
            self.pagina.update()

            if not any_error:
                compra_ou_venda = "Compra" if self.compra_ou_venda_radiobutton.selected_index == 0 else "Venda"
                outros_custos = float(self.outros_custos_textfield.value.replace(",", ""))
                self.usuarios.inserir_dados(
                    None,
                    **{
                        "ativo": self.tickers[self.ativo_autocomplete.selected_index],
                        "ordem": "Compra" if self.compra_ou_venda_radiobutton.selected_index == 0 else "Venda",
                        "data_negociacao": self.data_negociacao_datepicker.controls[0].text,
                        "Q": self.quantidade_textfield.value,
                        "P": self.preco_textfield.value.replace(",", ""),
                        "Vtotal": int(self.quantidade_textfield.value) * float(self.preco_textfield.value.replace(",", "")) + (outros_custos if compra_ou_venda == "Compra" else - outros_custos),
                    }
                )
                self.pagina.close(self.dialogo_de_confirmar)
                self.recarregar_dados(True)

        self.compra_ou_venda_radiobutton = ft.CupertinoSegmentedButton(
            border_color=ft.Colors.GREY_900,
            click_color=ft.Colors.GREY_400,
            selected_index=0,
            selected_color=ft.Colors.BLACK,
            unselected_color=ft.Colors.GREY_100,
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(5, 10),
                    content=ft.Row(
                        spacing=5,
                        controls=[
                            ft.Icon(ft.Icons.ARROW_UPWARD, size=16),
                            ft.Text("Compra", size=16, weight=ft.FontWeight.W_500),
                        ]
                    )
                ),
                ft.Container(
                    padding=ft.padding.symmetric(5, 10),
                    content=ft.Row(
                        spacing=5,
                        controls=[
                            ft.Icon(ft.Icons.ARROW_DOWNWARD, size=16),
                            ft.Text("Venda", size=16, weight=ft.FontWeight.W_500),
                        ]
                    )
                ),
            ],
        )

        self.ativo_autocomplete = ft.AutoComplete(on_select=mudanca_de_ativo)
        for ticker in self.tickers:
            self.ativo_autocomplete.suggestions.append(ft.AutoCompleteSuggestion(key=ticker.lower(), value=ticker))

        self.ativo_autocomplete_container = ft.Container(
            border=ft.border.all(1, ft.Colors.ON_SURFACE),
            border_radius=5,
            padding=ft.padding.all(10),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Text("Ativo", height=18, weight=ft.FontWeight.W_500),
                    self.ativo_autocomplete
                ]
            )
        )

        self.data_negociacao_datepicker = ft.Row(
            controls=[
                ft.ElevatedButton(
                    bgcolor=ft.Colors.ON_SURFACE,
                    expand=True,
                    icon=ft.Icons.CALENDAR_MONTH,
                    text="Data de negociação",
                    color=ft.Colors.SURFACE,
                    on_click=lambda e: self.pagina.open(
                        ft.DatePicker(
                            last_date=datetime.datetime.today(),
                            on_change=selecionar_data,
                        )
                    ),
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(20, 10),
                        icon_color=ft.Colors.SURFACE,
                        icon_size=20,
                        text_style=ft.TextStyle(
                            size=16,
                        ),
                    ),
                )
            ]
        )

        self.quantidade_textfield = ft.TextField(
            border_color=ft.Colors.ON_SURFACE,
            data=int,
            enable_interactive_selection=False,
            input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9]*$", replacement_string=""),
            label="Quantidade",
            on_change=textfield_on_change,
            value=1,
        )
        self.preco_textfield = ft.TextField(
            border_color=ft.Colors.ON_SURFACE,
            data=float,
            enable_interactive_selection=False,
            label="Preço",
            prefix=ft.Text("R$ "),
            on_change=textfield_on_change,
            value=f"{0:,.2f}",
        )
        self.outros_custos_textfield = ft.TextField(
            border_color=ft.Colors.ON_SURFACE,
            data=float,
            enable_interactive_selection=False,
            label="Outros custos",
            prefix=ft.Text("R$ "),
            on_change=textfield_on_change,
            value=f"{0:,.2f}",
        )

        self.valor_tempo_real_text = ft.Text("R$ 0.00", color=ft.Colors.SURFACE, weight=ft.FontWeight.W_600)
        
        self.dialogo_de_confirmar.content = ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=True,
                controls=[
                    self.compra_ou_venda_radiobutton,
                    self.ativo_autocomplete_container,
                    self.data_negociacao_datepicker,
                    self.quantidade_textfield,
                    self.preco_textfield,
                    self.outros_custos_textfield,
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Container(
                                alignment=ft.alignment.center,
                                bgcolor=ft.Colors.ON_SURFACE,
                                border_radius=20,
                                content=self.valor_tempo_real_text,
                                expand=True,
                                padding=ft.padding.symmetric(10),
                            )
                        ]
                    )
                ]
            )
        )
        self.dialogo_de_confirmar.actions[1].on_click = lambda e: salvar()
        self.pagina.open(self.dialogo_de_confirmar)

    def carregar_lancamentos(self):

        self.tabela_lancamentos.rows = []

        self.ativos: dict[str, dict[str, dict[str, dict[str]]]] = {}

        self.resumo_ativos = {}

        lancamentos = self.usuarios.obter_dados()
        if not isinstance(lancamentos, usuarios.Errors) and lancamentos:
            lancamentos = lancamentos[::-1]
            for i in range(len(lancamentos)):
                ativo = lancamentos[i]["ativo"]
                mes_ano = lancamentos[i]["data_negociacao"].strftime("%m/%Y")
                dia = lancamentos[i]["data_negociacao"].strftime("%d")
                ordem = lancamentos[i]["ordem"]
                quantidade = lancamentos[i]["Q"]

                self.resumo_ativos.setdefault(ativo, {
                        "Qcompra": 0,
                        "Qvenda": 0,
                        "Vtotal": 0,
                    }
                )

                if ordem == "Compra":
                    self.resumo_ativos[ativo]["Qcompra"] += quantidade
                    self.resumo_ativos[ativo]["Vtotal"] += lancamentos[i]["Vtotal"]

                else:
                    self.resumo_ativos[ativo]["Qvenda"] += quantidade

                self.ativos.setdefault(ativo, {}).setdefault(mes_ano, {}).setdefault(ordem, {}).setdefault(dia, {"Q": 0})
                self.ativos[ativo][mes_ano][ordem][dia]["Q"] += quantidade
                
                datarow = ft.DataRow(
                    cells=[
                        ft.DataCell(
                            content=ft.Row(
                                controls=[
                                    ft.Container(bgcolor=ft.Colors.GREEN if lancamentos[i]["ordem"] == "Compra" else ft.Colors.RED, width=5),
                                    ft.Text("FII"),
                                ]
                            )
                        ),
                        ft.DataCell(ft.Text(lancamentos[i]["ativo"])),
                        ft.DataCell(ft.Text(lancamentos[i]["ordem"])),
                        ft.DataCell(ft.Text(lancamentos[i]["data_negociacao"].strftime("%d/%m/%Y"))),
                        ft.DataCell(ft.Text(lancamentos[i]["Q"])),
                        ft.DataCell(ft.Text(f"R$ {float(lancamentos[i]['P']):,.2f}")),
                        ft.DataCell(ft.Text(f"R$ {float(lancamentos[i]['Vtotal']):,.2f}")),
                        ft.DataCell(ft.IconButton(icon= ft.Icons.DELETE, icon_color= ft.Colors.ON_SURFACE, on_click= lambda e, indice=len(lancamentos) - 1 - i: self.remover_lacamentos(indice)))
                    ]
                )

                self.tabela_lancamentos.rows.append(datarow)
        self.carregar_tabela_resumo()
        self.carregar_graficos()
        self.carregar_tabela_historico_de_proventos()
        self.carregando_tabela_proventos_mais_grafico()
        self.pagina.update()

    def remover_lacamentos(self, indice:int):

        def remover():
            self.usuarios.remover_dados(indice)
            self.pagina.close(self.dialogo_de_confirmar)
            self.recarregar_dados(True)

        
        self.dialogo_de_confirmar.content = ft.Text("Você quer deletar mesmo esse lançamento?", size=16, weight=ft.FontWeight.W_500)
        self.dialogo_de_confirmar.actions[1].on_click = lambda e: remover()
        self.pagina.on_keyboard_event = lambda e: remover() if e.key == "Enter" else None

        self.pagina.open(self.dialogo_de_confirmar)
        self.pagina.update()
    
    # ABA CONFIGURAÇÃO
    def carregar_aba_configuracao(self):
        self.caixa_texto_configuracao = ft.TextField(
            border_color=ft.Colors.ON_SURFACE,
            hint_text="Nome da carteira",
            label="Nome da carteira",
            value=self.usuarios.usuario_selecionado,
        )
        self.layout_config = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,  # Centraliza a coluna
            expand=True,
            controls=[
                ft.Container(height=20),
                ft.Row(
                    expand=True,
                    scroll=True,
                    controls=[
                        ft.Container(
                            border=ft.border.all(0.5, color=ft.Colors.ON_SURFACE),
                            border_radius=ft.border_radius.all(10),
                            expand=True,
                            margin=20,
                            padding=20,
                            content=ft.Column(
                                expand=True,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                controls=[
                                    ft.Column(
                                        expand=True,
                                        controls=[
                                            ft.Text("Configuração", size=20, weight=ft.FontWeight.W_500),
                                            self.caixa_texto_configuracao,
                                            ft.Row(
                                                controls=[
                                                    ft.IconButton(
                                                        icon=ft.Icons.SAVE,
                                                        icon_color=ft.Colors.ON_SURFACE,
                                                        on_click= lambda e: self.editar_carteira()
                                                    ),
                                                    ft.IconButton(
                                                        icon=ft.Icons.DELETE,
                                                        icon_color=ft.Colors.ON_SURFACE,
                                                        on_click= lambda e: self.remover_carteira()
                                                    )
                                                ]
                                            )
                                        ]
                                    ),
                                ],
                            )
                        ),
                    ]
                )
            ]
        )
        self.abas_widget.tabs[4].content = self.layout_config

ft.app(target=App)