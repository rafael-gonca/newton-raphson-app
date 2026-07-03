# Newton-Raphson App

Aplicativo desenvolvido em Python para visualizar e simular o Método de Newton-Raphson utilizado no cálculo numérico para aproximação de raízes de funções.

## Sobre o projeto

Este projeto foi desenvolvido como parte da disciplina de Cálculo I da graduação em Sistemas de Informação.

O objetivo foi criar uma aplicação interativa para demonstrar o funcionamento do método de Newton-Raphson na aproximação de raízes de funções, permitindo acompanhar cada iteração por meio de gráficos e simulações.

---

## Funcionalidades

- Cadastro de funções matemáticas
- Organização por pastas
- Método de Newton-Raphson
- Busca automática do chute inicial utilizando Bolzano
- Simulação passo a passo das iterações
- Visualização gráfica da função
- Zoom e movimentação do gráfico
- Armazenamento de exemplos em arquivo JSON
- Sistema de notas para cada função

---

## Tecnologias

- Python
- Tkinter
- NumPy
- SymPy
- Matplotlib

---

## Instalação

Clone o repositório:

```bash
git clone https://github.com/rafael-gonca/newton-raphson-app.git
```

Entre na pasta:

```bash
cd newton-raphson-app
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
python newton-raphson-app.py
```

---

## Como funciona

1. Cadastre uma função.
2. Escolha um chute inicial manual ou utilize o método de Bolzano.
3. Execute a simulação.
4. Navegue pelas iterações utilizando os botões Avançar e Retroceder.
5. Observe a aproximação da raiz diretamente no gráfico.

## Licença

Este projeto foi desenvolvido para fins acadêmicos.
