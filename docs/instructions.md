# Instruções

Estas são as suas instruções para poder ajudar o usuário nas demandas dele.

## Ponto principal

O usuário vai lhe reportar através das perguntas o que está ocorrendo:

* Erros: Irá te pedir para ler o arquivo docs/errors.md
* Melhorias: Irá te pedir para ler o arquivo docs/upgrades.md

## Instruções de escrita de código

Regras inegociaveis:

* Sempre ative o ambiente virtual.
* Siga o padrão de de escrita da convenção PEP8.
* Use o clean code.
* Sempre que possível, utilize a Programação orientada a objetos.
* Nomes de funções e classes que deixam claras seus objetivos, sempre em inglês, seguindo a convenção de camelCase para Classes e snake_case para funções.
* Variáveis também devem ter nomes claro, assim como os
* retornos das mesmas devem garantir a tipagem correta.
* Documente o código de forma clara.
* Link da documentação: https://peps.python.org/pep-0008/

## Pós processamento do pedido do usuário

  * Analise os erros de tipagem com mypy e Pylance;

  * Com o ambiente virtual ativado e na raiz do projeto, rode o comando:

  ```bash
  flake8 --exclude venv > flake_errors.txt
  ```

  * Se for possível, corrija com o autopep8, caso não funcione, corrija manualmente.

  * Analise o arquivo de erros do flake novamente,
  e corrija os erros reportados pelo Flake.

  Refaça o container com os seguintes comandos:

  ```bash
  docker compose down -v && sleep 10
  ```

  ```bash
  docker image rm unipost-app: latest && sleep 5
  ```

  ```bash
  docker system prune && sleep 5 && docker builder prune
  ```

  ```bash
  docker compose up --build -d
  ```
