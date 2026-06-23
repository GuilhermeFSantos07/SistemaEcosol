# form_ecosol.py
# Tela principal de cadastro do sistema ECOSOL.
# As cores são carregadas dinamicamente do arquivo .env via os.getenv(),

import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from dotenv import load_dotenv  # Biblioteca que lê o arquivo .env e injeta as variáveis no ambiente
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QLineEdit, QPushButton, QScrollArea, QGroupBox, 
                             QRadioButton, QCheckBox, QFileDialog, QMessageBox, 
                             QComboBox, QButtonGroup, QDateEdit)
from PyQt6.QtCore import Qt, QDate

# Carrega as variáveis do arquivo .env para que os os.getenv() abaixo funcionem
load_dotenv()

COR_PRIMARIA        = os.getenv("COR_PRIMARIA",       "#003366")  # Azul escuro principal (título, bordas de foco, GroupBox)
COR_PRIMARIA_HOVER  = os.getenv("COR_PRIMARIA_HOVER", "#004080")  # Azul hover dos botões primários
COR_SECUNDARIA      = os.getenv("COR_SECUNDARIA",     "#17a2b8")  # Azul ciano — botão "Anexar"
COR_ALERTA          = os.getenv("COR_ALERTA",         "#dc3545")  # Vermelho — botão "Gerar PDF"
COR_FUNDO_CLARO     = os.getenv("COR_FUNDO_CLARO",   "#f8f9fa")  # Cinza muito claro — fundo do formulário
COR_TEXTO_ESCURO    = os.getenv("COR_TEXTO_ESCURO",   "#212529")  # Quase preto — texto dos labels
COR_TEXTO_CLARO     = os.getenv("COR_TEXTO_CLARO",    "#ffffff")  # Branco — texto sobre fundo colorido
COR_BORDA           = os.getenv("COR_BORDA",          "#ced4da")  # Cinza suave — bordas dos inputs
COR_SALVAR          = "#28a745"                                    # Verde fixo — botão Salvar (sem variável no .env)
COR_SALVAR_HOVER    = "#218838"                                    # Verde escuro — hover do botão Salvar

# NonScrollComboBox
# Subclasse de QComboBox que ignora o scroll do mouse.
# Evita que o usuário troque o valor do combo acidentalmente ao rolar a página.
class NonScrollComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def wheelEvent(self, event):
        # Ignora o evento de scroll do mouse, repassando para o widget pai (scroll da tela)
        event.ignore()

# TelaNovoCadastro
# Widget principal do formulário ECOSOL.
# Recebe o controle de telas (para navegação) e o ID do usuário logado
# (para registrar quem criou o cadastro no banco de dados).
class TelaNovoCadastro(QWidget):
    def __init__(self, controle_telas, usuario_logado_id=None):
        super().__init__()
        self.controle_telas = controle_telas          # Referência ao widget pai (PainelSistema)
        self.usuario_logado_id = usuario_logado_id    # ID do usuário logado, usado como FK no banco
        self.arquivos_anexados = []                   # Lista de caminhos dos arquivos a serem anexados

        # ----- ESTADO DE ATUALIZAÇÃO CADASTRAL (histórico de versões) -----
        # grupo_id_atual: identifica a "pessoa/empreendimento" entre várias versões.
        #   - None enquanto não detectamos nenhum cadastro anterior (será um grupo novo).
        #   - Preenchido quando o operador confirma carregar um cadastro já existente.
        self.grupo_id_atual = None
        # Evita que o popup de "já existe" apareça de novo enquanto os dados do
        # próprio cadastro carregado ainda estão preenchidos no formulário.
        self._verificacao_duplicidade_suspensa = False
        
        # Cria a pasta local de uploads se ainda não existir
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
            
        self.configurar_ui()  # Monta todos os widgets da tela

    def configurar_ui(self):
        # Layout raiz vertical: cabeçalho + scroll + botões
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(10, 10, 10, 10)

        # ----- CABEÇALHO -----
        topo_layout = QHBoxLayout()
        titulo = QLabel("FORMULÁRIO DE CADASTRO ECOSOL")
        # Usa COR_PRIMARIA para a cor do título e a linha decorativa inferior
        titulo.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {COR_PRIMARIA}; border-bottom: 2px solid {COR_PRIMARIA}; padding-bottom: 5px;")
        topo_layout.addWidget(titulo)
        layout_principal.addLayout(topo_layout)

        # ----- ÁREA DE ROLAGEM PRINCIPAL -----
        # QScrollArea permite que o formulário longo role verticalmente
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)                           # Permite que o conteúdo interno redimensione
        scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter)        # Centraliza o conteúdo horizontalmente
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        # Widget interno que carrega todos os grupos do formulário
        conteudo_scroll = QWidget()
        conteudo_scroll.setObjectName("ConteudoForm")  # Nome usado para selecionar no QSS abaixo
        conteudo_scroll.setMaximumWidth(1200)           # Limita a largura máxima para melhor leitura

        # QSS (Qt Style Sheet) do formulário, usando as cores do .env
        # por variáveis Python interpoladas via f-string
        conteudo_scroll.setStyleSheet(f"""
            /* Fundo geral do conteúdo do formulário */
            #ConteudoForm {{ background-color: {COR_FUNDO_CLARO}; }}

            /* Estilo base de todos os campos de entrada */
            QLineEdit, QComboBox, QDateEdit {{
                border: 1px solid {COR_BORDA};
                border-radius: 4px;
                padding: 6px;
                background-color: {COR_TEXTO_CLARO};
            }}

            /* Destaque de borda quando o campo está em foco (selecionado) */
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 1px solid {COR_PRIMARIA};
            }}

            /* Caixas de agrupamento (seções do formulário) */
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COR_BORDA};
                border-radius: 6px;
                margin-top: 12px;
                padding: 15px;
            }}

            /* Título de cada GroupBox (ex: "1 - Identificação...") */
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 0 5px;
                color: {COR_PRIMARIA};
            }}

            /* Labels descritivos dos campos */
            QLabel {{
                font-size: 13px;
                color: {COR_TEXTO_ESCURO};
            }}
        """)

        # Layout vertical interno do scroll — agrupa todas as seções
        layout_form = QVBoxLayout(conteudo_scroll)
        layout_form.setSpacing(15)

        # SEÇÃO: TIPO DE CADASTRO
        # RadioButtons para o usuário escolher a categoria do empreendimento
        grupo_tipo = QGroupBox("Tipo de Cadastro")
        layout_tipo = QHBoxLayout()
        self.bg_tipo = QButtonGroup()  # Garante exclusividade entre os RadioButtons
        
        opcoes_tipo = ["Empreendimento solidário do Amazonas", "Empreendedor individual", "Autônomo", "Outros"]
        self.radios_tipo = {}  # Dicionário: texto -> objeto QRadioButton
        for op in opcoes_tipo:
            rb = QRadioButton(op)
            self.bg_tipo.addButton(rb)   # Registra no grupo para exclusividade
            layout_tipo.addWidget(rb)
            self.radios_tipo[op] = rb    # Salva referência para leitura posterior
            
        # Campo de texto que aparece apenas quando "Outros" é selecionado
        self.input_outros_tipo = QLineEdit()
        self.input_outros_tipo.setPlaceholderText("Qual?")
        self.input_outros_tipo.setEnabled(False)  # Começa desabilitado
        # Habilita/desabilita automaticamente conforme o radio "Outros" é marcado
        self.radios_tipo["Outros"].toggled.connect(self.input_outros_tipo.setEnabled)
        layout_tipo.addWidget(self.input_outros_tipo)
        
        grupo_tipo.setLayout(layout_tipo)
        layout_form.addWidget(grupo_tipo)

        # SEÇÃO 1: IDENTIFICAÇÃO DO EMPREENDIMENTO / REPRESENTANTE
        # Grid de 4 colunas (label | input | label | input) para compactar
        grupo_identificacao = QGroupBox("1 - Identificação do Empreendimento / Representante")
        layout_id = QGridLayout()
        layout_id.setSpacing(10)
        
        # Colunas 1 e 3 são elásticas (campos de input ocupam o espaço disponível)
        layout_id.setColumnStretch(1, 1)
        layout_id.setColumnStretch(3, 1)

        # Campos de texto simples com placeholders descritivos
        self.input_razao = QLineEdit()
        self.input_razao.setPlaceholderText("Digite o nome da empresa ou empreendimento")
        self.input_endereco = QLineEdit()
        self.input_endereco.setPlaceholderText("Digite o endereço completo")
        
        # InputMask garante formatação automática enquanto o usuário digita
        self.input_cep = QLineEdit()
        self.input_cep.setInputMask("00000-000")   # Formato: 69000-000
        # (sem blank customizado ";0": evita bug do Qt que corta zeros finais reais)
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Ex: contato@empreendimento.com")
        self.input_cnpj = QLineEdit()
        self.input_cnpj.setInputMask("00.000.000/0000-00")  # Formato: 00.000.000/0001-00
        # (sem blank customizado ";0": evita bug do Qt que corta zeros finais reais)
        self.input_cpf = QLineEdit()
        self.input_cpf.setInputMask("000.000.000-00")        # Formato: 000.000.000-00
        # (sem blank customizado ";0": evita bug do Qt que corta zeros finais reais)

        # ATUALIZAÇÃO CADASTRAL: ao terminar de digitar o CPF ou o CNPJ (sair do
        # campo ou apertar Enter), verifica se já existe um cadastro com esse
        # documento e, se houver, oferece a opção de carregar os dados antigos.
        self.input_cnpj.editingFinished.connect(lambda: self.verificar_cadastro_existente("cnpj"))
        self.input_cpf.editingFinished.connect(lambda: self.verificar_cadastro_existente("cpf"))

        self.input_rg = QLineEdit()
        self.input_rg.setPlaceholderText("Digite o RG")
        self.input_rep_legal = QLineEdit()
        self.input_rep_legal.setPlaceholderText("Digite o nome do representante legal")
        self.input_cor_raca = QLineEdit()
        self.input_cor_raca.setPlaceholderText("Digite a cor/raça")

        # ----- PAINEL DE SEXO (RadioButtons com fundo transparente) -----
        self.bg_sexo = QButtonGroup()
        widget_sexo = QWidget()
        widget_sexo.setStyleSheet("background: transparent;")  # Evita o fundo cinza padrão do QWidget
        layout_sexo = QHBoxLayout(widget_sexo)
        layout_sexo.setContentsMargins(0, 0, 0, 0)
        layout_sexo.setSpacing(12)

        opcoes_sexo = ["Masculino", "Feminino", "Prefiro não informar", "Outros"]
        self.radios_sexo = {}  # Dicionário: texto -> objeto QRadioButton
        for op in opcoes_sexo:
            rb = QRadioButton(op)
            self.bg_sexo.addButton(rb)
            layout_sexo.addWidget(rb)
            self.radios_sexo[op] = rb

        # Campo livre habilitado apenas quando "Outros" é marcado
        self.input_outros_sexo = QLineEdit()
        self.input_outros_sexo.setPlaceholderText("Especificar...")
        self.input_outros_sexo.setEnabled(False)
        self.radios_sexo["Outros"].toggled.connect(self.input_outros_sexo.setEnabled)
        layout_sexo.addWidget(self.input_outros_sexo)
        layout_sexo.addStretch()  # Empurra os radios para a esquerda

        # Máscara de telefone celular com DDD
        self.input_telefone = QLineEdit()
        self.input_telefone.setInputMask("(00) 00000-0000")
        # (sem blank customizado ";0": evita bug do Qt que corta zeros finais reais)

        # Posicionamento dos campos no grid (linha, coluna)
        layout_id.addWidget(QLabel("Razão Social / Nome Fantasia:"), 0, 0)
        layout_id.addWidget(self.input_razao, 0, 1)
        layout_id.addWidget(QLabel("CNPJ:"), 0, 2)
        layout_id.addWidget(self.input_cnpj, 0, 3)

        layout_id.addWidget(QLabel("Representante Legal:"), 1, 0)
        layout_id.addWidget(self.input_rep_legal, 1, 1)
        layout_id.addWidget(QLabel("CPF:"), 1, 2)
        layout_id.addWidget(self.input_cpf, 1, 3)

        layout_id.addWidget(QLabel("RG:"), 2, 0)
        layout_id.addWidget(self.input_rg, 2, 1)
        layout_id.addWidget(QLabel("Telefone:"), 2, 2)
        layout_id.addWidget(self.input_telefone, 2, 3)

        layout_id.addWidget(QLabel("E-mail / Site:"), 3, 0)
        layout_id.addWidget(self.input_email, 3, 1)
        layout_id.addWidget(QLabel("CEP:"), 3, 2)
        layout_id.addWidget(self.input_cep, 3, 3)

        layout_id.addWidget(QLabel("Endereço:"), 4, 0)
        layout_id.addWidget(self.input_endereco, 4, 1)
        layout_id.addWidget(QLabel("Cor/Raça:"), 4, 2)
        layout_id.addWidget(self.input_cor_raca, 4, 3)

        layout_id.addWidget(QLabel("Sexo:"), 5, 0)
        layout_id.addWidget(widget_sexo, 5, 1, 1, 3)  # Ocupa 3 colunas na linha 5

        grupo_identificacao.setLayout(layout_id)
        layout_form.addWidget(grupo_identificacao)

        # SEÇÃO 2: CARACTERÍSTICAS GERAIS DO EMPREENDIMENTO
        # Combos com campo "Outros" dinâmico e checkboxes de múltipla escolha
        grupo_caracteristicas = QGroupBox("2 - Características gerais do empreendimento")
        layout_caract = QGridLayout()
        layout_caract.setSpacing(10)
        layout_caract.setColumnStretch(1, 1)
        layout_caract.setColumnStretch(3, 1)
        
        # ----- Forma de Organização ECOSOL -----
        # NonScrollComboBox impede troca acidental de valor com scroll do mouse
        self.input_forma_ecosol = NonScrollComboBox()
        self.input_forma_ecosol.addItems(["Cooperativa", "Associação", "Grupo Informal", "Outros"])
        self.input_forma_ecosol.setPlaceholderText("Selecione a Forma Org. ECOSOL...")
        self.input_forma_ecosol.setCurrentIndex(-1)  # Exibe o placeholder ao iniciar
        self.input_outros_forma_ecosol = QLineEdit()
        self.input_outros_forma_ecosol.setPlaceholderText("Especificar...")
        self.input_outros_forma_ecosol.setEnabled(False)
        # Habilita o campo "Outros" apenas quando essa opção é selecionada no combo
        self.input_forma_ecosol.currentTextChanged.connect(
            lambda t: self.input_outros_forma_ecosol.setEnabled(t == "Outros")
        )
        lay_forma_ecosol = QHBoxLayout()
        lay_forma_ecosol.addWidget(self.input_forma_ecosol, 2)   # Combo ocupa 2/3 do espaço
        lay_forma_ecosol.addWidget(self.input_outros_forma_ecosol, 1)  # Campo "Outros" ocupa 1/3

        # ----- Forma de Organização do Empreendimento -----
        self.input_forma_emp = NonScrollComboBox()
        self.input_forma_emp.addItems(["MEI", "Autônomo", "Outros"])
        self.input_forma_emp.setPlaceholderText("Selecione a Forma Org. Emp...")
        self.input_forma_emp.setCurrentIndex(-1)
        self.input_outros_forma_emp = QLineEdit()
        self.input_outros_forma_emp.setPlaceholderText("Especificar...")
        self.input_outros_forma_emp.setEnabled(False)
        self.input_forma_emp.currentTextChanged.connect(
            lambda t: self.input_outros_forma_emp.setEnabled(t == "Outros")
        )
        lay_forma_emp = QHBoxLayout()
        lay_forma_emp.addWidget(self.input_forma_emp, 2)
        lay_forma_emp.addWidget(self.input_outros_forma_emp, 1)

        # ----- Segmento do Empreendimento -----
        self.input_segmento = NonScrollComboBox()
        self.input_segmento.addItems(["Comércio", "Serviços", "Artesanato", "Indústria", "Outros"])
        self.input_segmento.setPlaceholderText("Selecione o Segmento...")
        self.input_segmento.setCurrentIndex(-1)
        self.input_outros_segmento = QLineEdit()
        self.input_outros_segmento.setPlaceholderText("Especificar...")
        self.input_outros_segmento.setEnabled(False)
        self.input_segmento.currentTextChanged.connect(
            lambda t: self.input_outros_segmento.setEnabled(t == "Outros")
        )
        lay_segmento = QHBoxLayout()
        lay_segmento.addWidget(self.input_segmento, 2)
        lay_segmento.addWidget(self.input_outros_segmento, 1)

        # ----- Campos de texto livres -----
        self.input_materia_prima = QLineEdit()
        self.input_materia_prima.setPlaceholderText("Digite as matérias-primas")
        self.input_local_prod = QLineEdit()
        self.input_local_prod.setPlaceholderText("Digite o local de produção")
        self.input_onde_comerc = QLineEdit()
        self.input_onde_comerc.setPlaceholderText("Onde comercializa?")

        # ----- Beneficiários: 4 campos numéricos lado a lado -----
        layout_benef = QHBoxLayout()
        self.in_dir_m = QLineEdit(); self.in_dir_m.setPlaceholderText("Diretos Masculino")
        self.in_dir_f = QLineEdit(); self.in_dir_f.setPlaceholderText("Diretos Feminino")
        self.in_ind_m = QLineEdit(); self.in_ind_m.setPlaceholderText("Indiretos Masculino")
        self.in_ind_f = QLineEdit(); self.in_ind_f.setPlaceholderText("Indiretos Feminino")
        layout_benef.addWidget(self.in_dir_m)
        layout_benef.addWidget(self.in_dir_f)
        layout_benef.addWidget(self.in_ind_m)
        layout_benef.addWidget(self.in_ind_f)

        # ----- Combos simples Sim/Não -----
        self.input_cartao = NonScrollComboBox()
        self.input_cartao.addItems(["Sim", "Não"])
        self.input_cartao.setPlaceholderText("Selecione...")
        self.input_cartao.setCurrentIndex(-1)

        self.input_pix = NonScrollComboBox()
        self.input_pix.addItems(["Sim", "Não"])
        self.input_pix.setPlaceholderText("Selecione...")
        self.input_pix.setCurrentIndex(-1)

        # Posicionamento dos campos no grid da seção 2
        layout_caract.addWidget(QLabel("1 - Forma Org. ECOSOL:"), 0, 0)
        layout_caract.addLayout(lay_forma_ecosol, 0, 1)
        layout_caract.addWidget(QLabel("1.1 - Forma Org. Emp.:"), 0, 2)
        layout_caract.addLayout(lay_forma_emp, 0, 3)

        layout_caract.addWidget(QLabel("2 - Segmento:"), 1, 0)
        layout_caract.addLayout(lay_segmento, 1, 1)
        layout_caract.addWidget(QLabel("3 - Matéria-prima:"), 1, 2)
        layout_caract.addWidget(self.input_materia_prima, 1, 3)

        layout_caract.addWidget(QLabel("4 - Local Produção:"), 2, 0)
        layout_caract.addWidget(self.input_local_prod, 2, 1)
        layout_caract.addWidget(QLabel("5 - Onde Comercializa:"), 2, 2)
        layout_caract.addWidget(self.input_onde_comerc, 2, 3)

        layout_caract.addWidget(QLabel("6 - Beneficiários:"), 3, 0)
        layout_caract.addLayout(layout_benef, 3, 1, 1, 3)  # Ocupa 3 colunas

        layout_caract.addWidget(QLabel("7 - Máquina Cartão?:"), 4, 0)
        layout_caract.addWidget(self.input_cartao, 4, 1)
        layout_caract.addWidget(QLabel("7.1 - PIX?:"), 4, 2)
        layout_caract.addWidget(self.input_pix, 4, 3)

        # ----- Grupos de Checkboxes (múltipla escolha) -----
        # criar_grupo_checkboxes retorna a lista de QCheckBox para leitura posterior
        self.checks_classificacao = self.criar_grupo_checkboxes([
            "Agricultura Familiar", "Artistas", "Catadores", "Técnicos", 
            "Autônomos", "Artesãos", "Assentados", "Garimpeiros", "Desempregados", "Outros"
        ], layout_caract, "8 - Classificação Social:", 5)

        self.checks_motivo = self.criar_grupo_checkboxes([
            "Alternativa ao desemprego", "Produtos orgânicos", "Renda", 
            "Motivação social", "Qualificação", "Todos são donos", "Grupos étnicos", "Outros"
        ], layout_caract, "9 - Motivo Criação:", 6)

        grupo_caracteristicas.setLayout(layout_caract)
        layout_form.addWidget(grupo_caracteristicas)

        # SEÇÃO 3: ATIVIDADE ECONÔMICA E SITUAÇÃO DE TRABALHO
        grupo_atividade = QGroupBox("3 - Atividade econômica e situação de trabalho")
        layout_ativ = QGridLayout()
        layout_ativ.setSpacing(10)
        layout_ativ.setColumnStretch(1, 1)
        layout_ativ.setColumnStretch(3, 1)

        # Checkboxes de formas de comercialização (múltipla escolha)
        self.checks_formas_comerc = self.criar_grupo_checkboxes([
            "Lojas/espaços fixos", "Feiras", "Central de comercialização", "Comércio Eletrônico"
        ], layout_ativ, "1 - Formas de Comercialização:", 0)

        # Campo de texto para produtos comercializados
        self.input_produtos = QLineEdit()
        self.input_produtos.setPlaceholderText("Digite os produtos comercializados")

        # Combo Sim/Não para taxa/contribuição
        self.input_pagam_taxa = NonScrollComboBox()
        self.input_pagam_taxa.addItems(["Sim", "Não"])
        self.input_pagam_taxa.setPlaceholderText("Selecione...")
        self.input_pagam_taxa.setCurrentIndex(-1)

        # Combo de forma de contribuição
        self.input_forma_contrib = NonScrollComboBox()
        self.input_forma_contrib.addItems(["Taxa fixa", "Percentual", "Espontânea", "Caixa comum", "Não se aplica"])
        self.input_forma_contrib.setPlaceholderText("Selecione a Forma...")
        self.input_forma_contrib.setCurrentIndex(-1)

        # ----- Renda Preponderante (com campo "Outros" dinâmico) -----
        self.input_renda = NonScrollComboBox()
        self.input_renda.addItems(["Renda individual/familiar", "Complemento atividades", "Complemento governamental", "Aposentadoria", "Outros"])
        self.input_renda.setPlaceholderText("Selecione a Renda...")
        self.input_renda.setCurrentIndex(-1)
        self.input_outros_renda = QLineEdit()
        self.input_outros_renda.setPlaceholderText("Especificar...")
        self.input_outros_renda.setEnabled(False)
        self.input_renda.currentTextChanged.connect(
            lambda t: self.input_outros_renda.setEnabled(t == "Outros")
        )
        lay_renda = QHBoxLayout()
        lay_renda.addWidget(self.input_renda, 2)
        lay_renda.addWidget(self.input_outros_renda, 1)

        # ----- Para quem comercializa (com campo "Outros" dinâmico) -----
        self.input_para_quem = NonScrollComboBox()
        self.input_para_quem.addItems(["Consumidor final", "Atacadistas", "Governo", "Empresas privadas", "Outros"])
        self.input_para_quem.setPlaceholderText("Selecione o Destino...")
        self.input_para_quem.setCurrentIndex(-1)
        self.input_outros_para_quem = QLineEdit()
        self.input_outros_para_quem.setPlaceholderText("Especificar...")
        self.input_outros_para_quem.setEnabled(False)
        self.input_para_quem.currentTextChanged.connect(
            lambda t: self.input_outros_para_quem.setEnabled(t == "Outros")
        )
        lay_para_quem = QHBoxLayout()
        lay_para_quem.addWidget(self.input_para_quem, 2)
        lay_para_quem.addWidget(self.input_outros_para_quem, 1)

        # Combo Sim/Não para dificuldade de comercialização
        self.input_dificuldade = NonScrollComboBox()
        self.input_dificuldade.addItems(["Sim", "Não"])
        self.input_dificuldade.setPlaceholderText("Selecione...")
        self.input_dificuldade.setCurrentIndex(-1)

        # Combo de responsável pelas vendas
        self.input_resp_vendas = NonScrollComboBox()
        self.input_resp_vendas.addItems(["Cada um vende o seu", "Rodízio", "Sócios designados", "Pessoas não sócias", "Não se aplica"])
        self.input_resp_vendas.setPlaceholderText("Selecione o Responsável...")
        self.input_resp_vendas.setCurrentIndex(-1)

        # Posicionamento dos campos no grid da seção 3
        layout_ativ.addWidget(QLabel("2 - Produtos que comercializa:"), 1, 0)
        layout_ativ.addWidget(self.input_produtos, 1, 1)
        layout_ativ.addWidget(QLabel("3 - Pagam taxa/contribuição?"), 1, 2)
        layout_ativ.addWidget(self.input_pagam_taxa, 1, 3)

        layout_ativ.addWidget(QLabel("4 - Forma de contribuição:"), 2, 0)
        layout_ativ.addWidget(self.input_forma_contrib, 2, 1)
        layout_ativ.addWidget(QLabel("5 - Renda preponderante:"), 2, 2)
        layout_ativ.addLayout(lay_renda, 2, 3)

        layout_ativ.addWidget(QLabel("6 - Para quem comercializa?"), 3, 0)
        layout_ativ.addLayout(lay_para_quem, 3, 1)
        layout_ativ.addWidget(QLabel("7 - Encontra dificuldade?"), 3, 2)
        layout_ativ.addWidget(self.input_dificuldade, 3, 3)

        layout_ativ.addWidget(QLabel("8 - Responsável vendas:"), 4, 0)
        layout_ativ.addWidget(self.input_resp_vendas, 4, 1)

        grupo_atividade.setLayout(layout_ativ)
        layout_form.addWidget(grupo_atividade)

        # SEÇÃO FINAL: OBSERVAÇÕES, LOCAL, DATA E UPLOAD DE ARQUIVOS
        grupo_final = QGroupBox("Finalização e Anexos")
        layout_final = QGridLayout()
        layout_final.setSpacing(10)
        layout_final.setColumnStretch(1, 1)
        layout_final.setColumnStretch(3, 1)

        # Campo de observações gerais
        self.input_obs = QLineEdit()
        self.input_obs.setPlaceholderText("Digite observações adicionais")

        # ----- Local do Cadastro (com campo "Outros" dinâmico) -----
        self.input_local = NonScrollComboBox()
        self.input_local.addItems(["Manaus", "Itacoatiara", "Parintins", "Tefé", "Outros"])
        self.input_local.setPlaceholderText("Selecione o Local...")
        self.input_local.setCurrentIndex(-1)
        self.input_outros_local = QLineEdit()
        self.input_outros_local.setPlaceholderText("Especificar Local...")
        self.input_outros_local.setEnabled(False)
        self.input_local.currentTextChanged.connect(
            lambda t: self.input_outros_local.setEnabled(t == "Outros")
        )
        lay_local = QHBoxLayout()
        lay_local.addWidget(self.input_local, 2)
        lay_local.addWidget(self.input_outros_local, 1)

        # ----- Seletor de Data do Formulário -----
        self.input_data_form = QDateEdit()
        self.input_data_form.setCalendarPopup(True)          # Abre calendário ao clicar
        self.input_data_form.setDate(QDate.currentDate())    # Padrão: data de hoje
        self.input_data_form.setDisplayFormat("dd/MM/yyyy")  # Formato visual: dia/mês/ano
        self.input_data_form.setStyleSheet("QDateEdit { min-width: 160px; padding: 5px; }")

        # ----- Botão e indicador de arquivos anexados -----
        # Usa COR_SECUNDARIA do .env para o botão de anexar (azul ciano)
        self.btn_anexar = QPushButton("Anexar RG, CPF e Comprovante")
        self.btn_anexar.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {COR_SECUNDARIA}; 
                color: {COR_TEXTO_CLARO}; 
                border-radius: 4px; 
                padding: 6px 12px; 
                font-weight: bold; 
            }}
            QPushButton:hover {{ background-color: {COR_PRIMARIA}; }}
        """)
        self.btn_anexar.clicked.connect(self.selecionar_arquivos)

        # Label que exibe quantos arquivos foram selecionados
        self.lbl_arquivos = QLabel("Nenhum arquivo selecionado.")
        self.lbl_arquivos.setStyleSheet("color: #666; font-style: italic;")

        layout_upload = QHBoxLayout()
        layout_upload.addWidget(self.btn_anexar)
        layout_upload.addWidget(self.lbl_arquivos)
        layout_upload.addStretch()  # Empurra tudo para a esquerda

        # Posicionamento dos widgets finais no grid
        layout_final.addWidget(QLabel("OBS:"), 0, 0)
        layout_final.addWidget(self.input_obs, 0, 1, 1, 3)  # Ocupa 3 colunas

        layout_final.addWidget(QLabel("Local:"), 1, 0)
        layout_final.addLayout(lay_local, 1, 1)
        layout_final.addWidget(QLabel("Data do Formulário:"), 1, 2)
        layout_final.addWidget(self.input_data_form, 1, 3)

        layout_final.addWidget(QLabel("Arquivos:"), 2, 0)
        layout_final.addLayout(layout_upload, 2, 1, 1, 3)

        grupo_final.setLayout(layout_final)
        layout_form.addWidget(grupo_final)

        # BARRA DE BOTÕES DE AÇÃO (Salvar e Gerar PDF)
        # Posicionados lado a lado e centralizados com addStretch
        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(20)
        layout_botoes.setContentsMargins(0, 15, 0, 5)
        layout_botoes.addStretch()  # Empurra os botões para o centro

        # Botão Salvar — usa cor verde fixa (COR_SALVAR) pois não há variável no .env para isso
        self.btn_salvar = QPushButton("Salvar Cadastro Local")
        self.btn_salvar.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {COR_SALVAR}; 
                color: {COR_TEXTO_CLARO}; 
                padding: 10px 22px; 
                font-size: 14px; 
                font-weight: bold; 
                border-radius: 4px; 
            }}
            QPushButton:hover {{ background-color: {COR_SALVAR_HOVER}; }}
        """)
        self.btn_salvar.setFixedWidth(240)
        self.btn_salvar.clicked.connect(self.salvar_cadastro)
        layout_botoes.addWidget(self.btn_salvar)

        # Botão Gerar PDF — usa COR_ALERTA do .env (vermelho)
        self.btn_pdf = QPushButton("Gerar PDF")
        self.btn_pdf.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {COR_ALERTA}; 
                color: {COR_TEXTO_CLARO}; 
                padding: 10px 22px; 
                font-size: 14px; 
                font-weight: bold; 
                border-radius: 4px; 
            }}
            QPushButton:hover {{ background-color: #c82333; }}
        """)
        self.btn_pdf.setFixedWidth(240)
        self.btn_pdf.clicked.connect(self.gerar_pdf)
        layout_botoes.addWidget(self.btn_pdf)

        layout_botoes.addStretch()  # Fecha o centering dos botões
        layout_form.addLayout(layout_botoes)

        layout_form.addStretch()  # Empurra tudo para cima quando a tela é grande

        # Finaliza: coloca o widget de conteúdo dentro do scroll e adiciona à tela
        scroll.setWidget(conteudo_scroll)
        layout_principal.addWidget(scroll)

    # criar_grupo_checkboxes
    # Cria um bloco de QCheckBoxes dispostos em grid de até 4 colunas.
    # Quando "Outros" está na lista, cria automaticamente um QLineEdit ao lado.
    # Retorna a lista de QCheckBox para uso em obter_texto_checkboxes().
    def criar_grupo_checkboxes(self, opcoes, grid_layout, label_texto, row):
        # Label da linha (ex: "8 - Classificação Social:")
        label = QLabel(label_texto)
        label.setStyleSheet("font-weight: bold; color: #333;")
        grid_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # Container dos checkboxes com fundo transparente (evita cinza indesejado)
        widget_cb = QWidget()
        widget_cb.setStyleSheet("background: transparent;")
        layout_cb = QGridLayout(widget_cb)
        layout_cb.setContentsMargins(0, 0, 0, 0)
        layout_cb.setSpacing(8)

        lista_cb = []       # Lista que será retornada com todos os checkboxes
        colunas_max = 4     # Máximo de checkboxes por linha
        col = 0
        r = 0

        for op in opcoes:
            cb = QCheckBox(op)
            lista_cb.append(cb)

            if op == "Outros":
                # Para "Outros": cria um sub-widget com o checkbox + campo de texto na mesma linha
                sub_widget = QWidget()
                sub_widget.setStyleSheet("background: transparent;")
                sub_layout = QHBoxLayout(sub_widget)
                sub_layout.setContentsMargins(0, 0, 0, 0)
                sub_layout.setSpacing(5)
                sub_layout.addWidget(cb)

                input_outros = QLineEdit()
                input_outros.setPlaceholderText("Qual?")
                input_outros.setEnabled(False)                    # Desabilitado até marcar o checkbox
                cb.toggled.connect(input_outros.setEnabled)       # Habilita ao marcar
                sub_layout.addWidget(input_outros)

                # Armazena referência ao campo de texto dentro do próprio checkbox
                cb.setProperty("campo_outros", input_outros)
                layout_cb.addWidget(sub_widget, r, col)
            else:
                layout_cb.addWidget(cb, r, col)

            col += 1
            if col >= colunas_max:   # Quebra de linha a cada 4 colunas
                col = 0
                r += 1

        # O bloco de checkboxes ocupa as 3 colunas restantes do grid principal
        grid_layout.addWidget(widget_cb, row, 1, 1, 3)
        return lista_cb

    # obter_texto_checkboxes
    # Percorre a lista de QCheckBoxes e retorna uma string CSV com os marcados.
    # Se "Outros" estiver marcado e tiver texto, inclui "Outros: <texto>".
    def obter_texto_checkboxes(self, lista_checkboxes):
        selecionados = []
        for cb in lista_checkboxes:
            if cb.isChecked():
                texto = cb.text()
                if texto == "Outros":
                    # Recupera o QLineEdit vinculado via setProperty
                    campo = cb.property("campo_outros")
                    if campo and campo.text().strip():
                        texto = f"Outros: {campo.text().strip()}"
                selecionados.append(texto)
        return ", ".join(selecionados)  # Ex: "Cooperativa, Associação"

    # selecionar_arquivos
    # Abre um diálogo para o usuário selecionar PDFs ou imagens.
    # Acumula os caminhos em self.arquivos_anexados para uso no salvar_cadastro.
    def selecionar_arquivos(self):
        arquivos, _ = QFileDialog.getOpenFileNames(
            self, "Selecione os Documentos", "", 
            "Imagens/PDFs (*.pdf *.png *.jpg *.jpeg)"
        )
        if arquivos:
            self.arquivos_anexados.extend(arquivos)  # Adiciona sem sobrescrever seleções anteriores
            self.lbl_arquivos.setText(f"{len(self.arquivos_anexados)} arquivo(s) selecionado(s).")

    # =========================================================================
    # verificar_cadastro_existente
    # Chamado quando o operador termina de digitar o CPF ou o CNPJ.
    # Consulta o banco local: se já existir algum cadastro com esse documento,
    # pergunta se o operador quer carregar os dados da versão mais recente
    # (fluxo de ATUALIZAÇÃO CADASTRAL) em vez de preencher tudo do zero.
    #
    # Parâmetros:
    #   campo → "cpf" ou "cnpj", indica qual dos dois campos disparou a checagem
    # =========================================================================
    def verificar_cadastro_existente(self, campo):
        # Enquanto os dados de um cadastro carregado ainda estão no formulário,
        # não repete a pergunta (evita popup repetido sem o operador ter mudado nada)
        if self._verificacao_duplicidade_suspensa:
            return

        # Lê e limpa o valor do campo que disparou o evento, removendo a máscara.
        # Com o blank padrão do Qt (espaço), campo vazio já resulta em string vazia
        # diretamente após remover pontuação e espaços, sem precisar comparar com "0000...".
        if campo == "cpf":
            valor = self.input_cpf.text().replace(".", "").replace("-", "").replace(" ", "").strip()
        else:  # cnpj
            valor = self.input_cnpj.text().replace(".", "").replace("/", "").replace("-", "").replace(" ", "").strip()

        if not valor:
            return  # Campo vazio: nada para verificar

        try:
            conn = sqlite3.connect('ecosol_local.db')
            cursor = conn.cursor()
            # Busca a versão mais recente de qualquer cadastro com esse CPF/CNPJ.
            # Agrupar por grupo_id e ordenar por data garante que pegamos a última
            # atualização, e não uma versão antiga do histórico.
            cursor.execute(f"""
                SELECT grupo_id, razao_social_nome, data_cadastro
                FROM cadastros_ecosol
                WHERE {campo} = ? AND {campo} != ''
                ORDER BY data_cadastro DESC
                LIMIT 1
            """, (valor,))
            resultado = cursor.fetchone()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao verificar cadastro existente: {str(e)}")
            return

        if not resultado:
            return  # Nenhum cadastro encontrado com esse documento — segue um cadastro novo

        grupo_id_encontrado, nome_encontrado, data_encontrada = resultado

        # Se o cadastro encontrado já É o que está carregado no formulário agora
        # (mesmo grupo_id), não há necessidade de perguntar de novo
        if self.grupo_id_atual == grupo_id_encontrado:
            return

        resposta = QMessageBox.question(
            self, "Cadastro Já Existe",
            f"Já existe um cadastro para este documento:\n\n"
            f"Nome/Razão Social: {nome_encontrado}\n"
            f"Última atualização: {data_encontrada}\n\n"
            f"Deseja carregar os dados existentes para fazer uma ATUALIZAÇÃO CADASTRAL?\n\n"
            f"(Escolher 'Não' mantém os dados atuais e cria um cadastro novo e independente)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            self.carregar_dados_cadastro(grupo_id_encontrado)

    # =========================================================================
    # carregar_dados_cadastro
    # Busca a versão mais recente do grupo_id informado e preenche TODOS os
    # campos do formulário com esses dados, entrando em modo "atualização
    # cadastral": ao salvar, o novo registro herdará o mesmo grupo_id, mantendo
    # o histórico de versões da mesma pessoa/empreendimento.
    # =========================================================================
    def carregar_dados_cadastro(self, grupo_id):
        try:
            conn = sqlite3.connect('ecosol_local.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM cadastros_ecosol
                WHERE grupo_id = ?
                ORDER BY data_cadastro DESC
                LIMIT 1
            """, (grupo_id,))
            colunas = [desc[0] for desc in cursor.description]
            linha = cursor.fetchone()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar cadastro: {str(e)}")
            return

        if not linha:
            return  # Segurança: grupo_id não encontrado (não deveria ocorrer aqui)

        dados = dict(zip(colunas, linha))  # Facilita o acesso por nome de coluna

        # Suspende a verificação de duplicidade enquanto preenchemos os campos,
        # já que vamos justamente reescrever o CPF/CNPJ que disparou a busca
        self._verificacao_duplicidade_suspensa = True

        # ----- Tipo de Cadastro (radio + campo "Outros") -----
        self._marcar_radio_com_outros(
            self.radios_tipo, self.input_outros_tipo, dados.get("tipo_cadastro") or ""
        )

        # ----- Campos de texto simples -----
        self.input_razao.setText(dados.get("razao_social_nome") or "")
        self.input_endereco.setText(dados.get("endereco") or "")
        self.input_email.setText(dados.get("email") or "")
        self.input_rg.setText(dados.get("rg") or "")
        self.input_rep_legal.setText(dados.get("representante_legal") or "")
        self.input_cor_raca.setText(dados.get("cor_raca") or "")
        self.input_materia_prima.setText(dados.get("materia_prima") or "")
        self.input_local_prod.setText(dados.get("local_producao") or "")
        self.input_onde_comerc.setText(dados.get("onde_comercializa") or "")
        self.input_produtos.setText(dados.get("produtos_comercializados") or "")
        self.input_obs.setText(dados.get("obs") or "")

        # ----- Campos com máscara (CEP, CNPJ, CPF, telefone) -----
        # setText respeita a máscara já configurada nesses campos automaticamente
        self.input_cep.setText(dados.get("cep") or "")
        self.input_cnpj.setText(dados.get("cnpj") or "")
        self.input_cpf.setText(dados.get("cpf") or "")
        self.input_telefone.setText(dados.get("telefone") or "")

        # ----- Sexo (radio + campo "Outros") -----
        self._marcar_radio_com_outros(
            self.radios_sexo, self.input_outros_sexo, dados.get("sexo") or ""
        )

        # ----- Combos com campo "Outros" dinâmico -----
        self._selecionar_combo_com_outros(
            self.input_forma_ecosol, self.input_outros_forma_ecosol, dados.get("forma_organizacao_ecosol") or ""
        )
        self._selecionar_combo_com_outros(
            self.input_forma_emp, self.input_outros_forma_emp, dados.get("forma_organizacao_emp") or ""
        )
        self._selecionar_combo_com_outros(
            self.input_segmento, self.input_outros_segmento, dados.get("segmento_empreendimento") or ""
        )
        self._selecionar_combo_com_outros(
            self.input_renda, self.input_outros_renda, dados.get("renda_preponderante") or ""
        )
        self._selecionar_combo_com_outros(
            self.input_para_quem, self.input_outros_para_quem, dados.get("para_quem_comercializa") or ""
        )
        self._selecionar_combo_com_outros(
            self.input_local, self.input_outros_local, dados.get("local_cadastro") or ""
        )

        # ----- Combos simples (Sim/Não e demais, sem campo "Outros") -----
        self._selecionar_combo_simples(self.input_cartao, dados.get("maquina_cartao") or "")
        self._selecionar_combo_simples(self.input_pix, dados.get("pix") or "")
        self._selecionar_combo_simples(self.input_pagam_taxa, dados.get("pagam_taxa") or "")
        self._selecionar_combo_simples(self.input_forma_contrib, dados.get("forma_contribuicao") or "")
        self._selecionar_combo_simples(self.input_dificuldade, dados.get("dificuldade_comercializacao") or "")
        self._selecionar_combo_simples(self.input_resp_vendas, dados.get("responsavel_vendas") or "")

        # ----- Beneficiários (numéricos) -----
        self.in_dir_m.setText(str(dados.get("beneficiarios_diretos_m") or 0))
        self.in_dir_f.setText(str(dados.get("beneficiarios_diretos_f") or 0))
        self.in_ind_m.setText(str(dados.get("beneficiarios_indiretos_m") or 0))
        self.in_ind_f.setText(str(dados.get("beneficiarios_indiretos_f") or 0))

        # ----- Grupos de checkboxes (classificação, motivo, formas de comercialização) -----
        self._marcar_checkboxes_csv(self.checks_classificacao, dados.get("classificacao_social") or "")
        self._marcar_checkboxes_csv(self.checks_motivo, dados.get("motivo_criacao") or "")
        self._marcar_checkboxes_csv(self.checks_formas_comerc, dados.get("formas_comercializacao") or "")

        # ----- Data do formulário -----
        data_formulario_str = dados.get("data_formulario")
        if data_formulario_str:
            self.input_data_form.setDate(QDate.fromString(data_formulario_str, "yyyy-MM-dd"))

        # Entra em modo "atualização cadastral": o grupo_id é herdado da versão
        # anterior, então ao salvar, este novo registro fica ligado ao histórico
        self.grupo_id_atual = grupo_id

        self._verificacao_duplicidade_suspensa = False

        QMessageBox.information(
            self, "Dados Carregados",
            "Os dados do cadastro anterior foram carregados.\n\n"
            "Edite os campos necessários e clique em Salvar para registrar a ATUALIZAÇÃO CADASTRAL."
        )

    # =========================================================================
    # _marcar_radio_com_outros
    # Marca o QRadioButton cujo texto corresponde ao valor salvo. Se o valor
    # salvo começa com "Outros: ", marca o radio "Outros" e preenche o campo
    # de texto livre associado com o restante do texto.
    # =========================================================================
    def _marcar_radio_com_outros(self, dict_radios, campo_outros, valor_salvo):
        if not valor_salvo:
            return
        if valor_salvo.startswith("Outros:") and "Outros" in dict_radios:
            dict_radios["Outros"].setChecked(True)
            campo_outros.setText(valor_salvo.split(":", 1)[1].strip())
        elif valor_salvo in dict_radios:
            dict_radios[valor_salvo].setChecked(True)

    # =========================================================================
    # _selecionar_combo_com_outros
    # Seleciona no combo o item cujo texto corresponde ao valor salvo. Se o
    # valor salvo começa com "Outros: ", seleciona "Outros" no combo e
    # preenche o campo de texto livre associado com o restante do texto.
    # =========================================================================
    def _selecionar_combo_com_outros(self, combo, campo_outros, valor_salvo):
        if not valor_salvo:
            combo.setCurrentIndex(-1)
            return
        if valor_salvo.startswith("Outros:"):
            indice = combo.findText("Outros")
            if indice >= 0:
                combo.setCurrentIndex(indice)
            campo_outros.setText(valor_salvo.split(":", 1)[1].strip())
        else:
            indice = combo.findText(valor_salvo)
            combo.setCurrentIndex(indice)  # findText retorna -1 se não achar (mantém placeholder)

    # =========================================================================
    # _selecionar_combo_simples
    # Seleciona no combo o item cujo texto é exatamente igual ao valor salvo.
    # Usado para combos sem opção "Outros" (Sim/Não, formas de contribuição etc).
    # =========================================================================
    def _selecionar_combo_simples(self, combo, valor_salvo):
        indice = combo.findText(valor_salvo) if valor_salvo else -1
        combo.setCurrentIndex(indice)

    # =========================================================================
    # _marcar_checkboxes_csv
    # Recebe a string CSV salva no banco (ex: "Cooperativa, Outros: Bazar") e
    # marca os QCheckBox correspondentes na lista. Trata o caso especial do
    # item "Outros", preenchendo seu campo de texto livre associado.
    # =========================================================================
    def _marcar_checkboxes_csv(self, lista_checkboxes, valor_csv):
        if not valor_csv:
            return
        itens_salvos = [item.strip() for item in valor_csv.split(",")]

        for cb in lista_checkboxes:
            texto_cb = cb.text()

            if texto_cb == "Outros":
                # Caso especial: procura um item salvo no formato "Outros: <texto>"
                item_outros = next((item for item in itens_salvos if item.startswith("Outros:")), None)
                if item_outros:
                    cb.setChecked(True)
                    campo = cb.property("campo_outros")
                    if campo:
                        campo.setText(item_outros.split(":", 1)[1].strip())
            elif texto_cb in itens_salvos:
                cb.setChecked(True)

    # =========================================================================
    # _verificar_campos_vazios
    # Monta a lista de campos não preenchidos, agrupados por seção do
    # formulário, para exibir no popup de aviso antes de salvar. Como quase
    # todos os campos são opcionais, isso serve apenas como um alerta — o
    # operador decide se quer voltar e completar ou salvar assim mesmo.
    #
    # Recebe os valores já lidos e normalizados em salvar_cadastro (evita ler
    # os widgets de novo e duplicar a lógica de limpeza de máscara/"Outros").
    # Retorna uma lista de tuplas (nome_secao, [lista_de_campos_vazios]),
    # omitindo seções sem nenhum campo vazio.
    # =========================================================================
    def _verificar_campos_vazios(self, endereco, email, rg, cep, cnpj, cpf, telefone,
                                  sexo, val_forma_ecosol, val_forma_emp, val_segmento,
                                  val_renda, val_para_quem, val_local, grid_class_social,
                                  grid_motivos, grid_formas_comerc):

        # Estrutura: (nome_da_seção, [(rótulo_amigável, está_vazio?), ...])
        # está_vazio? já vem calculado como booleano para cada campo.
        estrutura = [
            ("Identificação do Empreendimento / Representante", [
                ("Endereço",              not endereco),
                ("CEP",                   not cep),
                ("E-mail / Site",         not email),
                ("CNPJ",                  not cnpj),
                ("CPF",                   not cpf),
                ("RG",                    not rg),
                ("Representante Legal",   not self.input_rep_legal.text().strip()),
                ("Telefone",              not telefone),
                ("Cor/Raça",              not self.input_cor_raca.text().strip()),
                ("Sexo",                  not sexo),
            ]),
            ("Características Gerais do Empreendimento", [
                ("Forma Org. ECOSOL",         not val_forma_ecosol),
                ("Forma Org. Empreendimento", not val_forma_emp),
                ("Segmento",                  not val_segmento),
                ("Matéria-Prima",             not self.input_materia_prima.text().strip()),
                ("Local de Produção",         not self.input_local_prod.text().strip()),
                ("Onde Comercializa",         not self.input_onde_comerc.text().strip()),
                ("Beneficiários Diretos (M)",   not self.in_dir_m.text().strip()),
                ("Beneficiários Diretos (F)",   not self.in_dir_f.text().strip()),
                ("Beneficiários Indiretos (M)", not self.in_ind_m.text().strip()),
                ("Beneficiários Indiretos (F)", not self.in_ind_f.text().strip()),
                ("Possui Máquina de Cartão",  self.input_cartao.currentIndex() == -1),
                ("Possui PIX",                self.input_pix.currentIndex() == -1),
                ("Classificação Social",      not grid_class_social),
                ("Motivo de Criação",         not grid_motivos),
            ]),
            ("Atividade Econômica e Situação de Trabalho", [
                ("Formas de Comercialização",       not grid_formas_comerc),
                ("Produtos Comercializados",        not self.input_produtos.text().strip()),
                ("Pagam Taxa/Contribuição",         self.input_pagam_taxa.currentIndex() == -1),
                ("Forma de Contribuição",           self.input_forma_contrib.currentIndex() == -1),
                ("Renda Preponderante",             not val_renda),
                ("Para Quem Comercializa",          not val_para_quem),
                ("Dificuldade de Comercialização",  self.input_dificuldade.currentIndex() == -1),
                ("Responsável pelas Vendas",        self.input_resp_vendas.currentIndex() == -1),
            ]),
            ("Finalização e Anexos", [
                ("Observações",   not self.input_obs.text().strip()),
                ("Local",         not val_local),
                ("Arquivos Anexados", len(self.arquivos_anexados) == 0),
            ]),
        ]

        # Filtra: mantém só as seções que têm ao menos 1 campo vazio,
        # e dentro delas, só os rótulos dos campos que estão vazios
        secoes_resultado = []
        for nome_secao, campos in estrutura:
            vazios = [rotulo for rotulo, esta_vazio in campos if esta_vazio]
            if vazios:
                secoes_resultado.append((nome_secao, vazios))

        return secoes_resultado

    # =========================================================================
    # _exibir_popup_campos_vazios
    # Mostra um popup listando os campos vazios agrupados por seção, com dois
    # botões: "Continuar" (salva mesmo assim) ou "Voltar" (cancela o salvamento
    # para o operador completar o formulário). Retorna True se deve continuar
    # salvando, False se deve interromper.
    # =========================================================================
    def _exibir_popup_campos_vazios(self, secoes_com_campos_vazios):
        linhas_mensagem = ["Os seguintes campos opcionais estão em branco:\n"]
        for nome_secao, campos_vazios in secoes_com_campos_vazios:
            linhas_mensagem.append(f"\n{nome_secao}:")
            for campo in campos_vazios:
                linhas_mensagem.append(f"   • {campo}")

        linhas_mensagem.append("\n\nDeseja continuar e salvar o cadastro assim mesmo,")
        linhas_mensagem.append("ou voltar para completar os campos?")

        caixa = QMessageBox(self)
        caixa.setWindowTitle("Campos em Branco")
        caixa.setIcon(QMessageBox.Icon.Warning)
        caixa.setText("\n".join(linhas_mensagem))

        btn_continuar = caixa.addButton("Continuar", QMessageBox.ButtonRole.AcceptRole)
        btn_voltar    = caixa.addButton("Voltar",    QMessageBox.ButtonRole.RejectRole)
        caixa.setDefaultButton(btn_voltar)  # "Voltar" é o padrão: evita salvar incompleto por engano

        caixa.exec()

        return caixa.clickedButton() == btn_continuar

    # gerar_pdf
    # Placeholder do botão "Gerar PDF" — ainda não implementado.
    # Exige ao menos a Razão Social preenchida antes de prosseguir.
    def gerar_pdf(self):
        razao = self.input_razao.text().strip()
        if not razao:
            QMessageBox.warning(self, "Aviso", "Preencha ao menos a Razão Social para gerar o PDF!")
            return
        QMessageBox.information(self, "PDF", f"Documento PDF de coleta criado para:\n{razao}")


    # salvar_cadastro
    # Coleta todos os valores do formulário, valida os campos obrigatórios
    # e insere um novo registro na tabela cadastros_ecosol do SQLite local.
    # Também copia os arquivos anexados para a pasta "uploads/" e registra
    # cada um em arquivos_anexos para sincronização futura.
    def salvar_cadastro(self):
        # ----- Lê o Tipo de Cadastro selecionado -----
        tipo_cadastro = ""
        for texto, rb in self.radios_tipo.items():
            if rb.isChecked():
                # Se "Outros", concatena o texto do campo livre
                tipo_cadastro = f"Outros: {self.input_outros_tipo.text()}" if texto == "Outros" else texto
                break

        if not tipo_cadastro:
            QMessageBox.warning(self, "Aviso", "Selecione o Tipo de Cadastro!")
            return

        # ----- Limpeza dos campos com máscara (remove caracteres de formatação) -----
        # Observação: como as máscaras agora usam o blank padrão do Qt (espaço,
        # não mais "0" customizado — ver correção do bug de zeros finais cortados),
        # um campo não preenchido já resulta em string vazia após remover a pontuação
        # e os espaços de preenchimento, sem precisar comparar com "0000...".
        razao    = self.input_razao.text().strip()
        endereco = self.input_endereco.text().strip()
        email    = self.input_email.text().strip()
        rg       = self.input_rg.text().strip()

        cep = self.input_cep.text().replace("-", "").replace(" ", "").strip()

        cnpj = self.input_cnpj.text().replace(".", "").replace("/", "").replace("-", "").replace(" ", "").strip()

        cpf = self.input_cpf.text().replace(".", "").replace("-", "").replace(" ", "").strip()

        telefone = self.input_telefone.text().replace("(", "").replace(")", "").replace(" ", "").replace("-", "").strip()

        # ----- Validação do campo obrigatório -----
        if not razao:
            QMessageBox.warning(self, "Aviso", "A Razão Social/Nome é obrigatória!")
            return

        # ----- Lê o campo de Sexo -----
        sexo = ""
        for texto, rb in self.radios_sexo.items():
            if rb.isChecked():
                sexo = f"Outros: {self.input_outros_sexo.text().strip()}" if texto == "Outros" else texto
                break

        # ----- Resolve os combos com opção "Outros" -----
        val_forma_ecosol = f"Outros: {self.input_outros_forma_ecosol.text().strip()}" if self.input_forma_ecosol.currentText() == "Outros" else self.input_forma_ecosol.currentText()
        val_forma_emp    = f"Outros: {self.input_outros_forma_emp.text().strip()}"    if self.input_forma_emp.currentText()    == "Outros" else self.input_forma_emp.currentText()
        val_segmento     = f"Outros: {self.input_outros_segmento.text().strip()}"     if self.input_segmento.currentText()     == "Outros" else self.input_segmento.currentText()
        val_renda        = f"Outros: {self.input_outros_renda.text().strip()}"        if self.input_renda.currentText()        == "Outros" else self.input_renda.currentText()
        val_para_quem    = f"Outros: {self.input_outros_para_quem.text().strip()}"    if self.input_para_quem.currentText()    == "Outros" else self.input_para_quem.currentText()
        val_local        = f"Outros: {self.input_outros_local.text().strip()}"        if self.input_local.currentText()        == "Outros" else self.input_local.currentText()

        # ----- Converte beneficiários para inteiro (0 se vazio ou não numérico) -----
        b_dir_m = int(self.in_dir_m.text()) if self.in_dir_m.text().isdigit() else 0
        b_dir_f = int(self.in_dir_f.text()) if self.in_dir_f.text().isdigit() else 0
        b_ind_m = int(self.in_ind_m.text()) if self.in_ind_m.text().isdigit() else 0
        b_ind_f = int(self.in_ind_f.text()) if self.in_ind_f.text().isdigit() else 0

        # ----- Lê os grupos de checkboxes como strings CSV -----
        grid_class_social  = self.obter_texto_checkboxes(self.checks_classificacao)
        grid_motivos       = self.obter_texto_checkboxes(self.checks_motivo)
        grid_formas_comerc = self.obter_texto_checkboxes(self.checks_formas_comerc)

        # ----- VERIFICAÇÃO DE CAMPOS VAZIOS (opcionais, não bloqueiam o salvamento) -----
        # Como quase todos os campos são opcionais (só a Razão Social é obrigatória,
        # já validada acima), avisamos o operador sobre o que ficou em branco antes
        # de gravar, para que ele possa decidir se quer voltar e completar ou salvar
        # assim mesmo. Reaproveita os valores já lidos/normalizados acima.
        secoes_com_campos_vazios = self._verificar_campos_vazios(
            endereco=endereco, email=email, rg=rg, cep=cep, cnpj=cnpj, cpf=cpf,
            telefone=telefone, sexo=sexo, val_forma_ecosol=val_forma_ecosol,
            val_forma_emp=val_forma_emp, val_segmento=val_segmento, val_renda=val_renda,
            val_para_quem=val_para_quem, val_local=val_local, grid_class_social=grid_class_social,
            grid_motivos=grid_motivos, grid_formas_comerc=grid_formas_comerc,
        )

        if secoes_com_campos_vazios:
            if not self._exibir_popup_campos_vazios(secoes_com_campos_vazios):
                return  # Operador escolheu "Voltar": interrompe o salvamento aqui

        # ----- Metadados do registro -----
        cadastro_id   = str(uuid.uuid4())                          # ID único para o registro
        data_atual    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Data/hora do momento do salvamento
        data_form     = self.input_data_form.date().toString("yyyy-MM-dd")  # Data do formulário físico
        responsavel_id = self.usuario_logado_id if self.usuario_logado_id else None  # FK para a tabela usuarios

        # ----- Resolve o grupo_id (histórico de versões) -----
        # Se self.grupo_id_atual já estiver definido, significa que o operador
        # confirmou carregar um cadastro existente: este novo registro é uma
        # ATUALIZAÇÃO e deve herdar o mesmo grupo_id, mantendo o histórico.
        # Caso contrário, é um cadastro novo: o grupo_id nasce igual ao próprio
        # cadastro_id, tornando-se a primeira versão de sua própria história.
        grupo_id = self.grupo_id_atual if self.grupo_id_atual else cadastro_id

        try:
            conn   = sqlite3.connect('ecosol_local.db')
            cursor = conn.cursor()

            # SQL de inserção com todas as colunas do schema definido em db_config.py
            sql_insert = """
                INSERT INTO cadastros_ecosol (
                    id, tipo_cadastro, razao_social_nome, endereco, cep, email, 
                    cnpj, cpf, rg, representante_legal, cor_raca, sexo, telefone,
                    forma_organizacao_ecosol, forma_organizacao_emp, segmento_empreendimento, 
                    materia_prima, local_producao, onde_comercializa, 
                    beneficiarios_diretos_m, beneficiarios_diretos_f, beneficiarios_indiretos_m, beneficiarios_indiretos_f, 
                    maquina_cartao, pix, classificacao_social, motivo_criacao,
                    formas_comercializacao, produtos_comercializados, pagam_taxa, forma_contribuicao, 
                    renda_preponderante, para_quem_comercializa, dificuldade_comercializacao, responsavel_vendas, 
                    obs, local_cadastro, data_formulario, data_cadastro, responsavel_id, grupo_id, sincronizado
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0
                )
            """

            valores = (
                cadastro_id, tipo_cadastro, razao, endereco, cep, email,
                cnpj, cpf, rg, self.input_rep_legal.text(), self.input_cor_raca.text(), sexo, telefone,
                val_forma_ecosol, val_forma_emp, val_segmento,
                self.input_materia_prima.text(), self.input_local_prod.text(), self.input_onde_comerc.text(),
                b_dir_m, b_dir_f, b_ind_m, b_ind_f,
                self.input_cartao.currentText(), self.input_pix.currentText(), grid_class_social, grid_motivos,
                grid_formas_comerc, self.input_produtos.text(), self.input_pagam_taxa.currentText(), self.input_forma_contrib.currentText(),
                val_renda, val_para_quem, self.input_dificuldade.currentText(), self.input_resp_vendas.currentText(),
                self.input_obs.text(), val_local, data_form, data_atual, responsavel_id, grupo_id
            )

            cursor.execute(sql_insert, valores)

            # ----- Copia cada arquivo anexado para "uploads/" e registra no banco -----
            for arquivo_origem in self.arquivos_anexados:
                nome_arquivo    = os.path.basename(arquivo_origem)
                novo_nome       = f"{cadastro_id}_{nome_arquivo}"      # Prefixo com o ID do cadastro
                caminho_destino = os.path.join("uploads", novo_nome)
                shutil.copy(arquivo_origem, caminho_destino)           # Copia o arquivo para a pasta local

                arquivo_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO arquivos_anexos (id, cadastro_id, caminho_arquivo, sincronizado)
                    VALUES (?, ?, ?, 0)
                """, (arquivo_id, cadastro_id, caminho_destino))  # sincronizado=0: pendente para upload

            conn.commit()  # Confirma todas as operações no banco
            conn.close()

            # Mensagem diferenciada: deixa claro para o operador se foi um cadastro
            # novo ou uma atualização vinculada a um histórico já existente
            if self.grupo_id_atual:
                QMessageBox.information(self, "Sucesso", "Atualização cadastral registrada com sucesso!")
            else:
                QMessageBox.information(self, "Sucesso", "Cadastro coletado com sucesso no ambiente local!")

            self.limpar_formulario()  # Reseta todos os campos para um novo cadastro

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar no banco local: {str(e)}")

    # limpar_formulario
    # Reseta todos os widgets para o estado inicial após um cadastro bem-sucedido.
    def limpar_formulario(self):
        # Limpa os campos de texto simples
        self.input_razao.clear()
        self.input_endereco.clear()
        self.input_cpf.clear()
        self.input_cnpj.clear()
        self.input_cep.clear()
        self.input_email.clear()
        self.input_rg.clear()
        self.input_rep_legal.clear()
        self.input_cor_raca.clear()
        self.input_telefone.clear()
        self.input_materia_prima.clear()
        self.input_local_prod.clear()
        self.input_onde_comerc.clear()
        self.input_produtos.clear()
        self.input_obs.clear()
        self.in_dir_m.clear()
        self.in_dir_f.clear()
        self.in_ind_m.clear()
        self.in_ind_f.clear()

        # Limpa os campos "Outros" de todos os combos/radios
        self.input_outros_tipo.clear()
        self.input_outros_sexo.clear()
        self.input_outros_forma_ecosol.clear()
        self.input_outros_forma_emp.clear()
        self.input_outros_segmento.clear()
        self.input_outros_renda.clear()
        self.input_outros_para_quem.clear()
        self.input_outros_local.clear()

        # Desmarca todos os RadioButtons (desativa exclusividade temporariamente para permitir desmarcar todos)
        self.bg_tipo.setExclusive(False)
        for rb in self.radios_tipo.values():
            rb.setChecked(False)
        self.bg_tipo.setExclusive(True)  # Reativa exclusividade

        self.bg_sexo.setExclusive(False)
        for rb in self.radios_sexo.values():
            rb.setChecked(False)
        self.bg_sexo.setExclusive(True)

        # Desmarca todos os checkboxes e limpa seus campos "Outros"
        for cb in self.checks_classificacao + self.checks_motivo + self.checks_formas_comerc:
            cb.setChecked(False)
            campo_dinamico = cb.property("campo_outros")
            if campo_dinamico:
                campo_dinamico.clear()

        # Reseta todos os combos para exibir o placeholder (índice -1 = sem seleção)
        combos = [
            self.input_forma_ecosol, self.input_forma_emp, self.input_segmento, 
            self.input_cartao, self.input_pix, self.input_pagam_taxa, 
            self.input_forma_contrib, self.input_renda, self.input_para_quem, 
            self.input_dificuldade, self.input_resp_vendas, self.input_local
        ]
        for combo in combos:
            combo.setCurrentIndex(-1)  # Exibe o placeholder, sinalizando campo vazio

        # Restaura a data para hoje e limpa a lista de arquivos
        self.input_data_form.setDate(QDate.currentDate())
        self.arquivos_anexados.clear()
        self.lbl_arquivos.setText("Nenhum arquivo selecionado.")

        # Reseta o estado de atualização cadastral: o próximo cadastro preenchido
        # será tratado como um cadastro novo e independente, a menos que o
        # operador acione de novo a verificação de duplicidade por CPF/CNPJ
        self.grupo_id_atual = None