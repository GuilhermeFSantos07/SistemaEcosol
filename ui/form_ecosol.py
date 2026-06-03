import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                             QLineEdit, QPushButton, QScrollArea, QGroupBox, 
                             QRadioButton, QCheckBox, QFileDialog, QMessageBox, 
                             QComboBox, QButtonGroup, QDateEdit)
from PyQt6.QtCore import Qt, QDate

class NonScrollComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def wheelEvent(self, event):
        event.ignore()

class TelaNovoCadastro(QWidget):
    def __init__(self, controle_telas, usuario_logado_id=None):
        super().__init__()
        self.controle_telas = controle_telas
        self.usuario_logado_id = usuario_logado_id
        self.arquivos_anexados = []
        
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
            
        self.configurar_ui()

    def configurar_ui(self):
        # Layout raiz principal da tela
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(10, 10, 10, 10)

        # 1. Cabeçalho
        topo_layout = QHBoxLayout()
        titulo = QLabel("FORMULÁRIO DE CADASTRO ECOSOL")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #004b23; border-bottom: 2px solid #004b23; padding-bottom: 5px;")
        topo_layout.addWidget(titulo)
        layout_principal.addLayout(topo_layout)

        # 2. Área de Rolagem Principal
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        # Widget interno do painel central
        conteudo_scroll = QWidget()
        conteudo_scroll.setObjectName("ConteudoForm")
        conteudo_scroll.setMaximumWidth(1200) 
        
        # Estilização global CSS nativa do Qt (QSS)
        conteudo_scroll.setStyleSheet("""
            #ConteudoForm { background-color: #f8f9fa; }
            QLineEdit, QComboBox, QDateEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                background-color: white;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 1px solid #004b23;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 12px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 0 5px;
                color: #004b23;
            }
            QLabel {
                font-size: 13px;
                color: #333333;
            }
        """)
        
        layout_form = QVBoxLayout(conteudo_scroll)
        layout_form.setSpacing(15)

        # --- TIPO DE CADASTRO ---
        grupo_tipo = QGroupBox("Tipo de Cadastro")
        layout_tipo = QHBoxLayout()
        self.bg_tipo = QButtonGroup() 
        
        opcoes_tipo = ["Empreendimento solidário do Amazonas", "Empreendedor individual", "Autônomo", "Outros"]
        self.radios_tipo = {}
        for op in opcoes_tipo:
            rb = QRadioButton(op)
            self.bg_tipo.addButton(rb)
            layout_tipo.addWidget(rb)
            self.radios_tipo[op] = rb
            
        self.input_outros_tipo = QLineEdit()
        self.input_outros_tipo.setPlaceholderText("Qual?")
        self.input_outros_tipo.setEnabled(False)
        self.radios_tipo["Outros"].toggled.connect(self.input_outros_tipo.setEnabled)
        layout_tipo.addWidget(self.input_outros_tipo)
        
        grupo_tipo.setLayout(layout_tipo)
        layout_form.addWidget(grupo_tipo)

        # --- SEÇÃO 1: IDENTIFICAÇÃO ---
        grupo_identificacao = QGroupBox("1 - Identificação do Empreendimento / Representante")
        layout_id = QGridLayout()
        layout_id.setSpacing(10)
        
        layout_id.setColumnStretch(1, 1)
        layout_id.setColumnStretch(3, 1)

        self.input_razao = QLineEdit()
        self.input_razao.setPlaceholderText("Digite o nome da empresa ou empreendimento")
        self.input_endereco = QLineEdit()
        self.input_endereco.setPlaceholderText("Digite o endereço completo")
        self.input_cep = QLineEdit()
        self.input_cep.setInputMask("00000-000;0") 
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Ex: contato@empreendimento.com")
        self.input_cnpj = QLineEdit()
        self.input_cnpj.setInputMask("00.000.000/0000-00;0") 
        self.input_cpf = QLineEdit()
        self.input_cpf.setInputMask("000.000.000-00;0") 
        self.input_rg = QLineEdit()
        self.input_rg.setPlaceholderText("Digite o RG")
        self.input_rep_legal = QLineEdit()
        self.input_rep_legal.setPlaceholderText("Digite o nome do representante legal")
        self.input_cor_raca = QLineEdit()
        self.input_cor_raca.setPlaceholderText("Digite a cor/raça")

        # Configuração do painel de Sexo (Removido o fundo cinza indesejado)
        self.bg_sexo = QButtonGroup()
        widget_sexo = QWidget()
        widget_sexo.setStyleSheet("background: transparent;") # Torna o contêiner 100% invisível
        layout_sexo = QHBoxLayout(widget_sexo)
        layout_sexo.setContentsMargins(0, 0, 0, 0)
        layout_sexo.setSpacing(12)

        opcoes_sexo = ["Masculino", "Feminino", "Prefiro não informar", "Outros"]
        self.radios_sexo = {}
        for op in opcoes_sexo:
            rb = QRadioButton(op)
            self.bg_sexo.addButton(rb)
            layout_sexo.addWidget(rb)
            self.radios_sexo[op] = rb

        self.input_outros_sexo = QLineEdit()
        self.input_outros_sexo.setPlaceholderText("Especificar...")
        self.input_outros_sexo.setEnabled(False)
        self.radios_sexo["Outros"].toggled.connect(self.input_outros_sexo.setEnabled)
        layout_sexo.addWidget(self.input_outros_sexo)
        layout_sexo.addStretch()

        self.input_telefone = QLineEdit()
        self.input_telefone.setInputMask("(00) 00000-0000;0") 

        # Posicionamento em Grid 50/50
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
        layout_id.addWidget(widget_sexo, 5, 1, 1, 3)

        grupo_identificacao.setLayout(layout_id)
        layout_form.addWidget(grupo_identificacao)

        # --- SEÇÃO 2: CARACTERÍSTICAS GERAIS ---
        grupo_caracteristicas = QGroupBox("2 - Características gerais do empreendimento")
        layout_caract = QGridLayout()
        layout_caract.setSpacing(10)
        
        layout_caract.setColumnStretch(1, 1)
        layout_caract.setColumnStretch(3, 1)
        
        # Combo Boxes atualizados com Legendas Nativas (Placeholders)
        self.input_forma_ecosol = NonScrollComboBox()
        self.input_forma_ecosol.addItems(["Cooperativa", "Associação", "Grupo Informal", "Outros"])
        self.input_forma_ecosol.setPlaceholderText("Selecione a Forma Org. ECOSOL...")
        self.input_forma_ecosol.setCurrentIndex(-1)
        self.input_outros_forma_ecosol = QLineEdit()
        self.input_outros_forma_ecosol.setPlaceholderText("Especificar...")
        self.input_outros_forma_ecosol.setEnabled(False)
        self.input_forma_ecosol.currentTextChanged.connect(lambda t: self.input_outros_forma_ecosol.setEnabled(t == "Outros"))
        lay_forma_ecosol = QHBoxLayout()
        lay_forma_ecosol.addWidget(self.input_forma_ecosol, 2)
        lay_forma_ecosol.addWidget(self.input_outros_forma_ecosol, 1)
        
        self.input_forma_emp = NonScrollComboBox()
        self.input_forma_emp.addItems(["MEI", "Autônomo", "Outros"])
        self.input_forma_emp.setPlaceholderText("Selecione a Forma Org. Emp...")
        self.input_forma_emp.setCurrentIndex(-1)
        self.input_outros_forma_emp = QLineEdit()
        self.input_outros_forma_emp.setPlaceholderText("Especificar...")
        self.input_outros_forma_emp.setEnabled(False)
        self.input_forma_emp.currentTextChanged.connect(lambda t: self.input_outros_forma_emp.setEnabled(t == "Outros"))
        lay_forma_emp = QHBoxLayout()
        lay_forma_emp.addWidget(self.input_forma_emp, 2)
        lay_forma_emp.addWidget(self.input_outros_forma_emp, 1)
        
        self.input_segmento = NonScrollComboBox()
        self.input_segmento.addItems(["Comércio", "Serviços", "Artesanato", "Indústria", "Outros"])
        self.input_segmento.setPlaceholderText("Selecione o Segmento...")
        self.input_segmento.setCurrentIndex(-1)
        self.input_outros_segmento = QLineEdit()
        self.input_outros_segmento.setPlaceholderText("Especificar...")
        self.input_outros_segmento.setEnabled(False)
        self.input_segmento.currentTextChanged.connect(lambda t: self.input_outros_segmento.setEnabled(t == "Outros"))
        lay_segmento = QHBoxLayout()
        lay_segmento.addWidget(self.input_segmento, 2)
        lay_segmento.addWidget(self.input_outros_segmento, 1)
        
        self.input_materia_prima = QLineEdit()
        self.input_materia_prima.setPlaceholderText("Digite as matérias-primas")
        self.input_local_prod = QLineEdit()
        self.input_local_prod.setPlaceholderText("Digite o local de produção")
        self.input_onde_comerc = QLineEdit()
        self.input_onde_comerc.setPlaceholderText("Onde comercializa?")
        
        layout_benef = QHBoxLayout()
        self.in_dir_m = QLineEdit(); self.in_dir_m.setPlaceholderText("Diretos Masculino")
        self.in_dir_f = QLineEdit(); self.in_dir_f.setPlaceholderText("Diretos Feminino")
        self.in_ind_m = QLineEdit(); self.in_ind_m.setPlaceholderText("Indiretos Masculino")
        self.in_ind_f = QLineEdit(); self.in_ind_f.setPlaceholderText("Indiretos Feminino")
        layout_benef.addWidget(self.in_dir_m); layout_benef.addWidget(self.in_dir_f)
        layout_benef.addWidget(self.in_ind_m); layout_benef.addWidget(self.in_ind_f)
        
        self.input_cartao = NonScrollComboBox(); self.input_cartao.addItems(["Sim", "Não"])
        self.input_cartao.setPlaceholderText("Selecione...")
        self.input_cartao.setCurrentIndex(-1)
        
        self.input_pix = NonScrollComboBox(); self.input_pix.addItems(["Sim", "Não"])
        self.input_pix.setPlaceholderText("Selecione...")
        self.input_pix.setCurrentIndex(-1)

        layout_caract.addWidget(QLabel("1 - Forma Org. ECOSOL:"), 0, 0)
        layout_caract.addLayout(lay_forma_ecosol, 0, 1)
        layout_caract.addWidget(QLabel("1.1 - Forma Org. Emp.:"), 0, 2)
        layout_caract.addLayout(lay_forma_emp, 0, 3)

        layout_caract.addWidget(QLabel("2 - Segmento:"), 1, 0)
        layout_caract.addLayout(lay_segmento, 1, 1)
        layout_caract.addWidget(QLabel("3 - Matéria-prima:"), 1, 2)
        layout_caract.addWidget(self.input_materia_prima, 1, 3)

        layout_caract.addWidget(QLabel("4 - Local Production:"), 2, 0)
        layout_caract.addWidget(self.input_local_prod, 2, 1)
        layout_caract.addWidget(QLabel("5 - Onde Comercializa:"), 2, 2)
        layout_caract.addWidget(self.input_onde_comerc, 2, 3)

        layout_caract.addWidget(QLabel("6 - Beneficiários:"), 3, 0)
        layout_caract.addLayout(layout_benef, 3, 1, 1, 3)

        layout_caract.addWidget(QLabel("7 - Máquina Cartão?:"), 4, 0)
        layout_caract.addWidget(self.input_cartao, 4, 1)
        layout_caract.addWidget(QLabel("7.1 - PIX?:"), 4, 2)
        layout_caract.addWidget(self.input_pix, 4, 3)

        # Grades de Checkbox limpas e sem fundos cinzas
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

        # --- SEÇÃO 3: ATIVIDADE ECONÔMICA ---
        grupo_atividade = QGroupBox("3 - Atividade econômica e situação de trabalho")
        layout_ativ = QGridLayout()
        layout_ativ.setSpacing(10)
        
        layout_ativ.setColumnStretch(1, 1)
        layout_ativ.setColumnStretch(3, 1)

        self.checks_formas_comerc = self.criar_grupo_checkboxes([
            "Lojas/espaços fixos", "Feiras", "Central de comercialização", "Comércio Eletrônico"
        ], layout_ativ, "1 - Formas de Comercialização:", 0)

        self.input_produtos = QLineEdit()
        self.input_produtos.setPlaceholderText("Digite os produtos comercializados")
        
        self.input_pagam_taxa = NonScrollComboBox(); self.input_pagam_taxa.addItems(["Sim", "Não"])
        self.input_pagam_taxa.setPlaceholderText("Selecione...")
        self.input_pagam_taxa.setCurrentIndex(-1)
        
        self.input_forma_contrib = NonScrollComboBox(); self.input_forma_contrib.addItems(["Taxa fixa", "Percentual", "Espontânea", "Caixa comum", "Não se aplica"])
        self.input_forma_contrib.setPlaceholderText("Selecione a Forma...")
        self.input_forma_contrib.setCurrentIndex(-1)
        
        self.input_renda = NonScrollComboBox()
        self.input_renda.addItems(["Renda individual/familiar", "Complemento atividades", "Complemento governamental", "Aposentadoria", "Outros"])
        self.input_renda.setPlaceholderText("Selecione a Renda...")
        self.input_renda.setCurrentIndex(-1)
        self.input_outros_renda = QLineEdit()
        self.input_outros_renda.setPlaceholderText("Especificar...")
        self.input_outros_renda.setEnabled(False)
        self.input_renda.currentTextChanged.connect(lambda t: self.input_outros_renda.setEnabled(t == "Outros"))
        lay_renda = QHBoxLayout()
        lay_renda.addWidget(self.input_renda, 2)
        lay_renda.addWidget(self.input_outros_renda, 1)

        self.input_para_quem = NonScrollComboBox()
        self.input_para_quem.addItems(["Consumidor final", "Atacadistas", "Governo", "Empresas privadas", "Outros"])
        self.input_para_quem.setPlaceholderText("Selecione o Destino...")
        self.input_para_quem.setCurrentIndex(-1)
        self.input_outros_para_quem = QLineEdit()
        self.input_outros_para_quem.setPlaceholderText("Especificar...")
        self.input_outros_para_quem.setEnabled(False)
        self.input_para_quem.currentTextChanged.connect(lambda t: self.input_outros_para_quem.setEnabled(t == "Outros"))
        lay_para_quem = QHBoxLayout()
        lay_para_quem.addWidget(self.input_para_quem, 2)
        lay_para_quem.addWidget(self.input_outros_para_quem, 1)

        self.input_dificuldade = NonScrollComboBox(); self.input_dificuldade.addItems(["Sim", "Não"])
        self.input_dificuldade.setPlaceholderText("Selecione...")
        self.input_dificuldade.setCurrentIndex(-1)
        
        self.input_resp_vendas = NonScrollComboBox(); self.input_resp_vendas.addItems(["Cada um vende o seu", "Rodízio", "Sócios designados", "Pessoas não sócias", "Não se aplica"])
        self.input_resp_vendas.setPlaceholderText("Selecione o Responsável...")
        self.input_resp_vendas.setCurrentIndex(-1)

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

        # --- SEÇÃO FINAL: OBS, LOCAL, DATA E UPLOADS ---
        grupo_final = QGroupBox("Finalização e Anexos")
        layout_final = QGridLayout()
        layout_final.setSpacing(10)
        
        layout_final.setColumnStretch(1, 1)
        layout_final.setColumnStretch(3, 1)
        
        self.input_obs = QLineEdit()
        self.input_obs.setPlaceholderText("Digite observações adicionais")
        
        self.input_local = NonScrollComboBox()
        self.input_local.addItems(["Manaus", "Itacoatiara", "Parintins", "Tefé", "Outros"]) 
        self.input_local.setPlaceholderText("Selecione o Local...")
        self.input_local.setCurrentIndex(-1)
        self.input_outros_local = QLineEdit()
        self.input_outros_local.setPlaceholderText("Especificar Local...")
        self.input_outros_local.setEnabled(False)
        self.input_local.currentTextChanged.connect(lambda t: self.input_outros_local.setEnabled(t == "Outros"))
        lay_local = QHBoxLayout()
        lay_local.addWidget(self.input_local, 2)
        lay_local.addWidget(self.input_outros_local, 1)

        self.input_data_form = QDateEdit()
        self.input_data_form.setCalendarPopup(True) 
        self.input_data_form.setDate(QDate.currentDate()) 
        self.input_data_form.setDisplayFormat("dd/MM/yyyy") 
        self.input_data_form.setStyleSheet("QDateEdit { min-width: 160px; padding: 5px; }")
        
        self.btn_anexar = QPushButton("Anexar RG, CPF e Comprovante")
        self.btn_anexar.setStyleSheet("""
            QPushButton { 
                background-color: #007bff; color: white; border-radius: 4px; 
                padding: 6px 12px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        self.btn_anexar.clicked.connect(self.selecionar_arquivos)
        self.lbl_arquivos = QLabel("Nenhum arquivo selecionado.")
        self.lbl_arquivos.setStyleSheet("color: #666; font-style: italic;")
        
        layout_upload = QHBoxLayout()
        layout_upload.addWidget(self.btn_anexar)
        layout_upload.addWidget(self.lbl_arquivos)
        layout_upload.addStretch()

        layout_final.addWidget(QLabel("OBS:"), 0, 0)
        layout_final.addWidget(self.input_obs, 0, 1, 1, 3)

        layout_final.addWidget(QLabel("Local:"), 1, 0)
        layout_final.addLayout(lay_local, 1, 1)
        layout_final.addWidget(QLabel("Data do Formulário:"), 1, 2)
        layout_final.addWidget(self.input_data_form, 1, 3)

        layout_final.addWidget(QLabel("Arquivos:"), 2, 0)
        layout_final.addLayout(layout_upload, 2, 1, 1, 3)
        
        grupo_final.setLayout(layout_final)
        layout_form.addWidget(grupo_final)

        # ================= SEÇÃO DE BOTÕES =================
        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(20)
        layout_botoes.setContentsMargins(0, 15, 0, 5)
        layout_botoes.addStretch() 

        self.btn_salvar = QPushButton("💾 Salvar Cadastro Local")
        self.btn_salvar.setStyleSheet("""
            QPushButton { background-color: #28a745; color: white; padding: 10px 22px; font-size: 14px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #218838; }
        """)
        self.btn_salvar.setFixedWidth(240) 
        self.btn_salvar.clicked.connect(self.salvar_cadastro)
        layout_botoes.addWidget(self.btn_salvar)

        self.btn_pdf = QPushButton("📄 Gerar PDF")
        self.btn_pdf.setStyleSheet("""
            QPushButton { background-color: #dc3545; color: white; padding: 10px 22px; font-size: 14px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #c82333; }
        """)
        self.btn_pdf.setFixedWidth(240) 
        self.btn_pdf.clicked.connect(self.gerar_pdf)
        layout_botoes.addWidget(self.btn_pdf)

        layout_botoes.addStretch() 
        layout_form.addLayout(layout_botoes)

        layout_form.addStretch()
        scroll.setWidget(conteudo_scroll)
        layout_principal.addWidget(scroll)

    def criar_grupo_checkboxes(self, opcoes, grid_layout, label_texto, row):
        label = QLabel(label_texto)
        label.setStyleSheet("font-weight: bold; color: #333;")
        grid_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        widget_cb = QWidget()
        widget_cb.setStyleSheet("background: transparent;") # Remove fundo cinza das caixas de escolha
        layout_cb = QGridLayout(widget_cb)
        layout_cb.setContentsMargins(0, 0, 0, 0)
        layout_cb.setSpacing(8)
        
        lista_cb = []
        colunas_max = 4  
        col = 0
        r = 0
        
        for op in opcoes:
            cb = QCheckBox(op)
            lista_cb.append(cb)
            
            if op == "Outros":
                sub_widget = QWidget()
                sub_widget.setStyleSheet("background: transparent;")
                sub_layout = QHBoxLayout(sub_widget)
                sub_layout.setContentsMargins(0, 0, 0, 0)
                sub_layout.setSpacing(5)
                sub_layout.addWidget(cb)
                
                input_outros = QLineEdit()
                input_outros.setPlaceholderText("Qual?")
                input_outros.setEnabled(False)
                cb.toggled.connect(input_outros.setEnabled)
                sub_layout.addWidget(input_outros)
                
                cb.setProperty("campo_outros", input_outros)
                layout_cb.addWidget(sub_widget, r, col)
            else:
                layout_cb.addWidget(cb, r, col)
                
            col += 1
            if col >= colunas_max:
                col = 0
                r += 1
                
        grid_layout.addWidget(widget_cb, row, 1, 1, 3)
        return lista_cb

    def obter_texto_checkboxes(self, lista_checkboxes):
        selecionados = []
        for cb in lista_checkboxes:
            if cb.isChecked():
                texto = cb.text()
                if texto == "Outros":
                    campo = cb.property("campo_outros")
                    if campo and campo.text().strip():
                        texto = f"Outros: {campo.text().strip()}"
                selecionados.append(texto)
        return ", ".join(selecionados)

    def selecionar_arquivos(self):
        arquivos, _ = QFileDialog.getOpenFileNames(self, "Selecione os Documentos", "", "Imagens/PDFs (*.pdf *.png *.jpg *.jpeg)")
        if arquivos:
            self.arquivos_anexados.extend(arquivos)
            self.lbl_arquivos.setText(f"{len(self.arquivos_anexados)} arquivo(s) selecionado(s).")

    def gerar_pdf(self):
        razao = self.input_razao.text().strip()
        if not razao:
            QMessageBox.warning(self, "Aviso", "Preencha ao menos a Razão Social para gerar o PDF!")
            return
        QMessageBox.information(self, "PDF", f"Documento PDF de coleta criado para:\n{razao}")

    def salvar_cadastro(self):
        tipo_cadastro = ""
        for texto, rb in self.radios_tipo.items():
            if rb.isChecked():
                tipo_cadastro = f"Outros: {self.input_outros_tipo.text()}" if texto == "Outros" else texto
                break

        if not tipo_cadastro:
            QMessageBox.warning(self, "Aviso", "Selecione o Tipo de Cadastro!")
            return

        razao = self.input_razao.text().strip()
        endereco = self.input_endereco.text().strip()
        email = self.input_email.text().strip()
        rg = self.input_rg.text().strip()

        cep = self.input_cep.text().replace("-", "")
        if cep == "00000000": cep = ""

        cnpj = self.input_cnpj.text().replace(".", "").replace("/", "").replace("-", "")
        if cnpj == "00000000000000": cnpj = ""

        cpf = self.input_cpf.text().replace(".", "").replace("-", "")
        if cpf == "00000000000": cpf = ""

        telefone = self.input_telefone.text().replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
        if telefone == "00000000000": telefone = ""

        if not razao:
            QMessageBox.warning(self, "Aviso", "A Razão Social/Nome é obrigatória!")
            return

        sexo = ""
        for texto, rb in self.radios_sexo.items():
            if rb.isChecked():
                sexo = f"Outros: {self.input_outros_sexo.text().strip()}" if texto == "Outros" else texto
                break

        val_forma_ecosol = f"Outros: {self.input_outros_forma_ecosol.text().strip()}" if self.input_forma_ecosol.currentText() == "Outros" else self.input_forma_ecosol.currentText()
        val_forma_emp = f"Outros: {self.input_outros_forma_emp.text().strip()}" if self.input_forma_emp.currentText() == "Outros" else self.input_forma_emp.currentText()
        val_segmento = f"Outros: {self.input_outros_segmento.text().strip()}" if self.input_segmento.currentText() == "Outros" else self.input_segmento.currentText()
        val_renda = f"Outros: {self.input_outros_renda.text().strip()}" if self.input_renda.currentText() == "Outros" else self.input_renda.currentText()
        val_para_quem = f"Outros: {self.input_outros_para_quem.text().strip()}" if self.input_para_quem.currentText() == "Outros" else self.input_para_quem.currentText()
        val_local = f"Outros: {self.input_outros_local.text().strip()}" if self.input_local.currentText() == "Outros" else self.input_local.currentText()

        b_dir_m = int(self.in_dir_m.text()) if self.in_dir_m.text().isdigit() else 0
        b_dir_f = int(self.in_dir_f.text()) if self.in_dir_f.text().isdigit() else 0
        b_ind_m = int(self.in_ind_m.text()) if self.in_ind_m.text().isdigit() else 0
        b_ind_f = int(self.in_ind_f.text()) if self.in_ind_f.text().isdigit() else 0

        grid_class_social = self.obter_texto_checkboxes(self.checks_classificacao)
        grid_motivos = self.obter_texto_checkboxes(self.checks_motivo)
        grid_formas_comerc = self.obter_texto_checkboxes(self.checks_formas_comerc)

        cadastro_id = str(uuid.uuid4())
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        data_form = self.input_data_form.date().toString("yyyy-MM-dd") 
        responsavel_id = self.usuario_logado_id if self.usuario_logado_id else None 

        try:
            conn = sqlite3.connect('ecosol_local.db')
            cursor = conn.cursor()

            sql_insert = """
                INSERT INTO cadastros_ecosol (
                    id, tipo_cadastro, razao_social_nome, endereco, cep, email, 
                    cnpj, cpf, rg, representante_legal, cor_raca, sexo, telefone,
                    forma_organizacao_ecosol, forma_organizacao_emp, segmento_empreendimento, 
                    materia_prima, local_producao, onde_comercializa, 
                    beneficiarios_diretos_m, beneficiarios_diretos_f, beneficiarios_indiretos_m, beneficiarios_indiretos_f, 
                    maquina_cartao, pix, classificacao_social, motivo_criacao,
                    formas_comercializacao, produtos_comercializados, pagam_taxa, forma_contribuicao, 
                    renda_preponderante, para_quem_comercializa, difficulty_comercializacao, responsavel_vendas, 
                    obs, local_cadastro, data_formulario, data_cadastro, responsavel_id, sincronizado
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0
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
                self.input_obs.text(), val_local, data_form, data_atual, responsavel_id
            )

            cursor.execute(sql_insert, valores)

            for arquivo_origem in self.arquivos_anexados:
                nome_arquivo = os.path.basename(arquivo_origem)
                novo_nome = f"{cadastro_id}_{nome_arquivo}"
                caminho_destino = os.path.join("uploads", novo_nome)
                shutil.copy(arquivo_origem, caminho_destino)
                arquivo_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO arquivos_anexos (id, cadastro_id, caminho_arquivo, sincronizado)
                    VALUES (?, ?, ?, 0)
                """, (arquivo_id, cadastro_id, caminho_destino))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Sucesso", "Cadastro coletado com sucesso no ambiente local!")
            self.limpar_formulario()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar no banco local: {str(e)}")

    def limpar_formulario(self):
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

        self.input_outros_tipo.clear()
        self.input_outros_sexo.clear() 
        self.input_outros_forma_ecosol.clear()
        self.input_outros_forma_emp.clear()
        self.input_outros_segmento.clear()
        self.input_outros_renda.clear()
        self.input_outros_para_quem.clear()
        self.input_outros_local.clear()
        
        self.bg_tipo.setExclusive(False)
        for rb in self.radios_tipo.values():
            rb.setChecked(False)
        self.bg_tipo.setExclusive(True)

        self.bg_sexo.setExclusive(False)
        for rb in self.radios_sexo.values():
            rb.setChecked(False)
        self.bg_sexo.setExclusive(True)
        
        for cb in self.checks_classificacao + self.checks_motivo + self.checks_formas_comerc:
            cb.setChecked(False)
            campo_dinamico = cb.property("campo_outros")
            if campo_dinamico:
                campo_dinamico.clear()
            
        combos = [self.input_forma_ecosol, self.input_forma_emp, self.input_segmento, 
                  self.input_cartao, self.input_pix, self.input_pagam_taxa, 
                  self.input_forma_contrib, self.input_renda, self.input_para_quem, 
                  self.input_dificuldade, self.input_resp_vendas, self.input_local]
        for combo in combos:
            combo.setCurrentIndex(-1) # Restaura para o estado vazio exibindo o placeholder guia
            
        self.input_data_form.setDate(QDate.currentDate()) 
        self.arquivos_anexados.clear()
        self.lbl_arquivos.setText("Nenhum arquivo selecionado.")