# HelpDesk Lite

Sistema de gerenciamento de chamados de suporte técnico em Python e SQLite, com menu interativo, subcomandos de linha de comando, histórico de alterações e indicadores. Foco em validação de dados, persistência e testes automatizados.

## Funcionalidades

- cadastro de chamados com título, descrição, solicitante, categoria (`hardware`, `software`, `rede`, `acesso`, `outro`) e prioridade (`baixa`, `media`, `alta`, `critica`);
- listagem com filtros por status, categoria, prioridade e solicitante, busca por texto (título, descrição e solicitante) e ordenação por data ou prioridade;
- consulta de um chamado com datas de criação, atualização e resolução e o **histórico** de alterações;
- edição de título, descrição, solicitante, categoria e prioridade, e atualização de status (`aberto`, `em andamento`, `resolvido`);
- exclusão com confirmação;
- **resumo** com totais por status, prioridade e categoria, pendências de alta prioridade e tempo médio de resolução;
- **exportação** para CSV ou JSON (CSV protegido contra injeção de fórmulas em planilhas);
- validação de campos obrigatórios, identificadores, categorias, prioridades e status, com normalização de maiúsculas e espaços;
- banco SQLite com **migrações automáticas**: um banco criado em versão anterior é atualizado sem perda de dados.

## Tecnologias

- **Linguagem:** Python 3.10 ou superior (testado no CI em 3.10, 3.11, 3.12 e 3.13)
- **Banco de dados:** SQLite (módulo `sqlite3` da biblioteca padrão), sem dependências externas
- **Qualidade:** `unittest`, `ruff` e GitHub Actions (lint, testes em várias versões, instalação do pacote e cobertura mínima de 85%)

## Como executar

```bash
git clone https://github.com/LipDev-sudo/helpdesk-lite.git
cd helpdesk-lite
python main.py
```

Sem argumentos abre o menu interativo. Também pode ser usado por subcomandos:

```bash
python main.py novo --titulo "Sem rede" --descricao "Sem acesso à internet" \
  --solicitante "Ana" --categoria rede --prioridade alta
python main.py listar --status aberto --ordenar prioridade
python main.py listar --busca impressora --categoria hardware --json
python main.py ver 1                      # dados e histórico
python main.py editar 1 --prioridade critica
python main.py status 1 "em andamento"
python main.py excluir 1 --sim
python main.py resumo
python main.py exportar --formato csv -o chamados.csv
python main.py --help
```

Erros de validação saem com código 1; argumentos inválidos, com código 2.

### Banco de dados

Por padrão, os dados ficam em `helpdesk.db` na raiz do projeto. Para usar outro arquivo:

```bash
python main.py --db /caminho/outro.db listar
HELPDESK_DB=/caminho/outro.db python main.py resumo
```

### Instalação como comando (opcional)

```bash
python -m pip install .
helpdesk resumo
```

## Executar os testes

```bash
python -m unittest discover -s tests -v
```

Os testes usam bancos temporários e não alteram o `helpdesk.db` local. O workflow `.github/workflows/tests.yml` roda a cada push e pull request na `main`: lint, testes em Python 3.10 a 3.13, instalação como pacote e cobertura.

## Estrutura do projeto

```text
helpdesk-lite/
├── main.py                  # atalho: python main.py
├── helpdesk_lite/
│   ├── cli.py               # menu interativo e subcomandos
│   ├── tickets.py           # regras de negócio dos chamados
│   └── database.py          # conexão, esquema e migrações
├── tests/                   # testes automatizados
├── pyproject.toml           # pacote (comando `helpdesk`) e configuração do ruff
└── .github/workflows/tests.yml
```

## Limitações

Não há autenticação, múltiplos usuários, anexos nem interface web.

## Objetivo do projeto

Projeto autoral desenvolvido para consolidar conhecimentos em Python, operações com bancos de dados relacionais, migrações de esquema, validação de entradas, organização de código e testes automatizados.

## Autor

**Hamilton Felipe Soares da Silva**

- GitHub: https://github.com/LipDev-sudo
- LinkedIn: https://br.linkedin.com/in/hamilton-felipe-875054383
- Portfólio: https://lipdev.vercel.app/
