# sincronizacao.py
# Tela de sincronização entre o banco local SQLite e o servidor PostgreSQL.
# Usa as mesmas variáveis de cor do .env que o form_ecosol.py para manter
# a identidade visual consistente em toda a aplicação.

import sqlite3
import psycopg2
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv  # Lê as variáveis do arquivo .env e injeta no ambiente
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QLineEdit, QPushButton, QGroupBox,
                             QTextEdit, QMessageBox, QApplication)
from PyQt6.QtCore import Qt

# Carrega o .env para que os os.getenv() abaixo consigam ler as variáveis
load_dotenv()

# PALETA DE CORES — lidas do .env, espelhando exatamente o form_ecosol.py
# Centraliza a identidade visual: mudar o .env reestiliza toda a aplicação
COR_PRIMARIA       = os.getenv("COR_PRIMARIA",       "#003366")  # Azul escuro — título, bordas de foco, GroupBox
COR_PRIMARIA_HOVER = os.getenv("COR_PRIMARIA_HOVER", "#004080")  # Azul mais escuro — estado hover dos botões
COR_SECUNDARIA     = os.getenv("COR_SECUNDARIA",     "#17a2b8")  # Azul ciano — botão "Testar Conexão"
COR_FUNDO_CLARO    = os.getenv("COR_FUNDO_CLARO",    "#f8f9fa")  # Cinza muito claro — fundo do console de log
COR_TEXTO_ESCURO   = os.getenv("COR_TEXTO_ESCURO",   "#212529")  # Quase preto — texto do console e labels
COR_TEXTO_CLARO    = os.getenv("COR_TEXTO_CLARO",    "#ffffff")  # Branco — texto sobre fundos coloridos
COR_BORDA          = os.getenv("COR_BORDA",          "#ced4da")  # Cinza suave — bordas dos inputs e GroupBox
COR_ENVIAR         = "#28a745"                                   # Verde fixo — botão Enviar (sem variável no .env)
COR_ENVIAR_HOVER   = "#218838"                                   # Verde escuro — hover do botão Enviar
COR_BAIXAR         = os.getenv("COR_ALERTA",         "#dc3545")  # Vermelho do .env — botão Baixar/Atualizar
COR_BAIXAR_HOVER   = "#c82333"                                   # Vermelho escuro — hover do botão Baixar

# TelaSincronizacao
# Widget que permite ao usuário configurar as credenciais do PostgreSQL,
# testar a conexão, enviar dados locais para o servidor e baixar atualizações.
class TelaSincronizacao(QWidget):
    def __init__(self):
        super().__init__()
        self.configurar_ui()  # Monta todos os widgets da tela

    def configurar_ui(self):
        # Layout raiz: apenas centraliza o widget de conteúdo horizontalmente
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        # Widget interno com largura máxima de 1200px — igual ao form_ecosol
        # Impede que o formulário fique excessivamente largo em telas grandes
        conteudo = QWidget()
        conteudo.setMaximumWidth(1200)

        # Layout vertical principal: título → credenciais → botões → console
        layout_principal = QVBoxLayout(conteudo)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        layout_principal.setSpacing(15)  # Espaçamento uniforme entre os blocos

        # Centraliza o conteudo no layout raiz
        layout_raiz.addWidget(conteudo, alignment=Qt.AlignmentFlag.AlignHCenter)

        # TÍTULO DA TELA
        # Usa COR_PRIMARIA para manter visual idêntico ao form_ecosol
        titulo = QLabel("SINCRONIZAÇÃO COM O SERVIDOR TI")
        titulo.setStyleSheet(
            f"font-size: 22px; font-weight: bold; "
            f"color: {COR_PRIMARIA}; "
            f"border-bottom: 2px solid {COR_PRIMARIA}; "
            f"padding-bottom: 5px;"
        )
        layout_principal.addWidget(titulo)

        # GRUPO: CREDENCIAIS DO POSTGRESQL
        # Campos organizados em grid 2 colunas (label | input) para aproveitar
        # melhor o espaço horizontal — padrão do form_ecosol
        grupo_credenciais = QGroupBox("Credenciais do Banco de Dados (PostgreSQL)")
        # QSS do grupo de credenciais, espelhando o padrão visual do form_ecosol
        grupo_credenciais.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COR_BORDA};
                border-radius: 6px;
                margin-top: 12px;
                padding: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 15px;
                padding: 0 5px;
                color: {COR_PRIMARIA};
            }}
            QLineEdit {{
                border: 1px solid {COR_BORDA};
                border-radius: 4px;
                padding: 6px;
                background-color: {COR_TEXTO_CLARO};
            }}
            QLineEdit:focus {{
                border: 1px solid {COR_PRIMARIA};
            }}
            QLabel {{
                font-size: 13px;
                color: {COR_TEXTO_ESCURO};
            }}
        """)

        # Grid de 4 colunas: label | input | label | input
        # Coloca dois pares por linha, como no form_ecosol
        layout_grid = QGridLayout()
        layout_grid.setSpacing(10)
        layout_grid.setColumnStretch(1, 1)  # Coluna do primeiro input é elástica
        layout_grid.setColumnStretch(3, 1)  # Coluna do segundo input é elástica

        # Pré-popula host e porta com os valores do .env (se existirem)
        ip_servidor    = os.getenv("DB_HOST", "localhost")  # Lê o IP do servidor do .env
        porta_servidor = os.getenv("DB_PORT", "5432")       # Lê a porta do .env

        # Criação dos campos de entrada com valores padrão onde aplicável
        self.input_host    = QLineEdit(); self.input_host.setText(ip_servidor)
        self.input_porta   = QLineEdit(); self.input_porta.setText(porta_servidor)
        self.input_banco   = QLineEdit(); self.input_banco.setText("ecosol_db")  # Nome padrão do banco
        self.input_usuario = QLineEdit(); self.input_usuario.setPlaceholderText("Usuário do banco de dados")
        self.input_senha   = QLineEdit(); self.input_senha.setPlaceholderText("Senha do banco de dados")
        self.input_senha.setEchoMode(QLineEdit.EchoMode.Password)  # Oculta os caracteres da senha

        # Campo para o caminho da pasta de rede onde os arquivos serão copiados
        self.input_pasta_rede = QLineEdit()
        self.input_pasta_rede.setPlaceholderText(r"Ex: \\192.168.1.100\Uploads_Ecosol")

        # Linha 0: IP/Host | Porta
        layout_grid.addWidget(QLabel("IP / Host:"), 0, 0)
        layout_grid.addWidget(self.input_host, 0, 1)
        layout_grid.addWidget(QLabel("Porta:"), 0, 2)
        layout_grid.addWidget(self.input_porta, 0, 3)

        # Linha 1: Nome do Banco | Usuário
        layout_grid.addWidget(QLabel("Nome do Banco:"), 1, 0)
        layout_grid.addWidget(self.input_banco, 1, 1)
        layout_grid.addWidget(QLabel("Usuário (DB):"), 1, 2)
        layout_grid.addWidget(self.input_usuario, 1, 3)

        # Linha 2: Senha | Pasta Compartilhada
        layout_grid.addWidget(QLabel("Senha (DB):"), 2, 0)
        layout_grid.addWidget(self.input_senha, 2, 1)
        layout_grid.addWidget(QLabel("Pasta Compartilhada:"), 2, 2)
        layout_grid.addWidget(self.input_pasta_rede, 2, 3)

        grupo_credenciais.setLayout(layout_grid)
        layout_principal.addWidget(grupo_credenciais)

        # BARRA DE BOTÕES DE AÇÃO — 3 botões lado a lado, centralizados
        # Mesmo padrão de tamanho e layout dos botões do form_ecosol
        # (Salvar: 240px, Gerar PDF: 240px → aqui usamos o mesmo fixedWidth)
        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(20)
        layout_botoes.setContentsMargins(0, 5, 0, 5)
        layout_botoes.addStretch()  # Empurra os botões para o centro

        # Botão Testar Conexão — azul ciano (COR_SECUNDARIA), igual ao form_ecosol
        self.btn_testar = QPushButton("Testar Conexão")
        self.btn_testar.setFixedWidth(240)  # Mesmo fixedWidth dos botões do form_ecosol
        self.btn_testar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_SECUNDARIA};
                color: {COR_TEXTO_CLARO};
                padding: 10px 22px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COR_PRIMARIA};
            }}
        """)
        self.btn_testar.clicked.connect(self.testar_conexao)
        layout_botoes.addWidget(self.btn_testar)

        # Botão Enviar — verde fixo (COR_ENVIAR), espelhando o btn_salvar do form_ecosol
        self.btn_enviar = QPushButton("⬆ Enviar Dados")
        self.btn_enviar.setFixedWidth(240)
        self.btn_enviar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_ENVIAR};
                color: {COR_TEXTO_CLARO};
                padding: 10px 22px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COR_ENVIAR_HOVER};
            }}
        """)
        self.btn_enviar.clicked.connect(self.enviar_dados)
        layout_botoes.addWidget(self.btn_enviar)

        # Botão Baixar — vermelho (COR_BAIXAR = COR_ALERTA do .env), espelhando btn_pdf
        self.btn_baixar = QPushButton("⬇ Atualizar Local")
        self.btn_baixar.setFixedWidth(240)
        self.btn_baixar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_BAIXAR};
                color: {COR_TEXTO_CLARO};
                padding: 10px 22px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COR_BAIXAR_HOVER};
            }}
        """)
        self.btn_baixar.clicked.connect(self.baixar_dados)
        layout_botoes.addWidget(self.btn_baixar)

        layout_botoes.addStretch()  # Fecha o centering
        layout_principal.addLayout(layout_botoes)

        # CONSOLE DE LOG
        # Área de texto somente leitura que exibe o progresso da sincronização
        # em tempo real (linha a linha, via self.log())
        lbl_status = QLabel("<b>Status da Sincronização:</b>")
        lbl_status.setStyleSheet(f"color: {COR_TEXTO_ESCURO}; font-size: 13px;")
        layout_principal.addWidget(lbl_status)

        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)  # Usuário não pode editar o console
        # Fonte monoespaçada facilita a leitura de logs; cores do .env para consistência
        self.console_log.setStyleSheet(
            f"background-color: {COR_FUNDO_CLARO}; "
            f"color: {COR_TEXTO_ESCURO}; "
            f"font-family: Consolas, monospace; "
            f"border: 1px solid {COR_BORDA}; "
            f"border-radius: 4px; "
            f"padding: 8px;"
        )
        layout_principal.addWidget(self.console_log)  # O console ocupa o espaço restante

    # log
    # Appenda uma mensagem ao console e força o redesenho imediato da tela.
    # processEvents() é necessário pois a sincronização roda na thread principal
    # e sem ele a UI ficaria congelada durante o processo.
    def log(self, mensagem):
        self.console_log.append(f"> {mensagem}")  # Prefixo ">" facilita leitura no console
        QApplication.processEvents()              # Força atualização visual imediata

    # obter_conexao_pg
    # Cria e retorna uma conexão psycopg2 com o PostgreSQL usando os valores
    # digitados nos inputs da tela. Lança exceção se a conexão falhar,
    # que é capturada pelos métodos chamadores (testar_conexao, enviar, baixar).
    def obter_conexao_pg(self):
        return psycopg2.connect(
            host=self.input_host.text().strip(),      # IP ou hostname do servidor
            port=self.input_porta.text().strip(),      # Porta TCP (padrão PostgreSQL: 5432)
            database=self.input_banco.text().strip(),  # Nome do banco de dados
            user=self.input_usuario.text().strip(),    # Usuário do banco
            password=self.input_senha.text().strip()   # Senha do banco
        )

    # testar_conexao
    # Apenas abre e fecha uma conexão para validar as credenciais.
    # Exibe mensagem de sucesso ou erro no console e em um QMessageBox.
    def testar_conexao(self):
        self.log("Testando conexão com o servidor PostgreSQL...")
        try:
            conn = self.obter_conexao_pg()
            conn.close()  # Fecha imediatamente — o objetivo é só testar
            self.log("SUCESSO: Conexão estabelecida com o banco de dados!")
            QMessageBox.information(self, "Sucesso", "Conexão com o PostgreSQL bem-sucedida!")
        except Exception as e:
            self.log(f"ERRO DE CONEXÃO: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Falha ao conectar:\n{str(e)}")

    # enviar_dados
    # Sincroniza do SQLite local para o PostgreSQL em 3 etapas:
    #   Etapa 1  — Garante que os usuários responsáveis por cadastros pendentes
    #              já existam no Postgres (evita violação de FK).
    #   Etapa 1b — Sincroniza os demais usuários locais ainda não enviados.
    #   Etapa 2  — Envia os cadastros com sincronizado=0.
    #   Etapa 3  — Copia arquivos físicos para a pasta de rede e registra no PG.
    def enviar_dados(self):
        self.log("--- INICIANDO ENVIO DE DADOS (UPLOAD) ---")

        try:
            conn_pg = self.obter_conexao_pg()      # Conexão com o PostgreSQL remoto
            cursor_pg = conn_pg.cursor()

            conn_sl = sqlite3.connect('ecosol_local.db')  # Conexão com o SQLite local
            cursor_sl = conn_sl.cursor()

            # ETAPA 1: Usuários responsáveis por cadastros pendentes
            # O Postgres tem FK de cadastros_ecosol.responsavel_id → usuarios.id
            # Por isso o usuário precisa existir no PG ANTES do cadastro ser inserido.
            self.log("Verificando usuários responsáveis por cadastros pendentes...")

            # Busca somente os usuários que são referenciados por cadastros ainda não enviados
            cursor_sl.execute("""
                SELECT DISTINCT u.id, u.nome, u.login, u.senha_hash, u.nivel_acesso
                FROM usuarios u
                INNER JOIN cadastros_ecosol c ON c.responsavel_id = u.id
                WHERE c.sincronizado = 0
            """)
            responsaveis_necessarios = cursor_sl.fetchall()

            for u in responsaveis_necessarios:
                try:
                    # ON CONFLICT (login) DO UPDATE: o "login" é a identidade real do usuário
                    # entre instalações diferentes (cada instalação local gera seu próprio "id"
                    # UUID para o admin padrão, mas o login "admin" é sempre o mesmo). Por isso
                    # o conflito é resolvido pelo login, não pelo id — e ao colidir, ATUALIZA os
                    # dados no servidor (nome/senha/nível) em vez de simplesmente ignorar.
                    cursor_pg.execute("""
                        INSERT INTO usuarios (id, nome, login, senha_hash, nivel_acesso)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (login) DO UPDATE SET
                            nome = EXCLUDED.nome,
                            senha_hash = EXCLUDED.senha_hash,
                            nivel_acesso = EXCLUDED.nivel_acesso
                    """, (u[0], u[1] or u[2], u[2], u[3], u[4]))
                    self.log(f"Usuário responsável '{u[2]}' garantido/atualizado no servidor.")
                except Exception as e:
                    self.log(f"Aviso ao garantir usuário responsável '{u[2]}': {e}")

            # Commit intermediário OBRIGATÓRIO: os usuários devem estar confirmados
            # no PG antes dos cadastros serem inseridos (validação de FK pelo Postgres)
            conn_pg.commit()
            self.log("Usuários responsáveis confirmados no servidor.")

            # ETAPA 1b: Demais usuários locais ainda não sincronizados
            # Cobre usuários criados localmente que não têm cadastros associados
            cursor_sl.execute("""
                SELECT id, nome, login, senha_hash, nivel_acesso
                FROM usuarios
                WHERE sincronizado = 0 OR sincronizado IS NULL
            """)
            usuarios_pendentes = cursor_sl.fetchall()

            for u in usuarios_pendentes:
                try:
                    # Mesma lógica da Etapa 1: conflito resolvido pelo login (identidade real),
                    # atualizando os dados no servidor em vez de ignorar quando já existir.
                    cursor_pg.execute("""
                        INSERT INTO usuarios (id, nome, login, senha_hash, nivel_acesso)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (login) DO UPDATE SET
                            nome = EXCLUDED.nome,
                            senha_hash = EXCLUDED.senha_hash,
                            nivel_acesso = EXCLUDED.nivel_acesso
                    """, (u[0], u[1] or u[2], u[2], u[3], u[4]))
                    # Marca como sincronizado no SQLite local para não reenviar
                    cursor_sl.execute("UPDATE usuarios SET sincronizado = 1 WHERE id = ?", (u[0],))
                    self.log(f"Usuário '{u[2]}' sincronizado.")
                except Exception as e:
                    self.log(f"Aviso ao sincronizar usuário '{u[2]}': {e}")

            conn_pg.commit()   # Confirma inserções de usuários no Postgres
            conn_sl.commit()   # Confirma marcações de sincronizado no SQLite

            # ETAPA 2: Cadastros pendentes (sincronizado = 0)
            # Monta o INSERT dinamicamente a partir das colunas da tabela,
            # excluindo a coluna 'sincronizado' que é exclusiva do SQLite.
            cursor_sl.execute("SELECT * FROM cadastros_ecosol WHERE sincronizado = 0")
            cadastros_pendentes = cursor_sl.fetchall()

            if not cadastros_pendentes:
                self.log("Nenhum cadastro pendente para enviar.")
            else:
                # Pega os nomes das colunas do cursor, excluindo 'sincronizado'
                colunas      = [desc[0] for desc in cursor_sl.description if desc[0] != 'sincronizado']
                placeholders = ', '.join(['%s'] * len(colunas))  # Ex: "%s, %s, %s, ..."
                colunas_str  = ', '.join(colunas)

                query_insert = f"""
                    INSERT INTO cadastros_ecosol ({colunas_str})
                    VALUES ({placeholders})
                    ON CONFLICT (id) DO NOTHING
                """

                cadastros_enviados = 0
                for cad in cadastros_pendentes:
                    try:
                        dados_insercao = cad[:-1]  # Remove o último campo (sincronizado) antes de enviar
                        cursor_pg.execute(query_insert, dados_insercao)
                        # Marca o cadastro como sincronizado no SQLite local
                        cursor_sl.execute(
                            "UPDATE cadastros_ecosol SET sincronizado = 1 WHERE id = ?",
                            (cad[0],)
                        )
                        cadastros_enviados += 1
                        self.log(f"Cadastro ID {cad[0][:8]}... enviado.")
                    except Exception as e:
                        self.log(f"ERRO no cadastro {cad[0][:8]}...: {e}")
                        conn_pg.rollback()  # Reverte apenas este cadastro; os outros continuam

                conn_pg.commit()  # Confirma todos os cadastros enviados no Postgres
                conn_sl.commit()  # Confirma todas as marcações de sincronizado no SQLite
                self.log(f"{cadastros_enviados} de {len(cadastros_pendentes)} cadastro(s) enviados.")

            # ETAPA 3: Arquivos físicos (sincronizado = 0)
            # Se a pasta de rede estiver preenchida e o arquivo existir localmente,
            # copia para a rede. O caminho final (rede ou local) é registrado no PG.
            pasta_rede = self.input_pasta_rede.text().strip()
            cursor_sl.execute(
                "SELECT id, cadastro_id, caminho_arquivo FROM arquivos_anexos WHERE sincronizado = 0"
            )
            arquivos_pendentes = cursor_sl.fetchall()

            for arq in arquivos_pendentes:
                arq_id, cad_id, caminho_local = arq

                if pasta_rede and os.path.exists(caminho_local):
                    # Tenta copiar o arquivo para a pasta de rede compartilhada
                    nome_arquivo  = os.path.basename(caminho_local)
                    destino_rede  = os.path.join(pasta_rede, nome_arquivo)
                    try:
                        shutil.copy(caminho_local, destino_rede)  # Cópia física do arquivo
                        caminho_final_banco = destino_rede         # Usa o caminho de rede no banco
                    except Exception as e:
                        self.log(f"Erro ao copiar arquivo {nome_arquivo} para a rede: {e}")
                        caminho_final_banco = caminho_local         # Fallback: mantém caminho local
                else:
                    caminho_final_banco = caminho_local  # Pasta de rede não configurada: salva caminho local

                try:
                    # Registra o arquivo no Postgres com o caminho final resolvido
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

            conn_pg.commit()   # Confirma registros de arquivos no Postgres
            conn_sl.commit()   # Confirma marcações de arquivos no SQLite

            conn_pg.close()    # Encerra a conexão com o PostgreSQL
            conn_sl.close()    # Encerra a conexão com o SQLite

            self.log("--- UPLOAD CONCLUÍDO COM SUCESSO ---")
            QMessageBox.information(self, "Concluído", "Todos os dados pendentes foram enviados para o servidor!")

        except Exception as e:
            # Captura erros críticos que impedem o início ou a execução geral da sincronização
            self.log(f"ERRO CRÍTICO NO UPLOAD: {str(e)}")
            QMessageBox.critical(self, "Erro", f"A sincronização falhou:\n{str(e)}")

    # baixar_dados
    # Busca no PostgreSQL todos os usuários e cadastros e insere no SQLite
    # local com INSERT OR IGNORE (não sobrescreve registros já existentes).
    # Marca os registros baixados com sincronizado=1 para evitar reenvio.
    def baixar_dados(self):
        self.log("--- INICIANDO ATUALIZAÇÃO LOCAL (DOWNLOAD) ---")
        try:
            conn_pg = self.obter_conexao_pg()        # Abre conexão com o servidor
            cursor_pg = conn_pg.cursor()

            conn_sl = sqlite3.connect('ecosol_local.db')  # Abre o banco local
            cursor_sl = conn_sl.cursor()

            # Baixa e insere/atualiza usuários do servidor no banco local.
            # Conflito resolvido pelo "login" (mesma lógica do upload): se o login
            # já existir localmente, ATUALIZA nome/senha/nível com o que está no
            # servidor (fonte de verdade). Se não existir, insere como novo.
            # Loga explicitamente quantos foram novos e quantos foram atualizados,
            # já que antes o INSERT OR IGNORE escondia silenciosamente os conflitos.
            self.log("Baixando usuários do servidor...")
            cursor_pg.execute("SELECT id, nome, login, senha_hash, nivel_acesso FROM usuarios")
            usuarios_servidor = cursor_pg.fetchall()

            novos_usuarios = 0
            atualizados_usuarios = 0

            for u in usuarios_servidor:
                # Verifica antes se o login já existe localmente, só para fins de log
                cursor_sl.execute("SELECT id FROM usuarios WHERE login = ?", (u[2],))
                ja_existia = cursor_sl.fetchone() is not None

                cursor_sl.execute("""
                    INSERT INTO usuarios (id, nome, login, senha_hash, nivel_acesso, sincronizado)
                    VALUES (?, ?, ?, ?, ?, 1)
                    ON CONFLICT(login) DO UPDATE SET
                        nome = excluded.nome,
                        senha_hash = excluded.senha_hash,
                        nivel_acesso = excluded.nivel_acesso,
                        sincronizado = 1
                """, (u[0], u[1], u[2], u[3], u[4]))  # sincronizado=1: já veio do servidor

                if ja_existia:
                    atualizados_usuarios += 1
                    self.log(f"Usuário '{u[2]}' já existia localmente — dados atualizados.")
                else:
                    novos_usuarios += 1
                    self.log(f"Usuário '{u[2]}' novo — inserido localmente.")

            self.log(f"Usuários: {novos_usuarios} novo(s), {atualizados_usuarios} atualizado(s).")

            # Baixa cadastros do servidor e insere localmente
            # Colunas são lidas dinamicamente do cursor para robustez
            self.log("Baixando cadastros da base central...")
            cursor_pg.execute("SELECT * FROM cadastros_ecosol")
            colunas_pg = [desc[0] for desc in cursor_pg.description]  # Nomes das colunas do PG
            cadastros  = cursor_pg.fetchall()

            if cadastros:
                # Adiciona a coluna 'sincronizado' que existe no SQLite mas não no PG
                placeholders = ', '.join(['?'] * (len(colunas_pg) + 1))  # +1 para o sincronizado
                colunas_str  = ', '.join(colunas_pg) + ', sincronizado'

                query_sl = f"INSERT OR IGNORE INTO cadastros_ecosol ({colunas_str}) VALUES ({placeholders})"

                for cad in cadastros:
                    dados_sl = cad + (1,)          # Acrescenta sincronizado=1 ao final da tupla
                    cursor_sl.execute(query_sl, dados_sl)

            conn_sl.commit()   # Confirma todas as inserções no SQLite

            conn_pg.close()    # Encerra conexão com o PostgreSQL
            conn_sl.close()    # Encerra conexão com o SQLite

            self.log("--- DOWNLOAD CONCLUÍDO COM SUCESSO ---")
            QMessageBox.information(self, "Concluído", "O banco de dados local foi atualizado com as informações do servidor!")

        except Exception as e:
            # Captura qualquer falha durante o download e exibe no console
            self.log(f"ERRO CRÍTICO NO DOWNLOAD: {str(e)}")