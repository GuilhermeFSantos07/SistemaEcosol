import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget, QFrame)
from PyQt6.QtCore import Qt
from database.db_config import inicializar_banco_local
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

COR_PRIMARIA = os.getenv("COR_PRIMARIA", "#003366")
COR_PRIMARIA_HOVER = os.getenv("COR_PRIMARIA_HOVER", "#004080")
COR_BARRA_RODAPE = os.getenv("COR_BARRA_RODAPE", "#111111")
COR_TEXTO_CLARO = os.getenv("COR_TEXTO_CLARO", "#ffffff")
COR_FUNDO_CLARO = os.getenv("COR_FUNDO_CLARO", "#f8f9fa")

# Importações das suas telas modulares
from ui.login import TelaLogin
from ui.form_ecosol import TelaNovoCadastro
from ui.sincronizacao import TelaSincronizacao
from ui.cadastro_user import TelaUsuarios

class PainelSistema(QWidget):
    """Área Principal com Menu Lateral Esquerdo, Conteúdo e Rodapé"""
    def __init__(self, usuario_id, nivel_acesso, ao_deslogar):
        super().__init__()
        self.usuario_id = usuario_id
        self.nivel_acesso = nivel_acesso
        self.ao_deslogar = ao_deslogar
        
        # Layout Mestre (Vertical: Corpo do Sistema em cima, Rodapé embaixo)
        layout_mestre = QVBoxLayout(self)
        layout_mestre.setContentsMargins(0, 0, 0, 0)
        layout_mestre.setSpacing(0)
        
        # ================= CORPO DO SISTEMA (Sidebar + Telas) =================
        corpo_sistema = QWidget()
        layout_corpo = QHBoxLayout(corpo_sistema)
        layout_corpo.setContentsMargins(0, 0, 0, 0)
        layout_corpo.setSpacing(0)
        
        # 1. MENU LATERAL (SIDEBAR)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(240)
        layout_sidebar = QVBoxLayout(self.sidebar)
        layout_sidebar.setContentsMargins(10, 20, 10, 20)
        
        lbl_logo = QLabel("ECOSOL AM")
        lbl_logo.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-bottom: 30px;")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_sidebar.addWidget(lbl_logo)
        
        self.btn_cadastro = QPushButton("📝 Novo Cadastro")
        self.btn_sincronizacao = QPushButton("🔄 Sincronização")
        self.btn_relatorios = QPushButton("📊 Relatórios")
        self.btn_usuarios = QPushButton("👥 Gerenciar Usuários")
        self.btn_sair = QPushButton("🚪 Sair do Sistema")
        self.btn_sair.setObjectName("BtnSair")
        
        for btn in [self.btn_cadastro, self.btn_sincronizacao, self.btn_relatorios, self.btn_usuarios]:
            btn.setObjectName("BtnMenu")
            layout_sidebar.addWidget(btn)
            
        # Controle de nível de acesso (garantido pelo .lower() no banco)
        if self.nivel_acesso != "admin":
            self.btn_usuarios.setVisible(False)
            
        layout_sidebar.addStretch()
        layout_sidebar.addWidget(self.btn_sair)
        
        layout_corpo.addWidget(self.sidebar)
        
        # 2. ÁREA DE CONTEÚDO (DIREITA)
        self.conteudo_stack = QStackedWidget()
        
        # Passando o ID do usuário logado para a tela de Novo Cadastro evitar erros no Postgres
        self.tela_novo_cadastro = TelaNovoCadastro(self, usuario_logado_id=self.usuario_id)
        self.tela_usuarios = TelaUsuarios()
        self.tela_sincronizacao = TelaSincronizacao()
        self.tela_relatorios = QLabel("<h2>Tela de Relatórios em Construção</h2>")
        self.tela_relatorios.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.conteudo_stack.addWidget(self.tela_novo_cadastro) 
        self.conteudo_stack.addWidget(self.tela_sincronizacao)   
        self.conteudo_stack.addWidget(self.tela_relatorios)      
        self.conteudo_stack.addWidget(self.tela_usuarios)        
        
        self.btn_cadastro.clicked.connect(lambda: self.conteudo_stack.setCurrentWidget(self.tela_novo_cadastro))
        self.btn_sincronizacao.clicked.connect(lambda: self.conteudo_stack.setCurrentWidget(self.tela_sincronizacao))
        self.btn_relatorios.clicked.connect(lambda: self.conteudo_stack.setCurrentWidget(self.tela_relatorios))
        self.btn_usuarios.clicked.connect(lambda: self.conteudo_stack.setCurrentWidget(self.tela_usuarios))
        self.btn_sair.clicked.connect(self.ao_deslogar)

        # Adiciona o stack de conteúdo ao corpo uma única vez (Linha duplicada corrigida aqui)
        layout_corpo.addWidget(self.conteudo_stack)
        layout_mestre.addWidget(corpo_sistema, stretch=1)

        # ================= BARRA DE RODAPÉ INSTITUCIONAL =================
        barra_rodape = QFrame()
        barra_rodape.setObjectName("Rodape")
        barra_rodape.setFixedHeight(35)
        
        layout_rodape = QHBoxLayout(barra_rodape)
        layout_rodape.setContentsMargins(15, 0, 15, 0)

        lbl_departamento = QLabel("DEPARTAMENTO DE TECNOLOGIA DA INFORMAÇÃO — DETI | SETEMP")
        lbl_departamento.setObjectName("TextoRodape")
        lbl_info_sistema = QLabel("SISTEMA ECOSOL | CADASTRO OFFLINE")
        lbl_info_sistema.setObjectName("TextoRodape")
        
        layout_rodape.addWidget(lbl_departamento, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout_rodape.addStretch()
        layout_rodape.addWidget(lbl_info_sistema, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout_mestre.addWidget(barra_rodape)


class JanelaPrincipal(QMainWindow):
    """Janela Mestra do Software"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Ecosol - Cadastro Offline")
        self.setMinimumSize(1024, 720)
        
        self.stacked_central = QStackedWidget()
        self.setCentralWidget(self.stacked_central)
        
        self.mostrar_tela_login()
        
    def mostrar_tela_login(self):
        # A TelaLogin agora deve retornar (id_usuario, nivel_acesso) no seu sinal/callback_sucesso
        self.tela_login = TelaLogin(self.fazer_login_sucesso)
        self.stacked_central.addWidget(self.tela_login)
        self.stacked_central.setCurrentWidget(self.tela_login)
        self.showNormal() 

    def fazer_login_sucesso(self, usuario_id, nivel_acesso):
        # Captura os dois parâmetros e repassa para o Painel do Sistema
        self.painel_sistema = PainelSistema(usuario_id, nivel_acesso, self.mostrar_tela_login)
        self.stacked_central.addWidget(self.painel_sistema)
        self.stacked_central.setCurrentWidget(self.painel_sistema)
        self.showMaximized()


# ================= STYLESHEET (QSS) DINÂMICO =================
STYLE_FIEL_BLINDADO = f"""
    QWidget {{
        background-color: {COR_FUNDO_CLARO};
        color: #212529;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
    }}
    
    QFrame#CardLogin {{
        background-color: {COR_TEXTO_CLARO};
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 20px;
    }}
    
    QLineEdit, QComboBox {{
        background-color: {COR_TEXTO_CLARO} !important;
        color: #212529 !important;
        border: 1px solid #ced4da;
        border-radius: 4px;
        padding: 8px;
        min-height: 20px;
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 2px solid {COR_PRIMARIA};
    }}
    
    QGroupBox {{
        background-color: {COR_TEXTO_CLARO};
        border: 2px solid #dee2e6;
        border-radius: 6px;
        margin-top: 15px;
        padding-top: 15px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
        color: {COR_PRIMARIA};
    }}
    
    QCheckBox, QRadioButton {{
        background-color: transparent;
        color: #212529;
        padding: 4px;
    }}

    QRadioButton::indicator, QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid #ced4da;
        background-color: {COR_TEXTO_CLARO};
    }}
    QRadioButton::indicator {{
        border-radius: 10px;
    }}
    QCheckBox::indicator {{
        border-radius: 4px;
    }}
    QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
        background-color: {COR_PRIMARIA};
        border: 2px solid {COR_PRIMARIA};
        image: url(NENHUMA); 
    }}
    
    QScrollArea {{
        border: none;
        background-color: {COR_FUNDO_CLARO};
    }}
    
    QFrame#Sidebar {{
        background-color: {COR_PRIMARIA}; 
        border: none;
    }}
    QFrame#Sidebar QWidget {{
        background-color: transparent;
    }}
    
    QPushButton {{
        background-color: {COR_PRIMARIA};
        color: {COR_TEXTO_CLARO};
        border: none;
        border-radius: 4px;
        padding: 10px 15px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {COR_PRIMARIA_HOVER};
    }}
    
    QPushButton#BtnMenu {{
        background-color: transparent;
        color: #e9ecef;
        text-align: left;
        padding: 12px 15px;
        font-size: 14px;
        border-radius: 4px;
    }}
    QPushButton#BtnMenu:hover {{
        background-color: {COR_PRIMARIA_HOVER};
        color: {COR_TEXTO_CLARO};
    }}
    
    QPushButton#BtnSair {{
        background-color: #dc3545;
        color: {COR_TEXTO_CLARO};
    }}
    QPushButton#BtnSair:hover {{
        background-color: #c82333;
    }}

    QFrame#Rodape {{
        background-color: {COR_BARRA_RODAPE};
        border-top: 2px solid {COR_PRIMARIA};
    }}
    QLabel#TextoRodape {{
        color: {COR_TEXTO_CLARO};
        font-size: 11px;
        font-weight: bold;
        background-color: transparent;
    }}
"""

if __name__ == "__main__":
    inicializar_banco_local()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_FIEL_BLINDADO) 
    
    janela = JanelaPrincipal()
    sys.exit(app.exec())