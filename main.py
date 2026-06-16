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
from ui.cadastros import TelaCadastros

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
        self.sidebar.setFixedWidth(220)
        layout_sidebar = QVBoxLayout(self.sidebar)
        layout_sidebar.setContentsMargins(12, 24, 12, 20)
        layout_sidebar.setSpacing(4)
        
        lbl_logo = QLabel("ECOSOL AM")
        lbl_logo.setObjectName("LogoTitulo")
        lbl_logo.setStyleSheet("color: white; font-size: 20px; font-weight: bold; letter-spacing: 2px;")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_sidebar.addWidget(lbl_logo)
        
        lbl_subtitulo = QLabel("Sistema de Cadastro Offline")
        lbl_subtitulo.setObjectName("LogoSubtitulo")
        lbl_subtitulo.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 11px; margin-bottom: 24px;")
        lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_sidebar.addWidget(lbl_subtitulo)
        
        # Divisor visual
        divider = QFrame()
        divider.setObjectName("SidebarDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: rgba(255,255,255,0.15); margin: 0 4px 12px 4px; max-height: 1px; border: none;")
        layout_sidebar.addWidget(divider)
        
        self.btn_cadastro = QPushButton("Novo Cadastro")
        self.btn_sincronizacao = QPushButton("Sincronização")
        self.btn_cadastros = QPushButton("Cadastros Existentes")
        self.btn_relatorios = QPushButton("Relatórios")
        self.btn_usuarios = QPushButton("Gerenciar Usuários")
        self.btn_sair = QPushButton("Sair do Sistema")
        self.btn_sair.setObjectName("BtnSair")
        
        for btn in [self.btn_cadastro, self.btn_sincronizacao, self.btn_cadastros, self.btn_relatorios, self.btn_usuarios]:
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
        self.tela_cadastros = TelaCadastros()
        self.tela_relatorios = QLabel("<h2>Tela de Relatórios em Construção</h2>")
        self.tela_relatorios.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.conteudo_stack.addWidget(self.tela_novo_cadastro) 
        self.conteudo_stack.addWidget(self.tela_sincronizacao)
        self.conteudo_stack.addWidget(self.tela_cadastros)   
        self.conteudo_stack.addWidget(self.tela_relatorios)      
        self.conteudo_stack.addWidget(self.tela_usuarios)        
        
        self.btn_cadastro.clicked.connect(lambda: self.conteudo_stack.setCurrentWidget(self.tela_novo_cadastro))
        self.btn_cadastros.clicked.connect(lambda: self.conteudo_stack.setCurrentWidget(self.tela_cadastros))
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
        lbl_departamento.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout_rodape.addWidget(lbl_departamento)

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
    /* ── BASE ── */
    QWidget {{
        background-color: #eef1f6;
        color: #1a2033;
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
    }}

    QMainWindow, QStackedWidget {{
        background-color: #eef1f6;
    }}

    /* ── SCROLL AREA ── */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background: #dde1ea;
        width: 8px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: #b0b8cc;
        border-radius: 4px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* ── SIDEBAR ── */
    QFrame#Sidebar {{
        background-color: {COR_PRIMARIA};
        border: none;
        border-right: 1px solid rgba(255,255,255,0.08);
    }}
    QFrame#Sidebar QWidget {{
        background-color: transparent;
    }}

    /* Separador visual abaixo do logo na sidebar */
    QFrame#SidebarDivider {{
        background-color: rgba(255,255,255,0.15);
        max-height: 1px;
        margin: 0 12px 12px 12px;
    }}

    /* ── BOTÕES DO MENU LATERAL ── */
    QPushButton#BtnMenu {{
        background-color: transparent;
        color: rgba(255,255,255,0.75);
        text-align: left;
        padding: 11px 16px;
        font-size: 13px;
        font-weight: normal;
        border-radius: 8px;
        border: none;
    }}
    QPushButton#BtnMenu:hover {{
        background-color: rgba(255,255,255,0.12);
        color: #ffffff;
    }}
    QPushButton#BtnMenu:checked, QPushButton#BtnMenu:pressed {{
        background-color: rgba(255,255,255,0.18);
        color: #ffffff;
        font-weight: bold;
    }}

    QPushButton#BtnSair {{
        background-color: rgba(220, 53, 69, 0.85);
        color: #ffffff;
        border-radius: 8px;
        padding: 10px 16px;
        text-align: left;
        font-size: 13px;
        border: none;
    }}
    QPushButton#BtnSair:hover {{
        background-color: #dc3545;
    }}

    /* ── BOTÕES GERAIS ── */
    QPushButton {{
        background-color: {COR_PRIMARIA};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {COR_PRIMARIA_HOVER};
    }}
    QPushButton:disabled {{
        background-color: #b0b8cc;
        color: #ffffff;
    }}

    /* ── CARD DE LOGIN ── */
    QFrame#CardLogin {{
        background-color: #ffffff;
        border: none;
        border-radius: 16px;
        padding: 10px;
    }}

    /* ── CAMPOS DE TEXTO E COMBO ── */
    QLineEdit, QComboBox {{
        background-color: #ffffff;
        color: #1a2033;
        border: 1.5px solid #d5dae6;
        border-radius: 8px;
        padding: 8px 12px;
        min-height: 22px;
        selection-background-color: {COR_PRIMARIA};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 2px solid {COR_PRIMARIA};
        background-color: #f5f8ff;
    }}
    QLineEdit:disabled, QComboBox:disabled {{
        background-color: #f0f2f7;
        color: #9aa0b4;
        border: 1.5px solid #e2e6f0;
    }}
    QLineEdit::placeholder {{
        color: #adb5bd;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}
    QComboBox::down-arrow {{
        width: 12px;
        height: 12px;
    }}
    QComboBox QAbstractItemView {{
        background-color: #ffffff;
        border: 1.5px solid #d5dae6;
        border-radius: 8px;
        selection-background-color: {COR_PRIMARIA};
        selection-color: #ffffff;
        padding: 4px;
    }}

    /* ── GROUP BOX ESTILO CARD ── */
    QGroupBox {{
        background-color: #ffffff;
        border: none;
        border-radius: 12px;
        margin-top: 20px;
        padding: 20px 20px 16px 20px;
        font-weight: bold;
        font-size: 13px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 16px;
        top: 4px;
        padding: 0 6px;
        color: {COR_PRIMARIA};
        font-size: 13px;
        font-weight: bold;
        background-color: #ffffff;
    }}

    /* ── CHECKBOXES E RADIO BUTTONS ── */
    QCheckBox, QRadioButton {{
        background-color: transparent;
        color: #1a2033;
        padding: 4px 6px;
        spacing: 8px;
    }}
    QCheckBox:hover, QRadioButton:hover {{
        color: {COR_PRIMARIA};
    }}

    QRadioButton::indicator, QCheckBox::indicator {{
        width: 17px;
        height: 17px;
        border: 2px solid #b0b8cc;
        background-color: #ffffff;
    }}
    QRadioButton::indicator {{
        border-radius: 9px;
    }}
    QCheckBox::indicator {{
        border-radius: 5px;
    }}
    QRadioButton::indicator:hover, QCheckBox::indicator:hover {{
        border-color: {COR_PRIMARIA};
    }}
    QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
        background-color: {COR_PRIMARIA};
        border-color: {COR_PRIMARIA};
        image: url(NENHUMA);
    }}

    /* ── LABELS ── */
    QLabel {{
        background-color: transparent;
        color: #1a2033;
    }}

    /* ── TABELA ── */
    QTableWidget {{
        background-color: #ffffff;
        border: none;
        border-radius: 10px;
        gridline-color: #eef1f6;
        selection-background-color: #e8eeff;
        selection-color: #1a2033;
    }}
    QTableWidget::item {{
        padding: 8px;
        border-bottom: 1px solid #f0f2f7;
    }}
    QHeaderView::section {{
        background-color: #f5f7fc;
        color: #5a6380;
        font-weight: bold;
        font-size: 12px;
        padding: 10px 8px;
        border: none;
        border-bottom: 2px solid #dde1ea;
    }}

    /* ── TEXT EDIT (console de log) ── */
    QTextEdit {{
        background-color: #1a2033;
        color: #a8ffce;
        border-radius: 10px;
        border: none;
        padding: 12px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 12px;
    }}

    /* ── RODAPÉ ── */
    QFrame#Rodape {{
        background-color: #0d1526;
        border: none;
        border-top: 3px solid {COR_PRIMARIA};
    }}
    QLabel#TextoRodape {{
        color: rgba(255,255,255,0.65);
        font-size: 11px;
        font-weight: bold;
        letter-spacing: 0.5px;
        background-color: transparent;
    }}
"""

if __name__ == "__main__":
    inicializar_banco_local()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_FIEL_BLINDADO) 
    
    janela = JanelaPrincipal()
    sys.exit(app.exec())