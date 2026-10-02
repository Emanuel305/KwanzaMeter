# KwanzaMeter

> **Gestão financeira pessoal simples, inteligente e adaptada à realidade do Kwanza.**

**KwanzaMeter** é uma aplicação de gestão financeira pessoal desenvolvida para ajudar utilizadores a **registar, organizar, acompanhar e analisar o seu dinheiro**, permitindo controlar receitas, despesas, orçamentos e metas financeiras através de uma interface moderna e intuitiva.

O projeto foi desenvolvido em **Python com Flet**, com suporte para **Android**, persistência local de dados, notificações, geração de relatórios financeiros em PDF, consulta de câmbio e integração com a **Kamba IA**, um assistente financeiro baseado em inteligência artificial.

O objetivo principal do KwanzaMeter é transformar a gestão financeira diária numa experiência mais simples, visual e organizada, permitindo que o utilizador tenha uma visão clara de **quanto recebe, quanto gasta, onde gasta e quais são os seus objetivos financeiros**.

---

## Sobre o projeto

O KwanzaMeter nasceu com a ideia de criar uma aplicação financeira direcionada principalmente para utilizadores que trabalham com **Kwanza (Kz)**.

Em vez de depender de folhas de cálculo ou anotações manuais dispersas, o utilizador pode centralizar a sua informação financeira numa única aplicação.

A aplicação permite:

* Registar receitas;
* Registar despesas;
* Organizar transações por categorias;
* Consultar o histórico financeiro;
* Editar e eliminar transações;
* Criar orçamentos;
* Associar despesas aos respetivos orçamentos;
* Controlar o cumprimento dos orçamentos;
* Receber notificações quando um orçamento é ultrapassado;
* Definir e acompanhar metas financeiras;
* Visualizar informações financeiras através de gráficos;
* Consultar taxas de câmbio;
* Conversar com a Kamba IA;
* Gerar relatórios financeiros mensais em PDF;
* Utilizar a aplicação em dispositivos Android.

---

# Objetivos

O KwanzaMeter foi pensado com vários objetivos principais:

### 1. Organização financeira

Permitir que o utilizador mantenha todas as suas receitas e despesas organizadas num único lugar.

### 2. Controlo dos gastos

Mostrar ao utilizador como o seu dinheiro está a ser utilizado e em quais categorias está a gastar mais.

### 3. Planeamento

Através dos orçamentos e metas, o utilizador pode estabelecer limites e objetivos financeiros.

### 4. Análise

Os dados registados são utilizados para apresentar informações resumidas sobre receitas, despesas, saldo e distribuição dos gastos.

### 5. Assistência inteligente

A integração com a Kamba IA permite que o utilizador tenha uma interface conversacional para fazer perguntas relacionadas com a sua gestão financeira.

### 6. Relatórios

O sistema permite gerar relatórios financeiros mensais em formato PDF para facilitar a consulta e análise dos dados.

---

# Principais funcionalidades

## Autenticação

O KwanzaMeter possui um sistema de autenticação com:

* Login;
* Registo de novos utilizadores;
* Palavra-passe;
* Dados financeiros separados por utilizador;
* Persistência dos dados.

Cada utilizador possui os seus próprios dados financeiros, evitando que as transações de uma conta sejam misturadas com as de outra.

---

# Gestão de transações

As transações são um dos componentes principais do KwanzaMeter.

O utilizador pode criar uma nova transação indicando:

* Tipo;
* Categoria;
* Descrição;
* Valor;
* Data;
* Hora.

Existem dois tipos principais:

### Receita

Representa dinheiro recebido pelo utilizador.

Exemplos:

* Salário;
* Pagamentos recebidos;
* Outros rendimentos.

### Despesa

Representa dinheiro gasto pelo utilizador.

Exemplos:

* Alimentação;
* Transporte;
* Moradia;
* Lazer;
* Educação;
* Saúde;
* Outros.

Cada transação é armazenada com informações estruturadas, permitindo que posteriormente seja utilizada pelo dashboard, orçamentos, relatórios e outros sistemas da aplicação.

---

# Categorias

As transações podem ser organizadas através de categorias.

As categorias atualmente utilizadas incluem:

* Salário
* Alimentação
* Transporte
* Moradia
* Lazer
* Educação
* Saúde
* Outros

A categorização é importante porque permite ao KwanzaMeter compreender a distribuição dos gastos do utilizador.

Por exemplo:

```text
Alimentação → Kz 35.000
Transporte  → Kz 15.000
Lazer       → Kz 10.000
Moradia     → Kz 50.000
```

Esses dados podem posteriormente ser apresentados através de gráficos e utilizados na geração de relatórios.

---

# Dashboard financeiro

O dashboard apresenta uma visão geral da situação financeira do utilizador.

Entre as informações apresentadas estão:

* Total de receitas;
* Total de despesas;
* Saldo disponível;
* Distribuição das despesas;
* Categorias com maior volume de gastos;
* Informações relacionadas com orçamentos;
* Resumo das transações recentes.

O objetivo do dashboard é permitir que o utilizador compreenda rapidamente a sua situação financeira sem precisar consultar cada transação individualmente.

---

# Visualização de dados

O KwanzaMeter utiliza gráficos para transformar os dados financeiros em informações mais fáceis de interpretar.

Um dos exemplos utilizados no projeto é a distribuição percentual dos gastos por categoria.

Uma distribuição de exemplo utilizada durante o desenvolvimento foi:

```text
Moradia       35%
Alimentação   25%
Transporte    15%
Lazer         10%
Outros        15%
```

Os valores apresentados na aplicação são calculados a partir dos dados financeiros registados pelo utilizador.

A utilização de gráficos é suportada pelo:

**Flet Charts**

---

# Sistema de orçamentos

Uma das funcionalidades mais importantes do KwanzaMeter é o sistema de **orçamentos associados às transações**.

O funcionamento foi projetado para que o orçamento não seja apenas um valor independente.

Ele acompanha automaticamente as despesas da categoria correspondente.

### Exemplo

O utilizador cria:

```text
Orçamento:
Categoria: Alimentação
Limite: Kz 50.000
```

Depois regista:

```text
Despesa:
Categoria: Alimentação
Valor: Kz 10.000
```

O orçamento passa automaticamente a apresentar:

```text
Gasto: Kz 10.000
Restante: Kz 40.000
```

Se posteriormente forem registadas mais despesas:

```text
Kz 15.000
Kz 12.000
Kz 8.000
```

O sistema acumula automaticamente os valores da categoria.

---

# Alertas de orçamento

Quando as despesas de uma determinada categoria ultrapassam o orçamento definido, o KwanzaMeter pode emitir uma notificação.

Exemplo:

```text
Orçamento: Kz 50.000
Despesas:  Kz 55.000

Estado:
Orçamento ultrapassado
```

Esta lógica permite que o utilizador seja informado quando ultrapassa o limite definido para determinada categoria.

---

# Orçamentos por período

Os orçamentos são associados a um período de tempo através de uma identificação no formato:

```text
YYYY-MM
```

Por exemplo:

```text
2026-09
2026-10
2026-11
```

Essa abordagem permite manter o histórico dos orçamentos e evita que os valores atuais substituam informações de meses anteriores.

Isso também é importante para a geração de relatórios financeiros históricos.

---

# Metas financeiras

O KwanzaMeter também possui o conceito de **metas financeiras**.

As metas permitem que o utilizador estabeleça objetivos relacionados com o seu dinheiro.

Uma meta pode representar, por exemplo:

```text
Objetivo:
Comprar um computador

Valor pretendido:
Kz 500.000
```

O sistema pode acompanhar o progresso da meta à medida que o utilizador avança em direção ao objetivo.

---

# Kamba IA

Uma das principais características do KwanzaMeter é a **Kamba IA**.

A Kamba foi criada para funcionar como um assistente financeiro integrado na aplicação.

O utilizador pode conversar com a IA e fazer perguntas relacionadas com finanças e gestão do seu dinheiro.

Exemplos de utilização:

```text
"Como posso organizar melhor os meus gastos?"

"Quanto estou a gastar em alimentação?"

"Como posso controlar melhor o meu orçamento?"

"Quais são as minhas principais categorias de despesas?"
```

A ideia é tornar a aplicação mais interativa, permitindo que o utilizador não dependa apenas de gráficos e números.

---

# Arquitetura da Kamba IA

A Kamba IA utiliza uma arquitetura separada entre a aplicação e o servidor.

A aplicação Flet envia a mensagem para um backend desenvolvido com **FastAPI**.

Fluxo simplificado:

```text
KwanzaMeter
     |
     v
FastAPI Backend
     |
     v
Groq API
     |
     v
Modelo de IA
     |
     v
Resposta
     |
     v
KwanzaMeter
```

O backend possui endpoints como:

```text
/health
/kamba
```

Também existe suporte para conversas separadas através de um identificador de conversa.

Cada conversa pode possuir o seu próprio histórico.

---

# Segurança da API da IA

Uma decisão importante da arquitetura foi **não colocar a chave da Groq dentro da aplicação Android**.

A chave da API permanece no backend.

O fluxo é:

```text
APK
  |
  v
Backend Kamba
  |
  v
Groq
```

Em vez de:

```text
APK
  |
  v
Groq diretamente
```

Isso evita expor diretamente a chave da API dentro do APK distribuído.

---

# Backend

O backend da Kamba IA foi desenvolvido utilizando:

* Python;
* FastAPI;
* Uvicorn;
* Groq API.

Durante o desenvolvimento existe suporte para execução local:

```text
http://127.0.0.1:8000
```

No Android, a aplicação utiliza o backend hospedado.

O backend foi disponibilizado através da infraestrutura do **Render**.

A aplicação também possui uma verificação de saúde através do endpoint:

```text
/health
```

---

# Conversão de moeda

O KwanzaMeter possui integração para obtenção de taxas de câmbio.

A aplicação utiliza uma API externa para consultar a taxa de câmbio e converter valores com base no Kwanza.

A chave utilizada pela API é armazenada através de variável de ambiente:

```text
EXCHANGE_RATE_API_KEY
```

O projeto utiliza `python-dotenv` para trabalhar com variáveis de ambiente durante o desenvolvimento.

---

# Relatórios financeiros em PDF

O KwanzaMeter possui um sistema de geração de **relatórios financeiros mensais em PDF**.

O relatório pode apresentar:

* Nome da aplicação;
* Mês e ano;
* Data de geração;
* Total de receitas;
* Total de despesas;
* Saldo;
* Gastos por categoria;
* Orçamentos;
* Estado dos orçamentos;
* Transações do mês;
* Paginação;
* Rodapé.

Um relatório pode apresentar informações semelhantes a:

```text
RELATÓRIO FINANCEIRO

Outubro de 2026

Receitas:  Kz 250.000
Despesas:  Kz 175.000
Saldo:     Kz 75.000
```

Os relatórios são gerados através da biblioteca:

**ReportLab**

No Android, o ficheiro pode ser disponibilizado através do sistema de seleção/gravação de ficheiros do Flet.

---

# Notificações Android

O KwanzaMeter possui integração com notificações Android.

As notificações são utilizadas principalmente para informar o utilizador sobre eventos financeiros importantes.

Um dos principais casos de utilização é o alerta de orçamento ultrapassado.

A aplicação utiliza:

```text
flet-android-notifications
```

Também foi configurada a permissão Android:

```text
POST_NOTIFICATIONS
```

---

# Interface

O KwanzaMeter foi desenvolvido com foco numa interface:

* Moderna;
* Simples;
* Limpa;
* Responsiva;
* Adaptada para dispositivos móveis.

Durante o desenvolvimento, a identidade visual passou por diferentes versões. A direção mais recente utiliza uma **paleta verde suave**, procurando transmitir uma aparência mais limpa e agradável para uma aplicação financeira.

A aplicação foi inicialmente desenvolvida com uma abordagem mobile-first.

---

# Tecnologia principal: Flet

A interface do KwanzaMeter é construída com **Flet**, permitindo desenvolver aplicações multiplataforma utilizando Python.

Isso permite que grande parte da lógica e da interface sejam desenvolvidas numa única linguagem.

O projeto utiliza Flet para:

* Interface gráfica;
* Navegação;
* Formulários;
* Botões;
* Listas;
* Diálogos;
* Seletores;
* FilePicker;
* Integração Android.

A versão utilizada durante a etapa atual do projeto é:

```text
Flet 0.86.5
```

---

# Suporte Android

O projeto foi preparado para ser compilado como aplicação Android.

Configurações atuais:

```text
Produto: KwanzaMeter
Versão: beta
Package: com.lasttime
Android Min SDK: 24
Android Target SDK: 35
```

O projeto já passou pelo processo de geração do APK e instalação em dispositivo Android durante o desenvolvimento.

Também foram corrigidas questões relacionadas com:

* Core-library desugaring;
* Dependências Python;
* Configuração do build;
* Inclusão das bibliotecas necessárias no APK.

---

# Persistência dos dados

O KwanzaMeter utiliza persistência de dados através de ficheiros JSON.

Os dados dos utilizadores são armazenados numa estrutura semelhante a:

```json
{
    "utilizador": {
        "password": "...",
        "transacoes": [],
        "orcamentos": []
    }
}
```

O sistema possui funções responsáveis por:

* Carregar dados;
* Guardar dados;
* Criar utilizadores;
* Migrar estruturas antigas;
* Carregar transações;
* Guardar transações;
* Carregar orçamentos;
* Guardar orçamentos.

O projeto também possui lógica para determinar o caminho apropriado do ficheiro de dados, incluindo suporte ao ambiente Windows através de `APPDATA`.

---

# Arquitetura geral

De forma simplificada, o KwanzaMeter pode ser representado assim:

```text
                    +----------------------+
                    |      KwanzaMeter     |
                    |      Flet / Python   |
                    +----------+-----------+
                               |
          +--------------------+--------------------+
          |                    |                    |
          v                    v                    v
   Dados locais          APIs externas       Backend Kamba
     / JSON             Câmbio / etc.           FastAPI
                                                   |
                                                   v
                                               Groq IA
```

No lado da aplicação encontram-se as funcionalidades relacionadas com:

```text
Autenticação
     |
     +-- Transações
     +-- Orçamentos
     +-- Metas
     +-- Dashboard
     +-- Relatórios
     +-- Câmbio
     +-- Kamba IA
```

---

# Estrutura do projeto

A estrutura atual do projeto está organizada aproximadamente desta forma:

```text
KwanzaMeter/
|
+-- assets/
|   +-- image/
|   +-- icon.png
|
+-- kamba_backend/
|   +-- .env
|   +-- requirements.txt
|   +-- server.py
|
+-- .env
+-- colors.py
+-- main.py
+-- pyproject.toml
+-- README.md
```

### `main.py`

É o principal ficheiro da aplicação.

Contém:

* Interface;
* Navegação;
* Autenticação;
* Gestão de transações;
* Orçamentos;
* Dashboard;
* Metas;
* Comunicação com a Kamba;
* Relatórios;
* Integrações externas.

### `colors.py`

Centraliza elementos relacionados com a identidade visual e cores do projeto.

### `kamba_backend/server.py`

Contém o servidor FastAPI responsável pela comunicação entre a aplicação e a IA.

### `pyproject.toml`

Contém as configurações do projeto Flet e as suas dependências.

### `assets/`

Contém recursos visuais utilizados pela aplicação.

---

# Dependências

Entre as principais dependências utilizadas pelo projeto encontram-se:

```text
flet
flet-charts
flet-android-notifications
requests
python-dotenv
reportlab
```

| Tecnologia                 | Utilização                                    |
| -------------------------- | --------------------------------------------- |
| Python                     | Linguagem principal                           |
| Flet                       | Interface gráfica e aplicação multiplataforma |
| Flet Charts                | Gráficos financeiros                          |
| Flet Android Notifications | Notificações Android                          |
| Requests                   | Comunicação HTTP                              |
| python-dotenv              | Variáveis de ambiente                         |
| ReportLab                  | Geração de PDFs                               |
| FastAPI                    | Backend da Kamba                              |
| Uvicorn                    | Servidor ASGI                                 |
| Groq                       | Infraestrutura de IA                          |

---

# Variáveis de ambiente

Informações sensíveis não devem ser armazenadas diretamente no código-fonte.

O projeto utiliza variáveis de ambiente para informações como:

```text
EXCHANGE_RATE_API_KEY
GROQ_API_KEY
```

O ficheiro `.env` deve permanecer fora do controlo de versão quando contém chaves privadas.

Exemplo:

```env
EXCHANGE_RATE_API_KEY=sua_chave
GROQ_API_KEY=sua_chave
```

> **Nunca publique chaves de API reais no GitHub.**

---

# Execução local

Para executar o projeto localmente, é necessário ter Python instalado.

Clone o repositório:

```bash
git clone https://github.com/SEU-USUARIO/KwanzaMeter.git
```

Entre na pasta:

```bash
cd KwanzaMeter
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

ou utilize o sistema de dependências definido no `pyproject.toml`.

Depois execute:

```bash
flet run main.py
```

---

# Executar o backend Kamba

O backend local pode ser executado através do Uvicorn.

Exemplo:

```bash
uvicorn server:app --host 127.0.0.1 --port 8000
```

Depois pode ser verificado através de:

```text
/health
```

Durante o desenvolvimento, a aplicação Flet pode comunicar com:

```text
http://127.0.0.1:8000
```

Enquanto a versão Android utiliza o backend remoto configurado para o projeto.

---

# Fluxo de utilização

O fluxo básico da aplicação pode ser representado assim:

```text
                 KwanzaMeter
                      |
              +-------+-------+
              |               |
           Login           Cadastro
              |               |
              +-------+-------+
                      |
                  Dashboard
                      |
        +-------------+-------------+
        |             |             |
   Transações    Orçamentos       Metas
        |             |             |
        +-------------+-------------+
                      |
              Análise financeira
                      |
             +--------+--------+
             |                 |
         Relatórios         Kamba IA
             |                 |
             +--------+--------+
                      |
                 Decisões do
                  utilizador
```

---

# Exemplo de utilização

Imagine que um utilizador recebe:

```text
Salário:
Kz 250.000
```

Durante o mês regista:

```text
Alimentação → Kz 40.000
Transporte  → Kz 20.000
Lazer       → Kz 15.000
Educação    → Kz 10.000
Moradia     → Kz 50.000
```

O KwanzaMeter pode utilizar esses dados para calcular:

```text
Receitas:
Kz 250.000

Despesas:
Kz 135.000

Saldo:
Kz 115.000
```

Ao mesmo tempo, o sistema pode acompanhar os orçamentos definidos para cada categoria.

---

# Relacionamento entre funcionalidades

Um dos princípios importantes do projeto é que as funcionalidades não funcionam de forma completamente isolada.

Por exemplo:

```text
Nova despesa
     |
     v
Categoria
     |
     v
Transação armazenada
     |
     +--------------> Dashboard
     |
     +--------------> Orçamento
     |
     +--------------> Relatório PDF
     |
     +--------------> Estatísticas
     |
     +--------------> Kamba IA
```

Assim, uma única transação pode contribuir para diferentes partes do sistema.

---

# Filosofia do projeto

O KwanzaMeter não foi pensado apenas como uma calculadora de despesas.

A proposta é criar um pequeno **ecossistema de gestão financeira pessoal**, onde os dados introduzidos pelo utilizador podem ser utilizados para:

```text
Registar
   |
Organizar
   |
Analisar
   |
Planejar
   |
Acompanhar
   |
Compreender
```

A Kamba IA complementa esse processo através de uma interface conversacional.

---

# Tecnologias utilizadas

### Frontend / Aplicação

* Python
* Flet
* Flet Charts
* Flet Android Notifications

### Backend

* Python
* FastAPI
* Uvicorn

### Inteligência Artificial

* Groq API
* Modelo `openai/gpt-oss-120b`

### Dados

* JSON
* Persistência local

### APIs

* ExchangeRate-API
* Groq API

### Relatórios

* ReportLab

### Plataforma

* Windows
* Android

### Configuração

* `pyproject.toml`
* `.env`
* Python 3.13

---

# Estado atual do projeto

O KwanzaMeter encontra-se em fase **Beta**.

A aplicação já possui uma base funcional composta por:

* Sistema de autenticação;
* Gestão de transações;
* Categorias;
* Dashboard;
* Orçamentos;
* Ligação entre orçamentos e despesas;
* Alertas de orçamento;
* Metas;
* Kamba IA;
* Backend FastAPI;
* Integração Groq;
* Consulta de câmbio;
* Notificações Android;
* Geração de relatórios PDF;
* Suporte Android;
* Persistência de dados;
* Configuração de build para APK.

O projeto continua em desenvolvimento, com foco em melhorar a experiência do utilizador, estabilidade, desempenho e funcionalidades financeiras.

---

# Possíveis evoluções

A arquitetura atual permite que o KwanzaMeter continue a evoluir.

Entre as áreas que podem receber melhorias estão:

* Melhor análise financeira;
* Mais tipos de gráficos;
* Evolução das metas;
* Melhorias na Kamba IA;
* Mais funcionalidades de relatórios;
* Melhor sincronização de dados;
* Melhorias de segurança;
* Expansão da plataforma;
* Melhor experiência de utilização no Android.

---

# Segurança e privacidade

O projeto considera a proteção das credenciais e das chaves de API como parte importante da arquitetura.

As chaves de serviços externos devem permanecer em variáveis de ambiente e, especialmente no caso da Kamba IA, a chave da Groq não deve ser distribuída dentro do APK.

O ficheiro `.env` não deve ser enviado para um repositório público quando contém credenciais reais.

---

# Tecnologias e arquitetura resumidas

```text
+---------------------------------------------+
|                 KwanzaMeter                 |
|                                             |
|              Python + Flet                  |
|                                             |
|  +--------+ +------------+ +------------+  |
|  | Login  | | Transações | | Orçamentos |  |
|  +--------+ +------------+ +------------+  |
|                                             |
|  +--------+ +------------+ +------------+  |
|  | Metas  | | Dashboard  | | Relatórios |  |
|  +--------+ +------------+ +------------+  |
|                                             |
|                 Kamba IA                    |
+---------------------+-----------------------+
                      |
                      v
              +---------------+
              |    FastAPI    |
              |    Backend    |
              +-------+-------+
                      |
                      v
                +----------+
                |   Groq   |
                |    IA    |
                +----------+
```

---

# Licença

Este projeto pode utilizar uma licença definida pelo autor do repositório.

Exemplo:

```text
Copyright © 2026 KwanzaMeter
```

A licença definitiva deve ser definida de acordo com a forma como o projeto será distribuído.

---

# Autor

**Emanuel Gomes**

Projeto desenvolvido como uma aplicação de gestão financeira pessoal utilizando Python, Flet e tecnologias de inteligência artificial.

---

# KwanzaMeter

> **Organize o seu dinheiro. Acompanhe os seus objetivos. Compreenda as suas finanças.**

O KwanzaMeter procura unir **gestão financeira, visualização de dados, automação e inteligência artificial** numa única aplicação, tendo o Kwanza como moeda principal e uma experiência pensada para dispositivos móveis.

---

## Contribuição

Sugestões, correções e melhorias podem contribuir para a evolução do projeto.

Se o projeto for disponibilizado publicamente, os interessados poderão:

```text
1. Fazer Fork
2. Criar uma Branch
3. Implementar alterações
4. Fazer Commit
5. Abrir um Pull Request
```

---

## Resumo

**KwanzaMeter** é uma aplicação de gestão financeira pessoal construída com **Python + Flet**, que combina:

**Transações**

**Análise financeira**

**Orçamentos**

**Metas**

**Relatórios PDF**

**Câmbio**

**Notificações**

**Kamba IA**

**Android**

num único ecossistema.

O projeto foi concebido para tornar a gestão financeira mais organizada, acessível e inteligente, oferecendo ao utilizador ferramentas para acompanhar o seu dinheiro e compreender melhor os seus próprios dados financeiros.
