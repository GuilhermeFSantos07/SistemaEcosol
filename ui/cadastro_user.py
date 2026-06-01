import sqlite3
import hashlib
import uuid
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QComboBox, QMessageBox, 
                             QHeaderView, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt

class TelaUsuarios(QWidget):
    def __init__(self):
        super().__init__()
        # Removido o inicializar_banco() redundante. O main.py + db_config.py já cuidam disso.
        self.configurar_ui()
        self.carregar_usuarios()

    def gerar_hash(self, senha):
        """Converte a senha em um hash irreversível usando SHA-256"""
        return hashlib.sha256(senha.encode('utf-8')).hexdigest()

    def configurar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        # Título
        titulo = QLabel("GERENCIAMENTO DE USUÁRIOS")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #004b23; border-bottom: 2px solid #004b23; padding-bottom: 5px;")
        layout_principal.addWidget(titulo)

        # ================= FORMULÁRIO DE NOVO USUÁRIO =================
        grupo_novo = QGroupBox("Adicionar Novo Usuário")
        layout_form = QFormLayout()

        self.input_nome = QLineEdit() # Adicionado campo para Nome Completo
        self.input_login = QLineEdit()
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_nivel = QComboBox()
        self.input_nivel.addItems(["operador", "visualizador", "admin"])

        layout_form.addRow("Nome Completo:", self.input_nome)
        layout_form.addRow("Nome de Usuário (Login):", self.input_login)
        layout_form.addRow("Senha:", self.input_senha)
        layout_form.addRow("Nível de Acesso:", self.input_nivel)

        btn_salvar = QPushButton("💾 Salvar Usuário")
        btn_salvar.clicked.connect(self.salvar_usuario)
        layout_form.addRow("", btn_salvar)

        grupo_novo.setLayout(layout_form)
        layout_principal.addWidget(grupo_novo)

        # ================= LISTA DE USUÁRIOS =================
        layout_principal.addWidget(QLabel("<b>Usuários Cadastrados:</b>"))
        
        self.tabela_usuarios = QTableWidget()
        self.tabela_usuarios.setColumnCount(4) # Expandido para 4 colunas para incluir o Nome
        self.tabela_usuarios.setHorizontalHeaderLabels(["ID", "Nome", "Login", "Nível de Acesso"])
        self.tabela_usuarios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_usuarios.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela_usuarios.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) 
        
        layout_principal.addWidget(self.tabela_usuarios)

        # Botão para deletar usuário
        btn_deletar = QPushButton("🗑️ Excluir Usuário Selecionado")
        btn_deletar.setStyleSheet("background-color: #b7094c;")
        btn_deletar.clicked.connect(self.deletar_usuario)
        
        layout_btn_del = QHBoxLayout()
        layout_btn_del.addStretch()
        layout_btn_del.addWidget(btn_deletar)
        layout_principal.addLayout(layout_btn_del)

    def carregar_usuarios(self):
        """Busca os usuários no banco e preenche a tabela"""
        self.tabela_usuarios.setRowCount(0)
        conn = sqlite3.connect('ecosol_local.db')
        cursor = conn.cursor()
        
        # Agora buscamos o nome também
        cursor.execute("SELECT id, nome, login, nivel_acesso FROM usuarios")
        
        for linha_idx, linha_dados in enumerate(cursor.fetchall()):
            self.tabela_usuarios.insertRow(linha_idx)
            for col_idx, dado in enumerate(linha_dados):
                item = QTableWidgetItem(str(dado))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabela_usuarios.setItem(linha_idx, col_idx, item)
                
        conn.close()

    def salvar_usuario(self):
        nome = self.input_nome.text().strip()
        login = self.input_login.text().strip()
        senha = self.input_senha.text().strip()
        nivel = self.input_nivel.currentText()

        # Validação do novo campo
        if not nome or not login or not senha:
            QMessageBox.warning(self, "Aviso", "Preencha o nome, nome de usuário e a senha!")
            return

        senha_hash = self.gerar_hash(senha)
        usuario_id = str(uuid.uuid4()) # Gera o ID em formato de texto exatamente como pede o db_config.py

        try:
            conn = sqlite3.connect('ecosol_local.db')
            cursor = conn.cursor()
            
            # Query de insert ajustada para bater perfeitamente com as colunas reais do banco
            cursor.execute("""
                INSERT INTO usuarios (id, nome, login, senha_hash, nivel_acesso, sincronizado) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (usuario_id, nome, login, senha_hash, nivel, 0))
            
            conn.commit()
            conn.close()

            self.input_nome.clear()
            self.input_login.clear()
            self.input_senha.clear()
            self.carregar_usuarios()
            QMessageBox.information(self, "Sucesso", "Usuário cadastrado com sucesso!")
            
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Erro", "Este nome de usuário já existe!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")

    def deletar_usuario(self):
        linha_selecionada = self.tabela_usuarios.currentRow()
        if linha_selecionada < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um usuário na tabela para excluir.")
            return

        usuario_id = self.tabela_usuarios.item(linha_selecionada, 0).text()
        login = self.tabela_usuarios.item(linha_selecionada, 2).text() # O Login agora fica na coluna 2 (index 2)

        # Regra de proteção simplificada (verificando apenas pelo login 'admin')
        if login == "admin":
            QMessageBox.warning(self, "Aviso", "Não é possível excluir o administrador padrão do sistema!")
            return

        resposta = QMessageBox.question(self, "Confirmar", f"Tem certeza que deseja excluir o usuário '{login}'?", 
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if resposta == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect('ecosol_local.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
            conn.commit()
            conn.close()
            self.carregar_usuarios()
            QMessageBox.information(self, "Sucesso", "Usuário excluído!")