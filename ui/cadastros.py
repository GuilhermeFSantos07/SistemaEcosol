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
    QSizePolicy, QAbstractItemView,       # Política de tamanho dos widgets
    QDialog                               # Janela popup do histórico de versões
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

# Nome interno usado só para identificar a posição da coluna de ações na tabela
# (não corresponde a nenhuma coluna real do banco, é só para a UI)
INDICE_COLUNA_ACOES = len(COLUNAS_TABELA)


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
        btn_pesquisar = QPushButton("Pesquisar")
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

        # Define a quantidade de colunas com base na lista COLUNAS_TABELA, mais
        # 1 coluna extra de "Ações" no final (botão de Histórico de versões)
        self.tabela.setColumnCount(len(COLUNAS_TABELA) + 1)

        # Define os cabeçalhos: as colunas do banco + o cabeçalho da coluna de ações
        self.tabela.setHorizontalHeaderLabels(
            [cabecalho for _, cabecalho in COLUNAS_TABELA] + ["Histórico"]
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

        # A coluna de Ações (última, índice INDICE_COLUNA_ACOES) tem largura fixa,
        # suficiente para o botão de histórico, independente do conteúdo
        self.tabela.horizontalHeader().setSectionResizeMode(
            INDICE_COLUNA_ACOES, QHeaderView.ResizeMode.Fixed
        )
        self.tabela.setColumnWidth(INDICE_COLUNA_ACOES, 110)

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
    #   - Primeiro filtra para trazer SOMENTE a versão mais recente de cada
    #     "pessoa/empreendimento" (mesmo grupo_id) — cadastros antigos que já
    #     foram atualizados não aparecem na lista principal, só no histórico.
    #   - Se o campo de texto estiver vazio → lista todas as versões mais recentes
    #   - Se tiver texto → aplica LIKE '%termo%' na coluna escolhida no combo,
    #     dentro desse conjunto já filtrado pela versão mais recente
    #
    # Usa LIKE com % dos dois lados para busca parcial (não precisa palavra exata).
    # =========================================================================
    def pesquisar(self):
        termo       = self.input_pesquisa.text().strip()         # Lê o texto digitado
        tipo_amig   = self.combo_tipo.currentText()              # Lê o texto amigável do combo
        coluna_db   = CAMPOS_PESQUISA.get(tipo_amig, "razao_social_nome")  # Traduz para nome do banco

        # Monta as colunas do SELECT na mesma ordem de COLUNAS_TABELA, e inclui
        # o grupo_id ao final — necessário para o botão de Histórico, mas não é
        # uma coluna visível na tabela principal (tratado separadamente)
        colunas_select = ", ".join(col for col, _ in COLUNAS_TABELA)

        # Subquery que identifica os "id" das versões mais recentes: para cada
        # grupo_id, pega a linha cujo data_cadastro é o maior (mais recente).
        # Isso garante que cadastros antigos já atualizados fiquem de fora da
        # lista principal, mesmo que tenham o mesmo grupo_id de outra linha.
        filtro_versao_recente = """
            id IN (
                SELECT c1.id FROM cadastros_ecosol c1
                WHERE c1.data_cadastro = (
                    SELECT MAX(c2.data_cadastro) FROM cadastros_ecosol c2
                    WHERE c2.grupo_id = c1.grupo_id
                )
            )
        """

        conn   = sqlite3.connect('ecosol_local.db')  # Abre conexão com o banco local
        cursor = conn.cursor()

        if termo:
            # Pesquisa com filtro: LIKE '%termo%' busca qualquer ocorrência parcial,
            # combinado com o filtro de versão mais recente (AND)
            sql = f"""
                SELECT {colunas_select}, grupo_id FROM cadastros_ecosol
                WHERE {filtro_versao_recente} AND {coluna_db} LIKE ?
                ORDER BY data_cadastro DESC
            """
            cursor.execute(sql, (f"%{termo}%",))  # Parâmetro com wildcards
        else:
            # Sem filtro de texto: lista todas as versões mais recentes
            sql = f"""
                SELECT {colunas_select}, grupo_id FROM cadastros_ecosol
                WHERE {filtro_versao_recente}
                ORDER BY data_cadastro DESC
            """
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
    # Recebe a lista de registros do banco (já incluindo grupo_id como último
    # elemento de cada linha) e preenche a tabela linha por linha. Também
    # adiciona o botão de "Histórico" na última coluna, exibido somente para
    # grupos que têm mais de uma versão registrada.
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

        # Descobre de antemão quais grupo_id têm mais de uma versão no banco,
        # numa única consulta (evita 1 query por linha dentro do loop abaixo)
        grupos_com_historico = self._buscar_grupos_com_historico()

        # Itera pelos registros e preenche célula por célula
        for linha_idx, linha_dados in enumerate(resultados):
            self.tabela.insertRow(linha_idx)  # Insere uma linha vazia na posição correta

            # O último elemento da linha é o grupo_id (adicionado no SELECT de
            # pesquisar()), que não é uma coluna visível — separamos ele aqui
            *valores_visiveis, grupo_id = linha_dados

            for col_idx, valor in enumerate(valores_visiveis):
                # Converte None (valor nulo do SQLite) para string vazia para exibição limpa
                texto = str(valor) if valor is not None else ""

                item = QTableWidgetItem(texto)                          # Cria o item de célula
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter |  # Alinha verticalmente ao centro
                                      Qt.AlignmentFlag.AlignLeft)      # Alinha horizontalmente à esquerda
                self.tabela.setItem(linha_idx, col_idx, item)          # Insere na tabela

            # ----- Coluna de Ações: botão de Histórico (somente se houver mais de 1 versão) -----
            if grupo_id in grupos_com_historico:
                btn_historico = QPushButton("Histórico")
                btn_historico.setToolTip("Ver versões anteriores deste cadastro")
                btn_historico.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COR_SECUNDARIA};
                        color: {COR_TEXTO_CLARO};
                        padding: 4px 8px;
                        font-size: 11px;
                        font-weight: bold;
                        border-radius: 4px;
                        border: none;
                    }}
                    QPushButton:hover {{ background-color: {COR_PRIMARIA}; }}
                """)
                # Lambda com argumento padrão captura o grupo_id correto desta iteração
                btn_historico.clicked.connect(lambda checked, gid=grupo_id: self.abrir_historico(gid))
                self.tabela.setCellWidget(linha_idx, INDICE_COLUNA_ACOES, btn_historico)

            # Altura uniforme para todas as linhas
            self.tabela.setRowHeight(linha_idx, 36)

    # =========================================================================
    # _buscar_grupos_com_historico
    # Consulta quais grupo_id têm MAIS DE UMA linha na tabela cadastros_ecosol
    # (ou seja, já passaram por pelo menos uma atualização cadastral).
    # Retorna um set de grupo_id para checagem rápida (O(1)) dentro do loop.
    # =========================================================================
    def _buscar_grupos_com_historico(self):
        conn   = sqlite3.connect('ecosol_local.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT grupo_id FROM cadastros_ecosol
            GROUP BY grupo_id
            HAVING COUNT(*) > 1
        """)
        grupos = {linha[0] for linha in cursor.fetchall()}
        conn.close()
        return grupos

    # =========================================================================
    # abrir_historico
    # Abre uma janela (QDialog) somente leitura com todas as versões antigas
    # do grupo_id informado, ordenadas da mais antiga para a mais recente,
    # para consulta e auditoria. Chamado pelo botão "🕒 Histórico" da linha.
    # =========================================================================
    def abrir_historico(self, grupo_id):
        conn   = sqlite3.connect('ecosol_local.db')
        cursor = conn.cursor()

        colunas_select = ", ".join(col for col, _ in COLUNAS_TABELA)
        cursor.execute(f"""
            SELECT {colunas_select} FROM cadastros_ecosol
            WHERE grupo_id = ?
            ORDER BY data_cadastro ASC
        """, (grupo_id,))
        versoes = cursor.fetchall()
        conn.close()

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Histórico de Atualizações Cadastrais")
        dialogo.resize(1000, 500)

        layout_dialogo = QVBoxLayout(dialogo)
        layout_dialogo.setContentsMargins(20, 20, 20, 20)
        layout_dialogo.setSpacing(12)

        titulo = QLabel(f"Histórico de Versões ({len(versoes)} registro(s))")
        titulo.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {COR_PRIMARIA}; "
            f"border-bottom: 2px solid {COR_PRIMARIA}; padding-bottom: 5px;"
        )
        layout_dialogo.addWidget(titulo)

        subtitulo = QLabel(
            "A primeira linha é o cadastro original; as demais são atualizações "
            "cadastrais posteriores, da mais antiga para a mais recente."
        )
        subtitulo.setStyleSheet("color: #6c757d; font-size: 12px;")
        subtitulo.setWordWrap(True)
        layout_dialogo.addWidget(subtitulo)

        tabela_historico = QTableWidget()
        tabela_historico.setColumnCount(len(COLUNAS_TABELA))
        tabela_historico.setHorizontalHeaderLabels([cabecalho for _, cabecalho in COLUNAS_TABELA])
        tabela_historico.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Somente leitura
        tabela_historico.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabela_historico.verticalHeader().setVisible(False)
        tabela_historico.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        tabela_historico.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        tabela_historico.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        tabela_historico.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COR_TEXTO_CLARO};
                border: 1px solid {COR_BORDA};
                border-radius: 6px;
                gridline-color: #f0f2f7;
                font-size: 12px;
            }}
            QTableWidget::item {{ padding: 6px 10px; }}
            QHeaderView::section {{
                background-color: #f5f7fc;
                color: #5a6380;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 6px;
                border: none;
                border-bottom: 2px solid {COR_BORDA};
            }}
        """)

        tabela_historico.setRowCount(len(versoes))
        for linha_idx, linha_dados in enumerate(versoes):
            for col_idx, valor in enumerate(linha_dados):
                texto = str(valor) if valor is not None else ""
                item = QTableWidgetItem(texto)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                tabela_historico.setItem(linha_idx, col_idx, item)
            tabela_historico.setRowHeight(linha_idx, 34)

        layout_dialogo.addWidget(tabela_historico)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setFixedWidth(120)
        btn_fechar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_PRIMARIA};
                color: {COR_TEXTO_CLARO};
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {COR_PRIMARIA_HOVER}; }}
        """)
        btn_fechar.clicked.connect(dialogo.accept)

        layout_btn = QHBoxLayout()
        layout_btn.addStretch()
        layout_btn.addWidget(btn_fechar)
        layout_dialogo.addLayout(layout_btn)

        dialogo.exec()