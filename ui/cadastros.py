# cadastros.py
# Tela de listagem e pesquisa de cadastros do sistema ECOSOL AM.

import sqlite3          # Banco de dados local SQLite
import os               # Leitura das variáveis de ambiente do .env
from dotenv import load_dotenv  # Carrega o .env para que os.getenv() funcione

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,   # Layouts principais
    QLabel, QLineEdit, QPushButton,       # Widgets básicos
    QTableWidget, QTableWidgetItem,       # Tabela de resultados
    QComboBox, QGroupBox,                 # Combo de tipo de busca e agrupador
    QHeaderView, QAbstractScrollArea,     # Configurações do cabeçalho e scroll
    QSizePolicy, QAbstractItemView        # Política de tamanho dos widgets
)
from PyQt6.QtCore import Qt              # Constantes de alinhamento e flags

# Carrega as variáveis definidas no arquivo .env
load_dotenv()

# PALETA DE CORES — lidas do .env, idênticas ao form_ecosol.py e sincronizacao.py
COR_PRIMARIA       = os.getenv("COR_PRIMARIA",       "#003366")  # Azul escuro — título, bordas, GroupBox
COR_PRIMARIA_HOVER = os.getenv("COR_PRIMARIA_HOVER", "#004080")  # Azul hover dos botões
COR_SECUNDARIA     = os.getenv("COR_SECUNDARIA",     "#17a2b8")  # Azul ciano — botão Pesquisar
COR_FUNDO_CLARO    = os.getenv("COR_FUNDO_CLARO",   "#f8f9fa")  # Cinza claro — fundo geral
COR_TEXTO_ESCURO   = os.getenv("COR_TEXTO_ESCURO",   "#212529")  # Quase preto — texto dos labels
COR_TEXTO_CLARO    = os.getenv("COR_TEXTO_CLARO",    "#ffffff")  # Branco — texto sobre fundo colorido
COR_BORDA          = os.getenv("COR_BORDA",          "#ced4da")  # Cinza suave — bordas dos inputs

# =============================================================================
# Mapeamento entre o texto exibido no combo e o nome real da coluna no banco.
# Permite que o usuário veja nomes amigáveis sem precisar conhecer o schema.
# =============================================================================
CAMPOS_PESQUISA = {
    "ID do Cadastro":              "id",                   # UUID único do registro
    "Nome / Razão Social":         "razao_social_nome",    # Nome da empresa ou empreendedor
    "Nome do Representante":       "representante_legal",  # Representante legal
    "CPF":                         "cpf",                  # CPF (armazenado sem formatação)
    "CNPJ":                        "cnpj",                 # CNPJ (armazenado sem formatação)
    "RG":                          "rg",                   # RG do representante
}

# =============================================================================
# Lista de colunas exibidas na tabela, na ordem desejada.
# Cada tupla: (nome_coluna_banco, cabeçalho_exibido_na_tabela)
# Todas as 40 colunas do schema são listadas para exibição completa.
# O scroll horizontal permite navegar entre as que não cabem na tela.
# =============================================================================
COLUNAS_TABELA = [
    ("id",                          "ID"),
    ("tipo_cadastro",               "Tipo"),
    ("razao_social_nome",           "Nome / Razão Social"),
    ("representante_legal",         "Representante"),
    ("cpf",                         "CPF"),
    ("cnpj",                        "CNPJ"),
    ("rg",                          "RG"),
    ("telefone",                    "Telefone"),
    ("email",                       "E-mail"),
    ("endereco",                    "Endereço"),
    ("cep",                         "CEP"),
    ("sexo",                        "Sexo"),
    ("cor_raca",                    "Cor/Raça"),
    ("forma_organizacao_ecosol",    "Forma Org. ECOSOL"),
    ("forma_organizacao_emp",       "Forma Org. Emp."),
    ("segmento_empreendimento",     "Segmento"),
    ("materia_prima",               "Matéria-Prima"),
    ("local_producao",              "Local Produção"),
    ("onde_comercializa",           "Onde Comercializa"),
    ("beneficiarios_diretos_m",     "Ben. Dir. M"),
    ("beneficiarios_diretos_f",     "Ben. Dir. F"),
    ("beneficiarios_indiretos_m",   "Ben. Ind. M"),
    ("beneficiarios_indiretos_f",   "Ben. Ind. F"),
    ("maquina_cartao",              "Cartão"),
    ("pix",                         "PIX"),
    ("classificacao_social",        "Classif. Social"),
    ("motivo_criacao",              "Motivo Criação"),
    ("formas_comercializacao",      "Formas Comerc."),
    ("produtos_comercializados",    "Produtos"),
    ("pagam_taxa",                  "Pagam Taxa"),
    ("forma_contribuicao",          "Forma Contrib."),
    ("renda_preponderante",         "Renda"),
    ("para_quem_comercializa",      "Para Quem Comerc."),
    ("dificuldade_comercializacao", "Dificuldade"),
    ("responsavel_vendas",          "Resp. Vendas"),
    ("obs",                         "Observações"),
    ("local_cadastro",              "Local"),
    ("data_formulario",             "Data Formulário"),
    ("data_cadastro",               "Data Cadastro"),
    ("sincronizado",                "Sincronizado"),
]


# =============================================================================
# TelaCadastros
# Widget principal da tela de listagem de cadastros.
#
# Estrutura visual:
#   Título + subtítulo
#   └── GroupBox "Pesquisar Cadastros"
#       └── [Combo tipo] [Campo texto] [Botão Pesquisar] [Botão Limpar]
#   └── Label contador de resultados
#   └── Tabela com scroll horizontal e vertical
# =============================================================================
class TelaCadastros(QWidget):
    def __init__(self):
        super().__init__()
        self.configurar_ui()      # Monta todos os widgets da tela
        self.pesquisar()          # Carrega todos os cadastros ao abrir a tela

    # =========================================================================
    # configurar_ui
    # Monta a interface completa: título, GroupBox de pesquisa e tabela.
    # Padrão idêntico ao form_ecosol.py e sincronizacao.py.
    # =========================================================================
    def configurar_ui(self):
        # Layout raiz vertical: empilha todos os blocos de cima para baixo
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 20, 30, 20)  # Margens externas da tela
        layout_principal.setSpacing(14)                       # Espaço entre os blocos

        # ----- CABEÇALHO: título com linha decorativa -----
        # Mesmo estilo do título em form_ecosol.py e sincronizacao.py
        titulo = QLabel("CONSULTA DE CADASTROS")
        titulo.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {COR_PRIMARIA}; "
            f"border-bottom: 2px solid {COR_PRIMARIA}; "
            f"padding-bottom: 5px;"
        )
        layout_principal.addWidget(titulo)

        # Subtítulo descritivo logo abaixo do título principal
        subtitulo = QLabel("Pesquise e visualize todos os cadastros do sistema")
        subtitulo.setStyleSheet("color: #6c757d; font-size: 12px; margin-top: -4px;")
        layout_principal.addWidget(subtitulo)

        # =================================================================
        # GRUPO: BARRA DE PESQUISA
        # Contém: combo de tipo | campo de texto | botão pesquisar | botão limpar
        # O GroupBox segue o mesmo estilo de bordas e título colorido dos demais
        # =================================================================
        grupo_pesquisa = QGroupBox("Pesquisar Cadastros")
        grupo_pesquisa.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 13px;
                border: 1px solid {COR_BORDA};
                border-radius: 6px;
                margin-top: 12px;
                padding: 16px 20px 14px 20px;
                background-color: {COR_TEXTO_CLARO};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 0 5px;
                color: {COR_PRIMARIA};
            }}
            QLineEdit, QComboBox {{
                border: 1px solid {COR_BORDA};
                border-radius: 4px;
                padding: 6px 10px;
                background-color: {COR_TEXTO_CLARO};
                min-height: 28px;
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {COR_PRIMARIA};
            }}
        """)

        # Layout horizontal interno do grupo: [combo] [campo] [btn pesquisar] [btn limpar]
        layout_pesquisa = QHBoxLayout()
        layout_pesquisa.setSpacing(10)  # Espaço entre os widgets da barra

        # ----- Combo de tipo de pesquisa (à esquerda) -----
        # Lista os campos disponíveis para o usuário escolher qual coluna pesquisar
        self.combo_tipo = QComboBox()
        self.combo_tipo.setFixedWidth(220)           # Largura fixa para não "espirrar"
        self.combo_tipo.setToolTip("Selecione o campo de pesquisa")
        for texto_amigavel in CAMPOS_PESQUISA.keys():
            self.combo_tipo.addItem(texto_amigavel)  # Adiciona cada opção amigável
        layout_pesquisa.addWidget(self.combo_tipo)

        # ----- Campo de texto para digitar o termo de pesquisa -----
        self.input_pesquisa = QLineEdit()
        self.input_pesquisa.setPlaceholderText("Digite o termo de pesquisa... (vazio = listar todos)")
        # Permite pressionar Enter para pesquisar sem clicar no botão
        self.input_pesquisa.returnPressed.connect(self.pesquisar)
        layout_pesquisa.addWidget(self.input_pesquisa)  # Ocupa o espaço restante (elástico)

        # ----- Botão Pesquisar (à direita do campo de texto) -----
        # Estilo azul ciano (COR_SECUNDARIA), mesmo do btn_testar em sincronizacao.py
        btn_pesquisar = QPushButton("🔍  Pesquisar")
        btn_pesquisar.setFixedWidth(140)   # Largura fixa para aparência uniforme
        btn_pesquisar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_SECUNDARIA};
                color: {COR_TEXTO_CLARO};
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {COR_PRIMARIA}; }}
        """)
        btn_pesquisar.clicked.connect(self.pesquisar)   # Conecta ao método de pesquisa
        layout_pesquisa.addWidget(btn_pesquisar)

        # ----- Botão Limpar (limpa o campo e recarrega todos) -----
        btn_limpar = QPushButton("✕  Limpar")
        btn_limpar.setFixedWidth(110)
        btn_limpar.setStyleSheet(f"""
            QPushButton {{
                background-color: #6c757d;
                color: {COR_TEXTO_CLARO};
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #5a6268; }}
        """)
        btn_limpar.clicked.connect(self.limpar_pesquisa)  # Conecta ao método de limpeza
        layout_pesquisa.addWidget(btn_limpar)

        grupo_pesquisa.setLayout(layout_pesquisa)       # Aplica o layout ao GroupBox
        layout_principal.addWidget(grupo_pesquisa)      # Adiciona o GroupBox à tela

        # ----- Label contador de resultados -----
        # Exibe "X cadastro(s) encontrado(s)" após cada pesquisa
        self.lbl_contador = QLabel("Carregando...")
        self.lbl_contador.setStyleSheet(
            f"color: {COR_PRIMARIA}; font-size: 12px; font-weight: bold;"
        )
        layout_principal.addWidget(self.lbl_contador)

        # =================================================================
        # TABELA DE RESULTADOS
        # Exibe todas as colunas do schema. O scroll horizontal é habilitado
        # para que o usuário possa navegar pelas colunas que não cabem na tela.
        # =================================================================
        self.tabela = QTableWidget()

        # Define a quantidade de colunas com base na lista COLUNAS_TABELA
        self.tabela.setColumnCount(len(COLUNAS_TABELA))

        # Define os cabeçalhos com os textos amigáveis da lista COLUNAS_TABELA
        self.tabela.setHorizontalHeaderLabels(
            [cabecalho for _, cabecalho in COLUNAS_TABELA]
        )

        # Estilo da tabela: fundo branco, gridlines suaves, cabeçalho destacado
        self.tabela.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COR_TEXTO_CLARO};
                border: 1px solid {COR_BORDA};
                border-radius: 6px;
                gridline-color: #f0f2f7;
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid #f0f2f7;
                color: {COR_TEXTO_ESCURO};
            }}
            QTableWidget::item:selected {{
                background-color: #e8eeff;
                color: {COR_TEXTO_ESCURO};
            }}
            QHeaderView::section {{
                background-color: #f5f7fc;
                color: #5a6380;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 6px;
                border: none;
                border-bottom: 2px solid {COR_BORDA};
                border-right: 1px solid {COR_BORDA};
            }}
            /* Estilo da barra de scroll horizontal */
            QScrollBar:horizontal {{
                background: #dde1ea;
                height: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal {{
                background: #b0b8cc;
                border-radius: 4px;
                min-width: 30px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """)

        # Comportamento de seleção: seleciona a linha inteira ao clicar
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Impede que o usuário edite diretamente as células da tabela
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Oculta o índice numérico lateral esquerdo (coluna de número de linha do Qt)
        self.tabela.verticalHeader().setVisible(False)

        # SCROLL HORIZONTAL: Não redimensiona as seções para caberem na tela
        # Isso ativa o scroll horizontal automaticamente quando há muitas colunas
        self.tabela.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents  # Cada coluna ajusta ao conteúdo
        )

        # Garante que a tabela expanda verticalmente para ocupar o espaço disponível
        self.tabela.setSizePolicy(
            QSizePolicy.Policy.Expanding,   # Expande horizontalmente
            QSizePolicy.Policy.Expanding    # Expande verticalmente
        )

        # Habilita scroll em ambas as direções (vertical e horizontal)
        self.tabela.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tabela.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        # Adiciona a tabela ao layout — ocupa todo o espaço vertical restante
        layout_principal.addWidget(self.tabela)

    # =========================================================================
    # pesquisar
    # Método principal de busca. Executado ao abrir a tela, ao pressionar Enter
    # no campo de texto, ou ao clicar no botão "Pesquisar".
    #
    # Lógica:
    #   - Se o campo de texto estiver vazio → SELECT sem filtro (lista tudo)
    #   - Se tiver texto → SELECT com LIKE '%termo%' na coluna escolhida no combo
    #
    # Usa LIKE com % dos dois lados para busca parcial (não precisa palavra exata).
    # =========================================================================
    def pesquisar(self):
        termo       = self.input_pesquisa.text().strip()         # Lê o texto digitado
        tipo_amig   = self.combo_tipo.currentText()              # Lê o texto amigável do combo
        coluna_db   = CAMPOS_PESQUISA.get(tipo_amig, "razao_social_nome")  # Traduz para nome do banco

        # Monta as colunas do SELECT na mesma ordem de COLUNAS_TABELA
        colunas_select = ", ".join(col for col, _ in COLUNAS_TABELA)

        conn   = sqlite3.connect('ecosol_local.db')  # Abre conexão com o banco local
        cursor = conn.cursor()

        if termo:
            # Pesquisa com filtro: LIKE '%termo%' busca qualquer ocorrência parcial
            sql = f"SELECT {colunas_select} FROM cadastros_ecosol WHERE {coluna_db} LIKE ?"
            cursor.execute(sql, (f"%{termo}%",))  # Parâmetro com wildcards
        else:
            # Sem filtro: lista todos os cadastros ordenados pela data de cadastro mais recente
            sql = f"SELECT {colunas_select} FROM cadastros_ecosol ORDER BY data_cadastro DESC"
            cursor.execute(sql)

        resultados = cursor.fetchall()  # Recupera todos os registros retornados
        conn.close()                    # Fecha a conexão com o banco

        self._preencher_tabela(resultados)  # Repassa os dados para o método de preenchimento

    # =========================================================================
    # limpar_pesquisa
    # Apaga o texto do campo de pesquisa e recarrega todos os cadastros.
    # Chamado pelo botão "✕ Limpar".
    # =========================================================================
    def limpar_pesquisa(self):
        self.input_pesquisa.clear()  # Limpa o campo de texto
        self.pesquisar()             # Recarrega todos os cadastros (campo vazio = sem filtro)

    # =========================================================================
    # _preencher_tabela
    # Recebe a lista de registros do banco e preenche a tabela linha por linha.
    # Também atualiza o contador de resultados no label lbl_contador.
    #
    # Prefixo _ indica método interno — não chamado diretamente pela UI.
    # =========================================================================
    def _preencher_tabela(self, resultados):
        self.tabela.setRowCount(0)   # Remove todas as linhas existentes antes de preencher

        # Atualiza o label de contagem com o total de registros retornados
        total = len(resultados)
        self.lbl_contador.setText(
            f"{total} cadastro(s) encontrado(s)"
        )

        # Itera pelos registros e preenche célula por célula
        for linha_idx, linha_dados in enumerate(resultados):
            self.tabela.insertRow(linha_idx)  # Insere uma linha vazia na posição correta

            for col_idx, valor in enumerate(linha_dados):
                # Converte None (valor nulo do SQLite) para string vazia para exibição limpa
                texto = str(valor) if valor is not None else ""

                item = QTableWidgetItem(texto)                          # Cria o item de célula
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter |  # Alinha verticalmente ao centro
                                      Qt.AlignmentFlag.AlignLeft)      # Alinha horizontalmente à esquerda
                self.tabela.setItem(linha_idx, col_idx, item)          # Insere na tabela

            # Altura uniforme para todas as linhas
            self.tabela.setRowHeight(linha_idx, 36)