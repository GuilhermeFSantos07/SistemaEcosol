# =============================================================================
# seguranca.py
# Módulo central de controle de acesso do sistema ECOSOL AM.
#
# Responsabilidades:
#   1. Definir as PERMISSÕES de cada cargo (quais telas pode acessar e se pode
#      interagir ou só visualizar)
#   2. Fornecer funções auxiliares que o main.py usa para aplicar as regras
#      em tempo de execução (mostrar/ocultar botões, bloquear widgets)
#
# Cargos disponíveis (vêm do banco como string em minúsculo):
#   "admin"       → acesso total, sem restrições
#   "operador"    → acessa Novo Cadastro e Cadastros (interação completa)
#   "visualizador"→ acessa Novo Cadastro, Cadastros e Relatórios, mas somente
#                   em modo leitura (widgets desabilitados, sem salvar/editar)
#
# Como usar no main.py:
#   from utils.seguranca import Seguranca
#   Seguranca.configurar_painel(painel, nivel_acesso)
# =============================================================================

from PyQt6.QtWidgets import (
    QWidget,       # Classe base de todos os widgets — usada para varredura recursiva
    QPushButton,   # Botões que serão desabilitados no modo visualizador
    QLineEdit,     # Campos de texto que serão bloqueados no modo visualizador
    QComboBox,     # Combos que serão bloqueados no modo visualizador
    QCheckBox,     # Checkboxes que serão bloqueados no modo visualizador
    QRadioButton,  # RadioButtons que serão bloqueados no modo visualizador
    QDateEdit,     # Seletores de data que serão bloqueados no modo visualizador
    QTextEdit,     # Áreas de texto que serão bloqueadas no modo visualizador
)


# =============================================================================
# MAPA DE PERMISSÕES POR CARGO
#
# Estrutura de cada cargo:
#   "telas_visiveis"   → lista de nomes de atributos do PainelSistema que
#                        correspondem aos botões do menu lateral que o cargo
#                        pode VER (clicar para acessar a tela)
#   "telas_somente_leitura" → lista de nomes de atributos do PainelSistema
#                        que correspondem às telas carregadas em modo leitura
#                        (widgets internos desabilitados para interação)
#
# Nomes usados aqui devem bater EXATAMENTE com os atributos do PainelSistema
# em main.py (self.btn_cadastro, self.tela_novo_cadastro, etc.)
# =============================================================================
PERMISSOES = {

    # -------------------------------------------------------------------------
    # ADMIN — acesso irrestrito a tudo
    # Todos os botões do menu ficam visíveis e nenhuma tela é bloqueada.
    # -------------------------------------------------------------------------
    "admin": {
        "telas_visiveis": [
            "btn_cadastro",        # Botão "Novo Cadastro" no menu lateral
            "btn_cadastros",       # Botão "Cadastros" no menu lateral
            "btn_sincronizacao",   # Botão "Sincronização" no menu lateral
            "btn_relatorios",      # Botão "Relatórios" no menu lateral
            "btn_usuarios",        # Botão "Gerenciar Usuários" no menu lateral
        ],
        "telas_somente_leitura": [],  # Nenhuma tela é bloqueada para o admin
    },

    # -------------------------------------------------------------------------
    # OPERADOR — pode interagir com Novo Cadastro e Cadastros
    # Não vê Sincronização, Relatórios nem Gerenciar Usuários.
    # -------------------------------------------------------------------------
    "operador": {
        "telas_visiveis": [
            "btn_cadastro",    # Botão "Novo Cadastro" no menu lateral
            "btn_cadastros",   # Botão "Cadastros" no menu lateral
        ],
        "telas_somente_leitura": [],  # As telas visíveis são totalmente interativas
    },

    # -------------------------------------------------------------------------
    # VISUALIZADOR — vê Novo Cadastro, Cadastros e Relatórios, mas somente leitura
    # Pode navegar pelas telas, mas todos os campos e botões ficam desabilitados.
    # -------------------------------------------------------------------------
    "visualizador": {
        "telas_visiveis": [
            "btn_cadastro",    # Botão "Novo Cadastro" no menu (tela em modo leitura)
            "btn_cadastros",   # Botão "Cadastros" no menu (tela em modo leitura)
            "btn_relatorios",  # Botão "Relatórios" no menu (tela em modo leitura)
        ],
        "telas_somente_leitura": [
            "tela_novo_cadastro",  # Formulário de cadastro — apenas visualização
            "tela_cadastros",      # Listagem de cadastros — apenas visualização
            "tela_relatorios",     # Relatórios — apenas visualização
        ],
    },
}

# Cargo padrão aplicado quando o nível recebido não é reconhecido pelo sistema.
# Segurança defensiva: se vier um cargo desconhecido, bloqueia tudo.
CARGO_PADRAO_DESCONHECIDO = "visualizador"


# =============================================================================
# Seguranca
# Classe utilitária com métodos estáticos — não precisa ser instanciada.
# Todos os métodos são chamados diretamente: Seguranca.configurar_painel(...)
# =============================================================================
class Seguranca:

    # =========================================================================
    # configurar_painel
    # Ponto de entrada principal. Chamado pelo PainelSistema em main.py logo
    # após a construção da interface, passando a si mesmo (self) e o nível.
    #
    # Parâmetros:
    #   painel        → instância do PainelSistema (tem os atributos btn_*, tela_*)
    #   nivel_acesso  → string do banco: "admin", "operador" ou "visualizador"
    #
    # O que faz:
    #   1. Resolve o cargo (normaliza para minúsculo, usa padrão se desconhecido)
    #   2. Aplica visibilidade dos botões do menu lateral
    #   3. Aplica bloqueio de interação nas telas de somente leitura
    # =========================================================================
    @staticmethod
    def configurar_painel(painel, nivel_acesso: str):

        # Normaliza o nível para minúsculo para evitar erros com "Admin", "ADMIN" etc.
        nivel = nivel_acesso.strip().lower() if nivel_acesso else CARGO_PADRAO_DESCONHECIDO

        # Se o cargo não existir no mapa, usa o cargo padrão mais restritivo
        if nivel not in PERMISSOES:
            nivel = CARGO_PADRAO_DESCONHECIDO

        # Busca as regras do cargo no mapa de permissões
        regras = PERMISSOES[nivel]

        # --- Passo 1: Configura a visibilidade dos botões do menu lateral ---
        Seguranca._aplicar_visibilidade_menu(painel, regras["telas_visiveis"])

        # --- Passo 2: Bloqueia interação nas telas de somente leitura ---
        Seguranca._aplicar_somente_leitura(painel, regras["telas_somente_leitura"])

        # --- Passo 3: Garante que a primeira tela visível esteja selecionada ---
        Seguranca._navegar_para_primeira_tela(painel, regras["telas_visiveis"])

    # =========================================================================
    # _aplicar_visibilidade_menu
    # Percorre TODOS os botões do menu lateral e define quais ficam visíveis.
    # Botões não listados em "telas_visiveis" são ocultados (setVisible(False)).
    #
    # Parâmetros:
    #   painel          → instância do PainelSistema
    #   botoes_visiveis → lista de nomes de atributos dos botões permitidos
    # =========================================================================
    @staticmethod
    def _aplicar_visibilidade_menu(painel, botoes_visiveis: list):

        # Lista completa de todos os botões do menu que existem no PainelSistema.
        # Se um botão for adicionado ao main.py no futuro, deve ser incluído aqui também.
        todos_os_botoes_menu = [
            "btn_cadastro",       # Novo Cadastro
            "btn_cadastros",      # Cadastros (listagem)
            "btn_sincronizacao",  # Sincronização
            "btn_relatorios",     # Relatórios
            "btn_usuarios",       # Gerenciar Usuários
        ]

        for nome_btn in todos_os_botoes_menu:
            # Busca o atributo no painel pelo nome string (ex: painel.btn_cadastro)
            botao = getattr(painel, nome_btn, None)

            if botao is None:
                # O atributo não existe no painel — pula silenciosamente
                # (pode acontecer se um botão ainda não foi implementado)
                continue

            # Exibe o botão se estiver na lista de permitidos; oculta caso contrário
            botao.setVisible(nome_btn in botoes_visiveis)

    # =========================================================================
    # _aplicar_somente_leitura
    # Para cada tela listada em "telas_somente_leitura", percorre recursivamente
    # todos os widgets filhos e desabilita os interativos (inputs, combos, botões).
    #
    # Widgets QLabel são mantidos habilitados para que o texto permaneça legível.
    # Widgets de layout (QFrame, QGroupBox) não são tocados — só os interativos.
    #
    # Parâmetros:
    #   painel      → instância do PainelSistema
    #   telas_sl    → lista de nomes de atributos das telas a bloquear
    # =========================================================================
    @staticmethod
    def _aplicar_somente_leitura(painel, telas_sl: list):

        # Tipos de widget que serão desabilitados no modo somente leitura
        # QLabel é EXCLUÍDO intencionalmente para manter textos visíveis e legíveis
        WIDGETS_INTERATIVOS = (
            QPushButton,   # Botões de ação (Salvar, Gerar PDF, Pesquisar etc.)
            QLineEdit,     # Campos de texto
            QComboBox,     # Listas suspensas
            QCheckBox,     # Caixas de seleção múltipla
            QRadioButton,  # Botões de seleção exclusiva
            QDateEdit,     # Seletores de data
            QTextEdit,     # Áreas de texto multi-linha
        )

        for nome_tela in telas_sl:
            # Busca o widget da tela no painel pelo nome do atributo
            tela = getattr(painel, nome_tela, None)

            if tela is None:
                # A tela ainda não existe ou o nome está errado — pula
                continue

            # findChildren percorre recursivamente TODOS os descendentes do widget
            # e retorna os que são instâncias de QWidget (ou subclasses)
            todos_widgets = tela.findChildren(QWidget)

            for widget in todos_widgets:
                # Verifica se o widget é de um tipo interativo que deve ser bloqueado
                if isinstance(widget, WIDGETS_INTERATIVOS):
                    widget.setEnabled(False)   # Desabilita: widget fica cinza e não responde

            # Também desabilita o próprio widget raiz da tela caso ele seja interativo
            # (raro, mas garante cobertura total)
            if isinstance(tela, WIDGETS_INTERATIVOS):
                tela.setEnabled(False)

    # =========================================================================
    # _navegar_para_primeira_tela
    # Após configurar a visibilidade, garante que o conteúdo exibido seja
    # a primeira tela que o cargo tem permissão de acessar.
    # Evita que o sistema fique mostrando uma tela "em branco" ou bloqueada.
    #
    # Mapeamento entre nome do botão e nome do atributo da tela correspondente:
    #   btn_cadastro     → tela_novo_cadastro
    #   btn_cadastros    → tela_cadastros
    #   btn_sincronizacao→ tela_sincronizacao
    #   btn_relatorios   → tela_relatorios
    #   btn_usuarios     → tela_usuarios
    # =========================================================================
    @staticmethod
    def _navegar_para_primeira_tela(painel, botoes_visiveis: list):

        # Dicionário que traduz nome do botão para nome da tela correspondente
        BOTAO_PARA_TELA = {
            "btn_cadastro":       "tela_novo_cadastro",   # Formulário de novo cadastro
            "btn_cadastros":      "tela_cadastros",        # Listagem/pesquisa de cadastros
            "btn_sincronizacao":  "tela_sincronizacao",    # Sincronização com PostgreSQL
            "btn_relatorios":     "tela_relatorios",       # Relatórios
            "btn_usuarios":       "tela_usuarios",         # Gerenciamento de usuários
        }

        for nome_btn in botoes_visiveis:
            # Pega o nome da tela correspondente ao primeiro botão visível
            nome_tela = BOTAO_PARA_TELA.get(nome_btn)

            if nome_tela is None:
                continue  # Botão sem tela mapeada — pula

            # Busca a tela no painel pelo nome do atributo
            tela = getattr(painel, nome_tela, None)

            if tela is not None and hasattr(painel, "conteudo_stack"):
                # Muda o QStackedWidget para exibir esta tela como padrão inicial
                painel.conteudo_stack.setCurrentWidget(tela)
                return  # Para após definir a primeira tela — não continua o loop

    # =========================================================================
    # tem_permissao
    # Função auxiliar pública para verificações pontuais de permissão em
    # qualquer parte do código — ex: habilitar/desabilitar um botão específico.
    #
    # Uso:
    #   if Seguranca.tem_permissao("operador", "btn_cadastro"):
    #       ...
    #
    # Parâmetros:
    #   nivel_acesso → nível do usuário logado
    #   recurso      → nome do botão ou tela a verificar
    #
    # Retorna:
    #   True  → o cargo tem permissão de ver/acessar o recurso
    #   False → o cargo não tem permissão
    # =========================================================================
    @staticmethod
    def tem_permissao(nivel_acesso: str, recurso: str) -> bool:

        # Normaliza o nível para evitar problemas com capitalização
        nivel = nivel_acesso.strip().lower() if nivel_acesso else CARGO_PADRAO_DESCONHECIDO

        # Usa o cargo padrão se o nível não for reconhecido
        if nivel not in PERMISSOES:
            nivel = CARGO_PADRAO_DESCONHECIDO

        # Verifica se o recurso está na lista de telas visíveis do cargo
        return recurso in PERMISSOES[nivel]["telas_visiveis"]

    # =========================================================================
    # eh_somente_leitura
    # Verifica se uma tela específica deve ser exibida em modo somente leitura
    # para o cargo informado.
    #
    # Uso:
    #   if Seguranca.eh_somente_leitura("visualizador", "tela_novo_cadastro"):
    #       ...
    #
    # Parâmetros:
    #   nivel_acesso → nível do usuário logado
    #   nome_tela    → nome do atributo da tela a verificar
    #
    # Retorna:
    #   True  → a tela deve ser bloqueada (somente leitura) para este cargo
    #   False → a tela é totalmente interativa para este cargo
    # =========================================================================
    @staticmethod
    def eh_somente_leitura(nivel_acesso: str, nome_tela: str) -> bool:

        nivel = nivel_acesso.strip().lower() if nivel_acesso else CARGO_PADRAO_DESCONHECIDO

        if nivel not in PERMISSOES:
            nivel = CARGO_PADRAO_DESCONHECIDO

        # Verifica se a tela está na lista de somente leitura do cargo
        return nome_tela in PERMISSOES[nivel]["telas_somente_leitura"]