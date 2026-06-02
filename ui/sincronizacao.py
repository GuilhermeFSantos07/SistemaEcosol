import sqlite3
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv
import shutil
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QFormLayout, 
                             QTextEdit, QMessageBox, QApplication)
from PyQt6.QtCore import Qt

load_dotenv()

class TelaSincronizacao(QWidget):
    def __init__(self):
        super().__init__()
        self.configurar_ui()

    def configurar_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("SINCRONIZAÇÃO COM O SERVIDOR TI")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #004b23; border-bottom: 2px solid #004b23; padding-bottom: 5px;")
        layout_principal.addWidget(titulo)

        # ================= CREDENCIAIS DO POSTGRESQL =================
        grupo_credenciais = QGroupBox("Credenciais do Banco de Dados (PostgreSQL)")
        layout_form = QFormLayout()

        ip_servidor = os.getenv("DB_HOST", "localhost")
        porta_servidor = os.getenv("DB_PORT", "5432")

        self.input_host = QLineEdit(); self.input_host.setText(ip_servidor)
        self.input_porta = QLineEdit(); self.input_porta.setText(porta_servidor)
        self.input_banco = QLineEdit(); self.input_banco.setText("ecosol_db")
        self.input_usuario = QLineEdit() 
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.input_pasta_rede = QLineEdit()
        self.input_pasta_rede.setPlaceholderText("Ex: \\\\192.168.1.100\\Uploads_Ecosol")

        layout_form.addRow("IP / Host:", self.input_host)
        layout_form.addRow("Porta:", self.input_porta)
        layout_form.addRow("Nome do Banco:", self.input_banco)
        layout_form.addRow("Usuário (DB):", self.input_usuario)
        layout_form.addRow("Senha (DB):", self.input_senha)
        layout_form.addRow("Pasta Compartilhada (Arquivos):", self.input_pasta_rede)

        btn_testar = QPushButton("🔌 Testar Conexão")
        btn_testar.setStyleSheet("background-color: #0077b6;")
        btn_testar.clicked.connect(self.testar_conexao)
        layout_form.addRow("", btn_testar)

        grupo_credenciais.setLayout(layout_form)
        layout_principal.addWidget(grupo_credenciais)

        # ================= AÇÕES =================
        layout_acoes = QHBoxLayout()
        
        self.btn_enviar = QPushButton("⬆️ Enviar Dados (Notebook -> Servidor)")
        self.btn_enviar.setStyleSheet("background-color: #28a745; padding: 15px; font-size: 14px;")
        self.btn_enviar.clicked.connect(self.enviar_dados)
        
        self.btn_baixar = QPushButton("⬇️ Atualizar Local (Servidor -> Notebook)")
        self.btn_baixar.setStyleSheet("background-color: #e63946; padding: 15px; font-size: 14px;")
        self.btn_baixar.clicked.connect(self.baixar_dados)
        
        layout_acoes.addWidget(self.btn_enviar)
        layout_acoes.addWidget(self.btn_baixar)
        layout_principal.addLayout(layout_acoes)

        # ================= CONSOLE DE LOGS =================
        layout_principal.addWidget(QLabel("<b>Status da Sincronização:</b>"))
        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setStyleSheet("background-color: #f8f9fa; color: #212529; font-family: Consolas, monospace;")
        layout_principal.addWidget(self.console_log)

    def log(self, mensagem):
        """Adiciona uma mensagem ao console e força a atualização da tela"""
        self.console_log.append(f"> {mensagem}")
        QApplication.processEvents()

    def obter_conexao_pg(self):
        """Retorna a conexão com o PostgreSQL com base nos inputs"""
        return psycopg2.connect(
            host=self.input_host.text().strip(),
            port=self.input_porta.text().strip(),
            database=self.input_banco.text().strip(),
            user=self.input_usuario.text().strip(),
            password=self.input_senha.text().strip()
        )

    def testar_conexao(self):
        self.log("Testando conexão com o servidor PostgreSQL...")
        try:
            conn = self.obter_conexao_pg()
            conn.close()
            self.log("SUCESSO: Conexão estabelecida com o banco de dados!")
            QMessageBox.information(self, "Sucesso", "Conexão com o PostgreSQL bem-sucedida!")
        except Exception as e:
            self.log(f"ERRO DE CONEXÃO: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Falha ao conectar:\n{str(e)}")

    def enviar_dados(self):
        """Pega os dados do SQLite onde sincronizado=0 e envia para o PostgreSQL"""
        self.log("--- INICIANDO ENVIO DE DADOS (UPLOAD) ---")
        
        try:
            conn_pg = self.obter_conexao_pg()
            cursor_pg = conn_pg.cursor()
            
            conn_sl = sqlite3.connect('ecosol_local.db')
            cursor_sl = conn_sl.cursor()

            # =========================================================
            # ETAPA 1: Sincronizar TODOS os usuários (pendentes ou não)
            # que sejam responsáveis por cadastros ainda não sincronizados.
            # Isso garante que a FK do Postgres seja satisfeita antes de
            # inserir os cadastros, independente do estado 'sincronizado'
            # do usuário no SQLite.
            # =========================================================
            self.log("Verificando usuários responsáveis por cadastros pendentes...")

            # Busca IDs de responsáveis dos cadastros que ainda precisam subir
            cursor_sl.execute("""
                SELECT DISTINCT u.id, u.nome, u.login, u.senha_hash, u.nivel_acesso
                FROM usuarios u
                INNER JOIN cadastros_ecosol c ON c.responsavel_id = u.id
                WHERE c.sincronizado = 0
            """)
            responsaveis_necessarios = cursor_sl.fetchall()

            for u in responsaveis_necessarios:
                try:
                    # UPSERT: insere ou ignora se já existir — garante que o usuário
                    # está no Postgres antes de qualquer cadastro referenciar ele
                    cursor_pg.execute("""
                        INSERT INTO usuarios (id, nome, login, senha_hash, nivel_acesso)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (u[0], u[1] or u[2], u[2], u[3], u[4]))
                    self.log(f"Usuário responsável '{u[2]}' garantido no servidor.")
                except Exception as e:
                    self.log(f"Aviso ao garantir usuário responsável '{u[2]}': {e}")

            # Commit intermediário OBRIGATÓRIO: os usuários precisam estar
            # confirmados no Postgres antes de inserirmos os cadastros que
            # os referenciam via FK. Sem isso, o Postgres rejeita a FK mesmo
            # que o INSERT de usuário tenha rodado na mesma transação.
            conn_pg.commit()
            self.log("Usuários responsáveis confirmados no servidor.")

            # =========================================================
            # ETAPA 1b: Sincronizar usuários pendentes restantes (sem cadastros)
            # =========================================================
            cursor_sl.execute("""
                SELECT id, nome, login, senha_hash, nivel_acesso 
                FROM usuarios 
                WHERE sincronizado = 0 OR sincronizado IS NULL
            """)
            usuarios_pendentes = cursor_sl.fetchall()

            for u in usuarios_pendentes:
                try:
                    cursor_pg.execute("""
                        INSERT INTO usuarios (id, nome, login, senha_hash, nivel_acesso)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (u[0], u[1] or u[2], u[2], u[3], u[4]))
                    cursor_sl.execute("UPDATE usuarios SET sincronizado = 1 WHERE id = ?", (u[0],))
                    self.log(f"Usuário '{u[2]}' sincronizado.")
                except Exception as e:
                    self.log(f"Aviso ao sincronizar usuário '{u[2]}': {e}")

            conn_pg.commit()
            conn_sl.commit()

            # =========================================================
            # ETAPA 2: Sincronizar CADASTROS pendentes
            # =========================================================
            cursor_sl.execute("SELECT * FROM cadastros_ecosol WHERE sincronizado = 0")
            cadastros_pendentes = cursor_sl.fetchall()
            
            if not cadastros_pendentes:
                self.log("Nenhum cadastro pendente para enviar.")
            else:
                colunas = [desc[0] for desc in cursor_sl.description if desc[0] != 'sincronizado']
                placeholders = ', '.join(['%s'] * len(colunas))
                colunas_str = ', '.join(colunas)
                
                query_insert = f"""
                    INSERT INTO cadastros_ecosol ({colunas_str}) 
                    VALUES ({placeholders}) 
                    ON CONFLICT (id) DO NOTHING
                """
                
                cadastros_enviados = 0
                for cad in cadastros_pendentes:
                    try:
                        # Remove o último campo (sincronizado) antes de enviar
                        dados_insercao = cad[:-1]
                        cursor_pg.execute(query_insert, dados_insercao)
                        cursor_sl.execute(
                            "UPDATE cadastros_ecosol SET sincronizado = 1 WHERE id = ?", 
                            (cad[0],)
                        )
                        cadastros_enviados += 1
                        self.log(f"Cadastro ID {cad[0][:8]}... enviado.")
                    except Exception as e:
                        # Loga o erro do cadastro específico mas continua os demais
                        self.log(f"ERRO no cadastro {cad[0][:8]}...: {e}")
                        conn_pg.rollback()  # Reverte só este cadastro com problema

                conn_pg.commit()
                conn_sl.commit()
                self.log(f"{cadastros_enviados} de {len(cadastros_pendentes)} cadastro(s) enviados.")

            # =========================================================
            # ETAPA 3: Sincronizar ARQUIVOS pendentes
            # =========================================================
            pasta_rede = self.input_pasta_rede.text().strip()
            cursor_sl.execute(
                "SELECT id, cadastro_id, caminho_arquivo FROM arquivos_anexos WHERE sincronizado = 0"
            )
            arquivos_pendentes = cursor_sl.fetchall()
            
            for arq in arquivos_pendentes:
                arq_id, cad_id, caminho_local = arq
                
                if pasta_rede and os.path.exists(caminho_local):
                    nome_arquivo = os.path.basename(caminho_local)
                    destino_rede = os.path.join(pasta_rede, nome_arquivo)
                    try:
                        shutil.copy(caminho_local, destino_rede)
                        caminho_final_banco = destino_rede
                    except Exception as e:
                        self.log(f"Erro ao copiar arquivo {nome_arquivo} para a rede: {e}")
                        caminho_final_banco = caminho_local
                else:
                    caminho_final_banco = caminho_local
                
                try:
                    cursor_pg.execute("""
                        INSERT INTO arquivos_anexos (id, cadastro_id, caminho_arquivo) 
                        VALUES (%s, %s, %s) 
                        ON CONFLICT (id) DO NOTHING
                    """, (arq_id, cad_id, caminho_final_banco))
                    cursor_sl.execute(
                        "UPDATE arquivos_anexos SET sincronizado = 1 WHERE id = ?", 
                        (arq_id,)
                    )
                    self.log(f"Arquivo do cadastro {cad_id[:8]}... sincronizado.")
                except Exception as e:
                    self.log(f"Erro ao sincronizar arquivo {arq_id[:8]}...: {e}")

            conn_pg.commit()
            conn_sl.commit()
            
            conn_pg.close()
            conn_sl.close()
            
            self.log("--- UPLOAD CONCLUÍDO COM SUCESSO ---")
            QMessageBox.information(self, "Concluído", "Todos os dados pendentes foram enviados para o servidor!")
            
        except Exception as e:
            self.log(f"ERRO CRÍTICO NO UPLOAD: {str(e)}")
            QMessageBox.critical(self, "Erro", f"A sincronização falhou:\n{str(e)}")

    def baixar_dados(self):
        """Pega todos os dados do PostgreSQL e atualiza o SQLite local"""
        self.log("--- INICIANDO ATUALIZAÇÃO LOCAL (DOWNLOAD) ---")
        try:
            conn_pg = self.obter_conexao_pg()
            cursor_pg = conn_pg.cursor()
            
            conn_sl = sqlite3.connect('ecosol_local.db')
            cursor_sl = conn_sl.cursor()

            # Baixando Usuários
            self.log("Baixando usuários do servidor...")
            cursor_pg.execute("SELECT id, nome, login, senha_hash, nivel_acesso FROM usuarios")
            for u in cursor_pg.fetchall():
                cursor_sl.execute("""
                    INSERT OR IGNORE INTO usuarios (id, nome, login, senha_hash, nivel_acesso, sincronizado) 
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (u[0], u[1], u[2], u[3], u[4]))
            
            # Baixando Cadastros
            self.log("Baixando cadastros da base central...")
            cursor_pg.execute("SELECT * FROM cadastros_ecosol")
            colunas_pg = [desc[0] for desc in cursor_pg.description]
            cadastros = cursor_pg.fetchall()
            
            if cadastros:
                placeholders = ', '.join(['?'] * (len(colunas_pg) + 1))  # +1 para o 'sincronizado'
                colunas_str = ', '.join(colunas_pg) + ', sincronizado'
                
                query_sl = f"INSERT OR IGNORE INTO cadastros_ecosol ({colunas_str}) VALUES ({placeholders})"
                
                for cad in cadastros:
                    dados_sl = cad + (1,)
                    cursor_sl.execute(query_sl, dados_sl)
            
            conn_sl.commit()
            conn_pg.close()
            conn_sl.close()
            
            self.log("--- DOWNLOAD CONCLUÍDO COM SUCESSO ---")
            QMessageBox.information(self, "Concluído", "O banco de dados local foi atualizado com as informações do servidor!")

        except Exception as e:
            self.log(f"ERRO CRÍTICO NO DOWNLOAD: {str(e)}")