import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QScrollArea, QGroupBox, 
                             QRadioButton, QCheckBox, QFormLayout, QFileDialog, 
                             QMessageBox, QComboBox, QButtonGroup, QDateEdit)
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
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        # 1. Cabeçalho
        topo_layout = QHBoxLayout()
        titulo = QLabel("FORMULÁRIO DE CADASTRO ECOSOL")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #004b23; border-bottom: 2px solid #004b23; padding-bottom: 5px;")
        topo_layout.addWidget(titulo)
        layout_principal.addLayout(topo_layout)

        # 2. Área com Barra de Rolagem
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        conteudo_scroll = QWidget()
        conteudo_scroll.setObjectName("ConteudoForm")
        conteudo_scroll.setStyleSheet("#ConteudoForm { background-color: #f8f9fa; }") 
        layout_form = QVBoxLayout(conteudo_scroll)

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
        layout_id = QFormLayout()

        self.input_razao = QLineEdit()
        self.input_endereco = QLineEdit()
        self.input_cep = QLineEdit()
        self.input_cep.setInputMask("00000-000;0") 
        self.input_email = QLineEdit()
        self.input_cnpj = QLineEdit()
        self.input_cnpj.setInputMask("00.000.000/0000-00;0") 
        self.input_cpf = QLineEdit()
        self.input_cpf.setInputMask("000.000.000-00;0") 
        self.input_rg = QLineEdit()
        self.input_rep_legal = QLineEdit()
        self.input_cor_raca = QLineEdit()

        # --- CAMPO SEXO (RadioButtons em linha) ---
        self.bg_sexo = QButtonGroup()
        widget_sexo = QWidget()
        layout_sexo = QHBoxLayout(widget_sexo)
        layout_sexo.setContentsMargins(0, 0, 0, 0)
        layout_sexo.setSpacing(15)

        opcoes_sexo = ["Masculino", "Feminino", "Outros", "Prefiro não informar"]
        self.radios_sexo = {}
        for op in opcoes_sexo:
            rb = QRadioButton(op)
            self.bg_sexo.addButton(rb)
            layout_sexo.addWidget(rb)
            self.radios_sexo[op] = rb

        layout_sexo.addStretch()

        self.input_telefone = QLineEdit()
        self.input_telefone.setInputMask("(00) 00000-0000;0") 

        layout_id.addRow("Razão Social / Nome Fantasia:", self.input_razao)
        layout_id.addRow("Endereço:", self.input_endereco)
        layout_id.addRow("CEP:", self.input_cep)
        layout_id.addRow("E-mail / Internet:", self.input_email)
        layout_id.addRow("CNPJ:", self.input_cnpj)
        layout_id.addRow("CPF:", self.input_cpf)
        layout_id.addRow("RG:", self.input_rg)
        layout_id.addRow("Representante Legal:", self.input_rep_legal)
        layout_id.addRow("Cor/Raça:", self.input_cor_raca)
        layout_id.addRow("Sexo:", widget_sexo)
        layout_id.addRow("Telefone:", self.input_telefone)
        grupo_identificacao.setLayout(layout_id)
        layout_form.addWidget(grupo_identificacao)

        # --- SEÇÃO 2: CARACTERÍSTICAS GERAIS ---
        grupo_caracteristicas = QGroupBox("2 - Características gerais do empreendimento")
        layout_caract = QFormLayout()
        
        self.input_forma_ecosol = NonScrollComboBox()
        self.input_forma_ecosol.addItems(["", "Cooperativa", "Associação", "Grupo Informal", "Outros"])
        self.input_outros_forma_ecosol = QLineEdit()
        self.input_outros_forma_ecosol.setPlaceholderText("Especificar Outros...")
        self.input_outros_forma_ecosol.setEnabled(False)
        self.input_forma_ecosol.currentTextChanged.connect(lambda t: self.input_outros_forma_ecosol.setEnabled(t == "Outros"))
        lay_forma_ecosol = QHBoxLayout()
        lay_forma_ecosol.addWidget(self.input_forma_ecosol, 2)
        lay_forma_ecosol.addWidget(self.input_outros_forma_ecosol, 1)
        
        self.input_forma_emp = NonScrollComboBox()
        self.input_forma_emp.addItems(["", "MEI", "Autônomo", "Outros"])
        self.input_outros_forma_emp = QLineEdit()
        self.input_outros_forma_emp.setPlaceholderText("Especificar Outros...")
        self.input_outros_forma_emp.setEnabled(False)
        self.input_forma_emp.currentTextChanged.connect(lambda t: self.input_outros_forma_emp.setEnabled(t == "Outros"))
        lay_forma_emp = QHBoxLayout()
        lay_forma_emp.addWidget(self.input_forma_emp, 2)
        lay_forma_emp.addWidget(self.input_outros_forma_emp, 1)
        
        self.input_segmento = NonScrollComboBox()
        self.input_segmento.addItems(["", "Comércio", "Serviços", "Artesanato", "Indústria", "Outros"])
        self.input_outros_segmento = QLineEdit()
        self.input_outros_segmento.setPlaceholderText("Especificar Outros...")
        self.input_outros_segmento.setEnabled(False)
        self.input_segmento.currentTextChanged.connect(lambda t: self.input_outros_segmento.setEnabled(t == "Outros"))
        lay_segmento = QHBoxLayout()
        lay_segmento.addWidget(self.input_segmento, 2)
        lay_segmento.addWidget(self.input_outros_segmento, 1)
        
        self.input_materia_prima = QLineEdit()
        self.input_local_prod = QLineEdit()
        self.input_onde_comerc = QLineEdit()
        
        layout_benef = QHBoxLayout()
        self.in_dir_m = QLineEdit(); self.in_dir_m.setPlaceholderText("Dir. M")
        self.in_dir_f = QLineEdit(); self.in_dir_f.setPlaceholderText("Dir. F")
        self.in_ind_m = QLineEdit(); self.in_ind_m.setPlaceholderText("Ind. M")
        self.in_ind_f = QLineEdit(); self.in_ind_f.setPlaceholderText("Ind. F")
        layout_benef.addWidget(self.in_dir_m); layout_benef.addWidget(self.in_dir_f)
        layout_benef.addWidget(self.in_ind_m); layout_benef.addWidget(self.in_ind_f)
        
        self.input_cartao = NonScrollComboBox(); self.input_cartao.addItems(["", "Sim", "Não"])
        self.input_pix = NonScrollComboBox(); self.input_pix.addItems(["", "Sim", "Não"])

        layout_caract.addRow("1 - Forma Org. ECOSOL:", lay_forma_ecosol)
        layout_caract.addRow("1.1 - Forma Org. Emp.:", lay_forma_emp)
        layout_caract.addRow("2 - Segmento:", lay_segmento)
        layout_caract.addRow("3 - Matéria-prima:", self.input_materia_prima)
        layout_caract.addRow("4 - Local Produção:", self.input_local_prod)
        layout_caract.addRow("5 - Onde Comercializa:", self.input_onde_comerc)
        layout_caract.addRow("6 - Beneficiários:", layout_benef)
        layout_caract.addRow("7 - Máquina Cartão?:", self.input_cartao)
        layout_caract.addRow("7.1 - PIX?:", self.input_pix)

        self.checks_classificacao = self.criar_grupo_checkboxes([
            "Agricultura Familiar", "Artistas", "Catadores", "Técnicos", 
            "Autônomos", "Artesãos", "Assentados", "Garimpeiros", "Desempregados", "Outros"
        ], layout_caract, "8 - Classificação Social:")
        
        self.checks_motivo = self.criar_grupo_checkboxes([
            "Alternativa ao desemprego", "Produtos orgânicos", "Renda", 
            "Motivação social", "Qualificação", "Todos são donos", "Grupos étnicos", "Outros"
        ], layout_caract, "9 - Motivo Criação:")

        grupo_caracteristicas.setLayout(layout_caract)
        layout_form.addWidget(grupo_caracteristicas)

        # --- SEÇÃO 3: ATIVIDADE ECONÔMICA ---
        grupo_atividade = QGroupBox("3 - Atividade econômica e situação de trabalho")
        layout_ativ = QFormLayout()

        self.checks_formas_comerc = self.criar_grupo_checkboxes([
            "Lojas/espaços fixos", "Feiras", "Central de comercialização", "Comércio Eletrônico"
        ], layout_ativ, "1 - Formas de Comercialização:")

        self.input_produtos = QLineEdit()
        self.input_pagam_taxa = NonScrollComboBox(); self.input_pagam_taxa.addItems(["", "Sim", "Não"])
        self.input_forma_contrib = NonScrollComboBox(); self.input_forma_contrib.addItems(["", "Taxa fixa", "Percentual", "Espontânea", "Caixa comum", "Não se aplica"])
        
        self.input_renda = NonScrollComboBox()
        self.input_renda.addItems(["", "Renda individual/familiar", "Complemento atividades", "Complemento governamental", "Aposentadoria", "Outros"])
        self.input_outros_renda = QLineEdit()
        self.input_outros_renda.setPlaceholderText("Especificar Outros...")
        self.input_outros_renda.setEnabled(False)
        self.input_renda.currentTextChanged.connect(lambda t: self.input_outros_renda.setEnabled(t == "Outros"))
        lay_renda = QHBoxLayout()
        lay_renda.addWidget(self.input_renda, 2)
        lay_renda.addWidget(self.input_outros_renda, 1)

        self.input_para_quem = NonScrollComboBox()
        self.input_para_quem.addItems(["", "Consumidor final", "Atacadistas", "Governo", "Empresas privadas", "Outros empreendimentos", "Outros"])
        self.input_outros_para_quem = QLineEdit()
        self.input_outros_para_quem.setPlaceholderText("Especificar Outros...")
        self.input_outros_para_quem.setEnabled(False)
        self.input_para_quem.currentTextChanged.connect(lambda t: self.input_outros_para_quem.setEnabled(t == "Outros"))
        lay_para_quem = QHBoxLayout()
        lay_para_quem.addWidget(self.input_para_quem, 2)
        lay_para_quem.addWidget(self.input_outros_para_quem, 1)

        self.input_dificuldade = NonScrollComboBox(); self.input_dificuldade.addItems(["", "Sim", "Não"])
        self.input_resp_vendas = NonScrollComboBox(); self.input_resp_vendas.addItems(["", "Cada um vende o seu", "Rodízio", "Sócios designados", "Pessoas não sócias", "Não se aplica"])

        layout_ativ.addRow("2 - Produtos que comercializa:", self.input_produtos)
        layout_ativ.addRow("3 - Pagam taxa/contribuição?", self.input_pagam_taxa)
        layout_ativ.addRow("4 - Forma de contribuição:", self.input_forma_contrib)
        layout_ativ.addRow("5 - Renda preponderante:", lay_renda)
        layout_ativ.addRow("6 - Para quem comercializa?", lay_para_quem)
        layout_ativ.addRow("7 - Encontra dificuldade?", self.input_dificuldade)
        layout_ativ.addRow("8 - Responsável vendas:", self.input_resp_vendas)

        grupo_atividade.setLayout(layout_ativ)
        layout_form.addWidget(grupo_atividade)

        # --- SEÇÃO FINAL: OBS, LOCAL, DATA E UPLOADS ---
        grupo_final = QGroupBox("Finalização e Anexos")
        layout_final = QFormLayout()
        
        self.input_obs = QLineEdit()
        
        self.input_local = NonScrollComboBox()
        self.input_local.addItems(["Manaus", "Itacoatiara", "Parintins", "Tefé", "Outros"]) 
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
        
        self.btn_anexar = QPushButton("📁 Anexar RG, CPF e Comprovante")
        self.btn_anexar.setStyleSheet("background-color: #007bff; color: white;")
        self.btn_anexar.clicked.connect(self.selecionar_arquivos)
        self.lbl_arquivos = QLabel("Nenhum arquivo selecionado.")
        
        layout_upload = QHBoxLayout()
        layout_upload.addWidget(self.btn_anexar)
        layout_upload.addWidget(self.lbl_arquivos)

        layout_final.addRow("OBS:", self.input_obs)
        layout_final.addRow("Local:", lay_local)
        layout_final.addRow("Data do Formulário:", self.input_data_form) 
        layout_final.addRow("Arquivos:", layout_upload)
        
        grupo_final.setLayout(layout_final)
        layout_form.addWidget(grupo_final)

        layout_form.addStretch()
        scroll.setWidget(conteudo_scroll)
        layout_principal.addWidget(scroll)

        # ================= BOTÃO DE SALVAR =================
        self.btn_salvar = QPushButton("Salvar Cadastro Local e Gerar PDF")
        self.btn_salvar.setStyleSheet("background-color: #28a745; color: white; padding: 15px; font-size: 16px; font-weight: bold;")
        self.btn_salvar.clicked.connect(self.salvar_cadastro)
        layout_principal.addWidget(self.btn_salvar)

    def criar_grupo_checkboxes(self, opcoes, layout, label_texto):
        widget_cb = QWidget()
        layout_cb = QVBoxLayout(widget_cb)
        layout_cb.setContentsMargins(0, 0, 0, 0)
        lista_cb = []
        for op in opcoes:
            cb = QCheckBox(op)
            lista_cb.append(cb)
            layout_cb.addWidget(cb)
        layout.addRow(label_texto, widget_cb)
        return lista_cb

    def obter_texto_checkboxes(self, lista_checkboxes):
        selecionados = [cb.text() for cb in lista_checkboxes if cb.isChecked()]
        return ", ".join(selecionados)

    def selecionar_arquivos(self):
        arquivos, _ = QFileDialog.getOpenFileNames(self, "Selecione os Documentos", "", "Imagens/PDFs (*.pdf *.png *.jpg *.jpeg)")
        if arquivos:
            self.arquivos_anexados.extend(arquivos)
            self.lbl_arquivos.setText(f"{len(self.arquivos_anexados)} arquivo(s) selecionado(s).")

    def salvar_cadastro(self):
        # 1. Tipo de Cadastro
        tipo_cadastro = ""
        for texto, rb in self.radios_tipo.items():
            if rb.isChecked():
                tipo_cadastro = f"Outros: {self.input_outros_tipo.text()}" if texto == "Outros" else texto
                break

        if not tipo_cadastro:
            QMessageBox.warning(self, "Aviso", "Selecione o Tipo de Cadastro!")
            return

        # 2. Capturar e Limpar Dados
        razao = self.input_razao.text().strip()
        endereco = self.input_endereco.text().strip()
        cep = self.input_cep.text().replace("_", "").replace("-", "")
        email = self.input_email.text().strip()
        cnpj = self.input_cnpj.text().replace("_", "").replace(".", "").replace("/", "").replace("-", "")
        cpf = self.input_cpf.text().replace("_", "").replace(".", "").replace("-", "")
        rg = self.input_rg.text().strip()
        telefone = self.input_telefone.text().replace("_", "").replace("(", "").replace(")", "").replace(" ", "").replace("-", "")

        if not razao:
            QMessageBox.warning(self, "Aviso", "A Razão Social/Nome é obrigatória!")
            return

        # Captura o sexo selecionado (vazio se nenhum marcado)
        sexo = ""
        for texto, rb in self.radios_sexo.items():
            if rb.isChecked():
                sexo = texto
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

        str_class_social = self.obter_texto_checkboxes(self.checks_classificacao)
        str_motivos = self.obter_texto_checkboxes(self.checks_motivo)
        str_formas_comerc = self.obter_texto_checkboxes(self.checks_formas_comerc)

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
                    renda_preponderante, para_quem_comercializa, dificuldade_comercializacao, responsavel_vendas, 
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
                self.input_cartao.currentText(), self.input_pix.currentText(), str_class_social, str_motivos,
                str_formas_comerc, self.input_produtos.text(), self.input_pagam_taxa.currentText(), self.input_forma_contrib.currentText(),
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

        # Limpa os radio buttons de sexo
        self.bg_sexo.setExclusive(False)
        for rb in self.radios_sexo.values():
            rb.setChecked(False)
        self.bg_sexo.setExclusive(True)
        
        for cb in self.checks_classificacao + self.checks_motivo + self.checks_formas_comerc:
            cb.setChecked(False)
            
        combos = [self.input_forma_ecosol, self.input_forma_emp, self.input_segmento, 
                  self.input_cartao, self.input_pix, self.input_pagam_taxa, 
                  self.input_forma_contrib, self.input_renda, self.input_para_quem, 
                  self.input_dificuldade, self.input_resp_vendas, self.input_local]
        for combo in combos:
            combo.setCurrentIndex(0)
            
        self.input_data_form.setDate(QDate.currentDate()) 
        self.arquivos_anexados.clear()
        self.lbl_arquivos.setText("Nenhum arquivo selecionado.")