# HelpDesk Lite

Sistema de chamados de suporte em linha de comando, escrito em Python com SQLite. Permite registrar, listar, consultar e acompanhar o status de chamados de TI sem depender de serviços externos.

## Funcionalidades

- cadastro de chamados com título, descrição, solicitante, categoria e prioridade;
- categorias: `hardware`, `software`, `rede`, `acesso` e `outro`;
- prioridades: `baixa`, `media` (padrão), `alta` e `critica`;
- listagem de todos os chamados ou filtrada por status (`aberto`, `em andamento`, `resolvido`);
- consulta de um chamado pelo ID;
- atualização de status, com validação de ID e de valores permitidos;
- exclusão de chamados, com confirmação;
- uso por subcomandos (`novo`, `listar`, `ver`, `status`, `excluir`) e saída `--json`, além do menu interativo;
- persistência em um arquivo SQLite local (`helpdesk.db`), criado automaticamente.

## Tecnologias

- Python 3.13
- SQLite (módulo `sqlite3` da biblioteca padrão)
- `unittest` para testes

Não há dependências externas.

## Como executar

```bash
git clone https://github.com/LipDev-sudo/helpdesk-lite.git
cd helpdesk-lite
python3 main.py
```

Sem argumentos abre o menu interativo (cadastrar, listar, consultar, atualizar status e excluir). Também pode ser usado por subcomandos:

```bash
python3 main.py novo --titulo "Sem rede" --descricao "Sem acesso à internet" \
  --solicitante "Ana" --categoria rede --prioridade alta
python3 main.py listar --status aberto
python3 main.py listar --json
python3 main.py ver 1
python3 main.py status 1 "em andamento"
python3 main.py excluir 1 --sim
python3 main.py --help
```

Erros de validação saem com código 1; argumentos inválidos, com código 2.

## Testes

```bash
python3 -m unittest discover -s tests -v
```

Os testes usam um banco temporário e não alteram o `helpdesk.db` local. O workflow `.github/workflows/tests.yml` os executa a cada push e pull request na `main`.

## Estrutura

```text
main.py        # menu interativo e subcomandos
tickets.py     # regras de negócio e validações
database.py    # conexão e criação da tabela
tests/         # testes automatizados
```

## Limitações

Projeto de estudo: não há autenticação, múltiplos usuários, interface web nem edição do conteúdo de um chamado (apenas o status).
