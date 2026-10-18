# HelpDesk Lite

Sistema de gerenciamento de chamados de suporte técnico desenvolvido em Python e SQLite, com foco em validação de dados, persistência e testes automatizados.

## Funcionalidades

- Cadastro de chamados com título, categoria e prioridade.
- Consulta de chamados por identificador.
- Listagem e filtragem de chamados por status.
- Atualização do status dos chamados.
- Validação de campos obrigatórios e identificadores.
- Validação de categorias, prioridades e status.
- Normalização de categorias e prioridades.
- Persistência de dados utilizando SQLite.
- Testes automatizados com `unittest`.

## Tecnologias

- **Linguagem:** Python 3.13+
- **Banco de dados:** SQLite
- **Testes:** `unittest`
- **Versionamento:** Git e GitHub

## Requisitos

- Python 3.13 ou superior.

O projeto utiliza o módulo `sqlite3`, disponível na biblioteca padrão do Python.

## Como executar

Clone o repositório:

```bash
git clone https://github.com/LipDev-sudo/helpdesk-lite.git
cd helpdesk-lite
```

Execute a aplicação:

```bash
python main.py
```

## Executar os testes

Na raiz do projeto, execute:

```bash
python -m unittest discover -s tests -v
```

A suíte de testes verifica funcionalidades como cadastro, consulta, listagem, atualização de status e validação de entradas.

## Estrutura do projeto

```text
helpdesk-lite/
├── database.py
├── main.py
├── tickets.py
└── tests/
    └── test_tickets.py
```

- `main.py`: fluxo principal e interação com o usuário.
- `tickets.py`: operações e regras de negócio dos chamados.
- `database.py`: acesso e gerenciamento do banco de dados.
- `tests/test_tickets.py`: testes automatizados.

## Objetivo do projeto

Projeto autoral desenvolvido para consolidar conhecimentos em Python, operações com bancos de dados relacionais, validação de entradas, organização de código e testes automatizados.

## Autor

**Hamilton Felipe Soares da Silva**

- GitHub: https://github.com/LipDev-sudo
- LinkedIn: https://br.linkedin.com/in/hamilton-felipe-875054383
- Portfólio: https://lipdev.vercel.app/
