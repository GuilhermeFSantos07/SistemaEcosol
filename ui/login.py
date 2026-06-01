import sqlite3
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame, QMessageBox
from PyQt6.QtCore import Qt
from database.db_config import gerar_hash_senha

class TelaLogin(QWidget):
    """Tela de Login Integrada ao Banco Local e com Interface Blindada"""
    def __init__(self, callback_sucesso):
        super().__init__()
        self.callback_sucesso = callback_sucesso
        
        # Resgata a cor primária para estilizações inline pontuais se necessário
        self.COR_PRIMARIA = os.getenv("COR_PRIMARIA", "#003366")
        self.configurar_ui()

    def configurar_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Container Card (ID "CardLogin" que conversa com o QSS do main.py)
        container = QFrame()
        container.setObjectName("CardLogin")
        container.setFixedWidth(360)
        
        layout_card = QVBoxLayout(container)
        
        titulo = QLabel("SISTEMA ECOSOL")
        titulo.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {self.COR_PRIMARIA}; margin-bottom: 20px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_card.addWidget(titulo)
        
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Usuário")
        
        self.input_senha = QLineEdit()
        self.input_senha.setPlaceholderText("Senha")
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout_card.addWidget(QLabel("Usuário:"))
        layout_card.addWidget(self.input_user)
        layout_card.addWidget(QLabel("Senha:"))
        layout_card.addWidget(self.input_senha)
        
        btn_entrar = QPushButton("Entrar no Sistema")
        btn_entrar.clicked.connect(self.fazer_login)
        layout_card.addWidget(btn_entrar)
        
        layout.addWidget(container)

    def fazer_login(self):
        login_digitado = self.input_user.text().strip()
        senha_digitada = self.input_senha.text()
        
        if not login_digitado or not senha_digitada:
            QMessageBox.warning(self, "Aviso", "Por favor, preencha todos os campos!")
            return

        senha_hash = gerar_hash_senha(senha_digitada)

        try:
            conn = sqlite3.connect('ecosol_local.db')
            cursor = conn.cursor()
            
            # CORREÇÃO: Adicionado o campo 'id' (ou 'id_usuario' caso use esse nome) na busca
            cursor.execute(
                "SELECT id, nome, nivel_acesso FROM usuarios WHERE login = ? AND senha_hash = ?", 
                (login_digitado, senha_hash)
            )
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                # CORREÇÃO: Desempacota também o usuario_id retornado pelo banco local
                usuario_id, nome_usuario, nivel_acesso = resultado
                
                # O .lower() padroniza "Admin" para "admin", evitando quebras de permissão no painel
                # Repassa com segurança o ID e o nível de acesso para o main.py
                self.callback_sucesso(usuario_id, nivel_acesso.lower())
            else:
                QMessageBox.warning(self, "Erro", "Usuário ou senha inválidos!")
                
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro de Banco", f"Falha ao conectar no banco local: {e}")