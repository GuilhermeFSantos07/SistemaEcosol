import sqlite3      # Banco de dados local SQLite
import hashlib      # Geração do hash SHA-256 da senha
import uuid         # Geração de IDs únicos para cada usuário
import os           # Leitura das variáveis de ambiente do .env
from dotenv import load_dotenv  # Carrega o arquivo .env para os.getenv() funcionar

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,  # Layouts principais
    QLabel, QLineEdit, QPushButton,                   # Widgets básicos de formulário
    QTableWidget, QTableWidgetItem,                   # Tabela de listagem de usuários
    QComboBox, QMessageBox,                           # Combo de nível de acesso e caixas de diálogo
    QHeaderView, QGroupBox, QScrollArea,              # Cabeçalho da tabela, agrupador e scroll
    QFrame, QApplication                              # Frame para separadores e atualização de UI
)
from PyQt6.QtCore import Qt       # Constantes de alinhamento e flags
from PyQt6.QtGui import QColor    # Para colorir células da tabela se necessário

# Carrega as variáveis definidas no arquivo .env para que os os.getenv() abaixo funcionem
load_dotenv()

COR_PRIMARIA       = os.getenv("COR_PRIMARIA",       "#003366")  # Azul escuro — título, bordas, GroupBox
COR_PRIMARIA_HOVER = os.getenv("COR_PRIMARIA_HOVER", "#004080")  # Azul mais escuro — hover dos botões
COR_SECUNDARIA     = os.getenv("COR_SECUNDARIA",     "#17a2b8")  # Azul ciano — botão Editar
COR_ALERTA         = os.getenv("COR_ALERTA",         "#dc3545")  # Vermelho — botão Excluir
COR_FUNDO_CLARO    = os.getenv("COR_FUNDO_CLARO",   "#f8f9fa")  # Cinza muito claro — fundo geral
COR_TEXTO_ESCURO   = os.getenv("COR_TEXTO_ESCURO",   "#212529")  # Quase preto — texto dos labels
COR_TEXTO_CLARO    = os.getenv("COR_TEXTO_CLARO",    "#ffffff")  # Branco — texto sobre fundo colorido
COR_BORDA          = os.getenv("COR_BORDA",          "#ced4da")  # Cinza suave — bordas dos inputs
COR_SALVAR         = "#28a745"   # Verde fixo — botão Salvar (sem variável no .env, igual ao form_ecosol)
COR_SALVAR_HOVER   = "#218838"   # Verde escuro — hover do botão Salvar


class TelaUsuarios(QWidget):
    def __init__(self):
        super().__init__()

        # Armazena o ID do usuário em edição (None = modo de criação, string = modo de edição)
        self.usuario_em_edicao_id = None

        self.configurar_ui()      # Monta todos os widgets da tela
        self.carregar_usuarios()  # Preenche a tabela com os dados do banco

    # gerar_hash
    # Converte a senha em texto puro em um hash SHA-256 irreversível.
    # Mesmo algoritmo usado em db_config.py para garantir compatibilidade
    # com o login e com a sincronização para o PostgreSQL.
    def gerar_hash(self, senha):
        return hashlib.sha256(senha.encode('utf-8')).hexdigest()  # Retorna string hexadecimal de 64 caracteres

    # configurar_ui
    def configurar_ui(self):
        # Layout raiz vertical que empilha: título → formulário → tabela
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 20, 30, 20)  # Margens externas da tela
        layout_principal.setSpacing(16)                       # Espaço entre os blocos

        # ----- CABEÇALHO DA TELA -----
        # Título principal com linha decorativa inferior — idêntico ao form_ecosol e sincronizacao
        titulo = QLabel("GERENCIAMENTO DE USUÁRIOS")
        titulo.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {COR_PRIMARIA}; "
            f"border-bottom: 2px solid {COR_PRIMARIA}; "
            f"padding-bottom: 5px;"
        )
        layout_principal.addWidget(titulo)

        # GRUPO: FORMULÁRIO DE ADICIONAR / EDITAR USUÁRIO
        self.grupo_form = QGroupBox("Adicionar Novo Usuário")  # Título muda para "Editar" no modo edição
        self.grupo_form.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 13px;
                border: 1px solid {COR_BORDA};
                border-radius: 6px;
                margin-top: 12px;
                padding: 20px 20px 16px 20px;
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
                padding: 6px;
                background-color: {COR_TEXTO_CLARO};
                min-height: 28px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {COR_PRIMARIA};
            }}
            QLabel {{
                font-size: 13px;
                color: {COR_TEXTO_ESCURO};
            }}
        """)

        # Grid interno do formulário: 4 colunas para colocar 2 pares label+input por linha
        layout_grid = QGridLayout()
        layout_grid.setSpacing(10)             # Espaçamento entre células do grid
        layout_grid.setColumnStretch(1, 1)     # Coluna do 1º input é elástica (ocupa espaço disponível)
        layout_grid.setColumnStretch(3, 1)     # Coluna do 2º input é elástica

        # ----- Campo: Nome Completo (linha 0, colunas 0-1) -----
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Digite o nome completo do usuário")
        layout_grid.addWidget(QLabel("Nome Completo:"), 0, 0)   # Label na coluna 0
        layout_grid.addWidget(self.input_nome, 0, 1)            # Input na coluna 1

        # ----- Campo: Login / Nome de Usuário (linha 0, colunas 2-3) -----
        self.input_login = QLineEdit()
        self.input_login.setPlaceholderText("Nome de usuário para login")
        layout_grid.addWidget(QLabel("Nome de Usuário (Login):"), 0, 2)  # Label na coluna 2
        layout_grid.addWidget(self.input_login, 0, 3)                    # Input na coluna 3

        # ----- Campo: Senha (linha 1, colunas 0-1) -----
        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Senha do usuário")
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)  # Oculta os caracteres digitados
        layout_grid.addWidget(QLabel("Senha:"), 1, 0)
        layout_grid.addWidget(self.input_senha, 1, 1)

        # ----- Campo: Nível de Acesso (linha 1, colunas 2-3) -----
        self.input_nivel = QComboBox()
        self.input_nivel.addItems(["operador", "visualizador", "admin"])  # Opções de nível disponíveis
        layout_grid.addWidget(QLabel("Nível de Acesso:"), 1, 2)
        layout_grid.addWidget(self.input_nivel, 1, 3)

        self.grupo_form.setLayout(layout_grid)       # Aplica o grid ao GroupBox
        layout_principal.addWidget(self.grupo_form)  # Adiciona o GroupBox ao layout da tela

        # ----- BARRA DE BOTÕES DO FORMULÁRIO -----
        # Botões Salvar e Cancelar centralizados, com mesmo estilo do form_ecosol
        layout_botoes_form = QHBoxLayout()
        layout_botoes_form.setSpacing(12)
        layout_botoes_form.addStretch()  # Empurra os botões para o centro

        # Botão principal: Salvar Usuário (verde, igual ao btn_salvar do form_ecosol)
        self.btn_salvar = QPushButton("＋ Salvar Usuário")
        self.btn_salvar.setFixedWidth(200)  # Largura fixa para aparência uniforme
        self.btn_salvar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_SALVAR};
                color: {COR_TEXTO_CLARO};
                padding: 10px 22px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {COR_SALVAR_HOVER}; }}
        """)
        self.btn_salvar.clicked.connect(self.salvar_usuario)  # Conecta ao método de salvar
        layout_botoes_form.addWidget(self.btn_salvar)

        # Botão secundário: Cancelar (visível apenas no modo edição, começa oculto)
        self.btn_cancelar = QPushButton("✕ Cancelar Edição")
        self.btn_cancelar.setFixedWidth(180)
        self.btn_cancelar.setStyleSheet(f"""
            QPushButton {{
                background-color: #6c757d;
                color: {COR_TEXTO_CLARO};
                padding: 10px 22px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{ background-color: #5a6268; }}
        """)
        self.btn_cancelar.clicked.connect(self.cancelar_edicao)  # Conecta ao método de cancelar
        self.btn_cancelar.setVisible(False)   # Oculto por padrão — só aparece no modo edição
        layout_botoes_form.addWidget(self.btn_cancelar)

        layout_botoes_form.addStretch()  # Fecha o centering dos botões
        layout_principal.addLayout(layout_botoes_form)

        # SUBTÍTULO DA SEÇÃO DE LISTAGEM
        lbl_lista = QLabel("Usuários Cadastrados")
        lbl_lista.setStyleSheet(
            f"font-size: 15px; font-weight: bold; "
            f"color: {COR_PRIMARIA}; "
            f"border-bottom: 1px solid {COR_BORDA}; "
            f"padding-bottom: 4px;"
        )
        layout_principal.addWidget(lbl_lista)

        self.tabela_usuarios = QTableWidget()
        self.tabela_usuarios.setColumnCount(6)  # 6 colunas: #, ID, Nome, Login, Nível, Ações
        self.tabela_usuarios.setHorizontalHeaderLabels(
            ["#", "ID", "Nome", "Login", "Nível de Acesso", "Ações"]
        )

        # Estilo da tabela: fundo branco, bordas suaves, cabeçalho colorido
        self.tabela_usuarios.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COR_TEXTO_CLARO};
                border: 1px solid {COR_BORDA};
                border-radius: 6px;
                gridline-color: #f0f2f7;
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 8px;
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
                font-size: 12px;
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid {COR_BORDA};
            }}
        """)

        # Configurações de comportamento da tabela
        self.tabela_usuarios.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # Seleciona a linha inteira
        self.tabela_usuarios.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)         # Impede edição direta na célula
        self.tabela_usuarios.setAlternatingRowColors(False)  # Sem alternância de cor (estilo limpo)
        self.tabela_usuarios.verticalHeader().setVisible(False)  # Oculta o índice lateral esquerdo

        # Configuração das larguras das colunas
        header = self.tabela_usuarios.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)        # Coluna # — largura fixa pequena
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)      # Coluna ID — ocupa espaço livre
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)      # Coluna Nome — ocupa espaço livre
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)      # Coluna Login — ajusta ao conteúdo
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Coluna Nível — ajusta ao conteúdo
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)        # Coluna Ações — largura fixa

        self.tabela_usuarios.setColumnWidth(0, 40)   # Coluna # — pequena
        self.tabela_usuarios.setColumnWidth(5, 130)  # Coluna Ações — espaço para 2 botões

        layout_principal.addWidget(self.tabela_usuarios)  # Adiciona a tabela ao layout

    # carregar_usuarios
    # Busca todos os usuários no banco SQLite e preenche a tabela linha a linha.
    def carregar_usuarios(self):
        self.tabela_usuarios.setRowCount(0)  # Limpa todas as linhas antes de recarregar

        conn   = sqlite3.connect('ecosol_local.db')  # Abre conexão com o banco local
        cursor = conn.cursor()

        # Busca ID, Nome, Login e Nível de todos os usuários ordenados por nome
        cursor.execute("SELECT id, nome, login, nivel_acesso FROM usuarios ORDER BY nome")
        usuarios = cursor.fetchall()  # Recupera todos os resultados de uma vez
        conn.close()                  # Fecha a conexão imediatamente após a leitura

        for linha_idx, dados in enumerate(usuarios):
            usuario_id, nome, login, nivel = dados  # Desempacota os campos do registro

            self.tabela_usuarios.insertRow(linha_idx)  # Insere uma nova linha vazia na tabela

            # ----- Coluna 0: Número sequencial (#) -----
            item_num = QTableWidgetItem(str(linha_idx + 1))  # Exibe 1, 2, 3... (não o índice 0-base)
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Centraliza o número
            self.tabela_usuarios.setItem(linha_idx, 0, item_num)

            # ----- Coluna 1: ID do usuário (UUID completo) -----
            item_id = QTableWidgetItem(str(usuario_id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_usuarios.setItem(linha_idx, 1, item_id)

            # ----- Coluna 2: Nome completo -----
            item_nome = QTableWidgetItem(str(nome) if nome else "")  # Trata None do banco
            item_nome.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_usuarios.setItem(linha_idx, 2, item_nome)

            # ----- Coluna 3: Login -----
            item_login = QTableWidgetItem(str(login))
            item_login.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_usuarios.setItem(linha_idx, 3, item_login)

            # ----- Coluna 4: Nível de Acesso (com badge colorido) -----
            widget_nivel = QWidget()                              # Container para o badge
            widget_nivel.setStyleSheet("background: transparent;")
            layout_nivel = QHBoxLayout(widget_nivel)
            layout_nivel.setContentsMargins(4, 2, 4, 2)
            layout_nivel.setAlignment(Qt.AlignmentFlag.AlignCenter)

            badge = QLabel(str(nivel).capitalize())  # Ex: "Admin", "Operador"

            # Cor do badge varia conforme o nível de acesso
            if nivel.lower() == "admin":
                cor_badge = "#6f42c1"   # Roxo para admin — destaque visual
            elif nivel.lower() == "operador":
                cor_badge = COR_PRIMARIA  # Azul escuro para operador
            else:
                cor_badge = "#6c757d"   # Cinza para visualizador e outros

            badge.setStyleSheet(f"""
                background-color: {cor_badge};
                color: white;
                border-radius: 10px;
                padding: 2px 10px;
                font-size: 11px;
                font-weight: bold;
            """)
            layout_nivel.addWidget(badge)
            self.tabela_usuarios.setCellWidget(linha_idx, 4, widget_nivel)  # Insere o widget na célula

            # ----- Coluna 5: Ações (botões Editar e Excluir) -----
            widget_acoes = QWidget()
            widget_acoes.setStyleSheet("background: transparent;")
            layout_acoes = QHBoxLayout(widget_acoes)
            layout_acoes.setContentsMargins(4, 2, 4, 2)  # Margens internas pequenas
            layout_acoes.setSpacing(6)                    # Espaço entre os botões
            layout_acoes.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Botão Editar — azul ciano (COR_SECUNDARIA), mesmo padrão do btn_testar em sincronizacao
            btn_editar = QPushButton("✏️")
            btn_editar.setFixedSize(32, 28)     # Tamanho compacto para caber na linha
            btn_editar.setToolTip("Editar usuário")  # Tooltip ao passar o mouse
            btn_editar.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COR_SECUNDARIA};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }}
                QPushButton:hover {{ background-color: {COR_PRIMARIA}; }}
            """)
            # Lambda com argumento padrão captura o valor atual de usuario_id na iteração
            btn_editar.clicked.connect(lambda checked, uid=usuario_id: self.iniciar_edicao(uid))
            layout_acoes.addWidget(btn_editar)

            # Botão Excluir — vermelho (COR_ALERTA), mesmo tom do botão Baixar em sincronizacao
            btn_excluir = QPushButton("🗑️")
            btn_excluir.setFixedSize(32, 28)
            btn_excluir.setToolTip("Excluir usuário")
            btn_excluir.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COR_ALERTA};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }}
                QPushButton:hover {{ background-color: #c82333; }}
            """)
            # Lambda com argumento padrão captura login e id corretamente
            btn_excluir.clicked.connect(lambda checked, uid=usuario_id, lg=login: self.deletar_usuario(uid, lg))
            layout_acoes.addWidget(btn_excluir)

            self.tabela_usuarios.setCellWidget(linha_idx, 5, widget_acoes)  # Insere o widget na célula

            # Ajusta a altura da linha para acomodar os botões de ação
            self.tabela_usuarios.setRowHeight(linha_idx, 50)

    # iniciar_edicao
    # Chamado quando o usuário clica em "✏️ Editar" em uma linha da tabela.
    # Busca os dados do usuário no banco e preenche o formulário para edição.
    # Também muda o título do GroupBox e exibe o botão "Cancelar Edição".
    def iniciar_edicao(self, usuario_id):
        conn   = sqlite3.connect('ecosol_local.db')  # Abre conexão para buscar os dados
        cursor = conn.cursor()

        # Busca nome, login e nível do usuário pelo ID único
        cursor.execute("SELECT nome, login, nivel_acesso FROM usuarios WHERE id = ?", (usuario_id,))
        resultado = cursor.fetchone()  # Espera exatamente 1 resultado
        conn.close()

        if not resultado:
            # Segurança: se o registro não existir (foi deletado em paralelo), avisa e recarrega
            QMessageBox.warning(self, "Aviso", "Usuário não encontrado no banco!")
            self.carregar_usuarios()
            return

        nome, login, nivel = resultado  # Desempacota os dados retornados

        # Preenche os campos do formulário com os dados atuais do usuário
        self.input_nome.setText(nome or "")     # Nome completo
        self.input_login.setText(login)         # Login (nome de usuário)
        self.input_senha.clear()               # Senha sempre em branco (não exibe o hash)
        self.input_senha.setPlaceholderText("Deixe em branco para manter a senha atual")

        # Seleciona o nível correto no combo
        index = self.input_nivel.findText(nivel.lower())  # Busca o índice pelo texto
        if index >= 0:
            self.input_nivel.setCurrentIndex(index)  # Seleciona o item correspondente

        # Guarda o ID do usuário em edição para usar no UPDATE
        self.usuario_em_edicao_id = usuario_id

        # Atualiza a UI para modo de edição: muda título e exibe botão Cancelar
        self.grupo_form.setTitle("✏️ Editando Usuário")  # Indica visualmente o modo de edição
        self.btn_salvar.setText("💾 Atualizar Usuário")  # Muda texto do botão de salvar
        self.btn_cancelar.setVisible(True)              # Exibe o botão de cancelar

        # Rola a tela para o topo para que o formulário fique visível
        self.scroll().ensureWidgetVisible(self.grupo_form) if hasattr(self, 'scroll') else None

    # cancelar_edicao
    # Reseta o formulário e o estado da tela de volta ao modo de criação.
    # Chamado pelo botão "✕ Cancelar Edição".
    def cancelar_edicao(self):
        self.usuario_em_edicao_id = None   # Limpa o ID em edição (volta ao modo criação)

        # Limpa todos os campos do formulário
        self.input_nome.clear()
        self.input_login.clear()
        self.input_senha.clear()
        self.input_senha.setPlaceholderText("Senha do usuário")  # Restaura o placeholder original
        self.input_nivel.setCurrentIndex(0)  # Volta para o primeiro item ("operador")

        # Restaura o título e os botões para o modo de criação
        self.grupo_form.setTitle("Adicionar Novo Usuário")
        self.btn_salvar.setText("＋ Salvar Usuário")
        self.btn_cancelar.setVisible(False)  # Oculta o botão de cancelar

    # salvar_usuario
    # Chamado pelo botão "Salvar" / "Atualizar".
    # Se self.usuario_em_edicao_id for None → INSERT (novo usuário).
    # Se tiver um ID → UPDATE (atualização do usuário existente).
    # Valida os campos obrigatórios antes de qualquer operação no banco.
    def salvar_usuario(self):
        # Lê e limpa os valores dos campos do formulário
        nome  = self.input_nome.text().strip()
        login = self.input_login.text().strip()
        senha = self.input_senha.text().strip()
        nivel = self.input_nivel.currentText()  # Texto do item selecionado no combo

        # ----- Validação dos campos obrigatórios -----
        if not nome or not login:
            # Nome e login são sempre obrigatórios (para criar e para editar)
            QMessageBox.warning(self, "Aviso", "Preencha o Nome Completo e o Nome de Usuário!")
            return

        # No modo criação, a senha também é obrigatória
        if not self.usuario_em_edicao_id and not senha:
            QMessageBox.warning(self, "Aviso", "Preencha a senha para o novo usuário!")
            return

        # ----- Modo EDIÇÃO (UPDATE) -----
        if self.usuario_em_edicao_id:
            try:
                conn   = sqlite3.connect('ecosol_local.db')
                cursor = conn.cursor()

                if senha:
                    # Senha foi informada: atualiza todos os campos incluindo a senha
                    senha_hash = self.gerar_hash(senha)  # Gera novo hash SHA-256
                    cursor.execute("""
                        UPDATE usuarios
                        SET nome = ?, login = ?, senha_hash = ?, nivel_acesso = ?, sincronizado = 0
                        WHERE id = ?
                    """, (nome, login, senha_hash, nivel, self.usuario_em_edicao_id))
                else:
                    # Senha em branco: atualiza tudo EXCETO a senha (mantém o hash atual)
                    cursor.execute("""
                        UPDATE usuarios
                        SET nome = ?, login = ?, nivel_acesso = ?, sincronizado = 0
                        WHERE id = ?
                    """, (nome, login, nivel, self.usuario_em_edicao_id))

                conn.commit()   # Confirma a transação no banco
                conn.close()

                self.cancelar_edicao()    # Volta ao modo de criação e limpa o formulário
                self.carregar_usuarios()  # Recarrega a tabela com os dados atualizados
                QMessageBox.information(self, "Sucesso", "Usuário atualizado com sucesso!")

            except sqlite3.IntegrityError:
                # Ocorre se o login informado já pertence a outro usuário (UNIQUE no banco)
                QMessageBox.critical(self, "Erro", "Este nome de usuário já está em uso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao atualizar: {str(e)}")

        # ----- Modo CRIAÇÃO (INSERT) -----
        else:
            senha_hash  = self.gerar_hash(senha)        # Gera o hash da senha informada
            usuario_id  = str(uuid.uuid4())             # Gera UUID único para o novo usuário

            try:
                conn   = sqlite3.connect('ecosol_local.db')
                cursor = conn.cursor()

                # Insere o novo usuário com sincronizado=0 (pendente para envio ao servidor)
                cursor.execute("""
                    INSERT INTO usuarios (id, nome, login, senha_hash, nivel_acesso, sincronizado)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (usuario_id, nome, login, senha_hash, nivel, 0))

                conn.commit()
                conn.close()

                # Limpa o formulário e recarrega a tabela após o insert
                self.input_nome.clear()
                self.input_login.clear()
                self.input_senha.clear()
                self.carregar_usuarios()
                QMessageBox.information(self, "Sucesso", "Usuário cadastrado com sucesso!")

            except sqlite3.IntegrityError:
                # Login duplicado: a coluna login tem constraint UNIQUE no banco
                QMessageBox.critical(self, "Erro", "Este nome de usuário já existe!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")

    # deletar_usuario
    # Chamado pelo botão "🗑️" da coluna Ações.
    # Recebe o ID e o login diretamente (sem precisar ler da seleção da tabela).
    # Protege o usuário 'admin' de ser excluído acidentalmente.
    def deletar_usuario(self, usuario_id, login):
        # Proteção: o administrador padrão não pode ser excluído
        if login.lower() == "admin":
            QMessageBox.warning(self, "Aviso", "Não é possível excluir o administrador padrão do sistema!")
            return

        # Confirmação explícita antes de deletar — operação irreversível
        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o usuário '{login}'?\n\nEsta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            conn   = sqlite3.connect('ecosol_local.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))  # Delete pelo ID único
            conn.commit()
            conn.close()

            # Se estava editando este usuário, cancela a edição também
            if self.usuario_em_edicao_id == usuario_id:
                self.cancelar_edicao()

            self.carregar_usuarios()  # Recarrega a tabela sem o usuário deletado
            QMessageBox.information(self, "Sucesso", "Usuário excluído com sucesso!")