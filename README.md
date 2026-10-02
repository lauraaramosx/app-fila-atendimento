# Sistema de Gerenciamento de Fila de Atendimento

 ## 1\. Descrição

 Aplicação web desenvolvida com **Python, Flask e SQLite** para gerenciamento de filas de atendimento. O sistema permite cadastrar clientes, controlar a ordem de atendimento e acompanhar o status dos atendimentos.

 ## 2\. Funcionalidades

 - Cadastro de clientes;
- Visualização da fila;
- Chamada do próximo cliente;
- Controle de status: **Aguardando, Em Atendimento, Concluído e Cancelado**;
- Prioridade **Normal ou Preferencial**;
- Histórico de atendimentos;
- Atualização automática da fila.

 ## 3\. Tecnologias

 - **Python**
- **Flask**
- **SQLite**
- **HTML5**
- **CSS3**
- **JavaScript**

 ## 4\. Execução

 Crie e ative um ambiente virtual:

```
python -m venv .venv
```

 No Windows:

```
.venv\Scripts\activate
```

 Instale as dependências:

```
pip install -r requirements.txt
```

 Execute a aplicação:

```
python app.py
```

 Acesse no navegador:

```
http://127.0.0.1:5000
```

 ## 5\. Objetivo

 O projeto tem como objetivo aplicar conceitos de **desenvolvimento web, banco de dados, gerenciamento de estados e organização de filas**, utilizando a estrutura **FIFO (First In, First Out)** e prioridade de atendimento.

 ## 6\. Autor

 Projeto acadêmico desenvolvido para fins de estudo e aplicação prática de tecnologias web.
