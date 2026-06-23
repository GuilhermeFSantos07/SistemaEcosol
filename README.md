# Sistema de cadastro Offline-first (Python)

Este é um projeto desenvolvido durante meu estágio no SINE AM com a intenção de simplificar o cadastros de pessoas no sistema ECOSOL, anteriormente era feito manual e depois jogado em um planilha do Exel.

O sistema é capaz de realizar o cadastro de um formulário que foi baseado no papel abaixo. A ideia era simples: transformar o preenchimento manual em algo digital e de forma mais simples, o sistema precisaria além de realizar cadastros de formulários, poder anexar documentos, gerar um documento de comprovação, ter tipos de perfis, ser capaz de gerar relatório em exel, fazer upload dos dados para um banco de dados e o mais importante ter a capacidade de rodar offline.

<p align="center">
  <img width="921" height="1295" alt="image" src="https://github.com/user-attachments/assets/e15beafb-6f17-4340-b6e9-046755b9232e" />
  <img width="921" height="1295" alt="image" src="https://github.com/user-attachments/assets/2711a70e-4ff2-4578-97f5-64d9f620abe5" />
</p>

## 🛠️ Tecnologias e Conceitos Utilizados

* **Python**
* **PyQt6**
* **PostgreSQL**

### Conceitos
* **Teste de software**

## 📋 Funcionalidades

1.  **Login:** Tela de Login dos usuários.
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/37f024f9-9588-4b8f-ac12-7bf7c0f4ba52" />

---

2.  **Cadastro baseado no Formulário manual:** Ao digitar o CNPJ ou CPF ele consulta se existe um cadastro, caso sim sobe um pop-up para caso queira apenas editar os dados, os arquivos são anexados por pasta que é salva com o ID, e também gera um PDF com os dados como uma forma de declaração.
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/07ff9507-0c07-49da-854a-9e6876f65763" />
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/2a3448db-5a81-40f8-bc0e-4d344c27fd68" />

---

3.  **Cadastros Existentes:** Lista os cadastros realizados, tem uma barra de pesquisa que pode alterar o tipo de procura, e também mostra o histórico de alterações
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/6929c1b4-e418-414d-bc3a-4448df35ca56" />

---

4.  **Sincronização:** Realiza a sincronização do banco local com o postgreSQL.
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/1663abd6-49e8-479f-abfc-401356f4eda5" />

---

5.  **Relatórios:** Exibe alguns dados basicos de cadastros e também a opção de exportar alguns dados do banco em exel.
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/aeabbcc3-f40d-4d70-857f-daaf2678d86e" />
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/a7150ee7-0a91-453c-a01b-7fe0c1752cd9" />

---

6.  **Gerenciamento usuários:** Permite a criação de novos usuários assim como a atualização de alguns (existem três: Administrador, Operador e Visualizador).
<img width="1920" height="1032" alt="image" src="https://github.com/user-attachments/assets/02c28d88-bd49-4eff-a3a2-06d7e63f451c" />

