# seginf

Exercícios de Segurança da Informação

## Requisitos

 - Python3.12

## Instalação

Crie o ambiente virtual

```sh
python3 -m venv .venv
```

Ative:

Linux:

```sh
. .venv/bin/activate
```

Windows:

**Atenção!** No Windows pode ser necessário mudar a política de execução do usuário! Tente executar o seguinte comando como administrador:

``` ps
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

E ative:

```sh
& .venv/Scripts/activate.ps1
```

Mais detalhe em: <https://learn.microsoft.com/pt-br/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.3>

Instale os pacotes:

```sh
python3 -m pip install -r requirements.txt
```

## Execução

Existem várias formas de executar o servidor:

Python:

```sh
python3 -m at1
```

Flask:

```sh
flask -A at1 run
```

No lugar do `at1` você pode usar o `at2` ou o `at3` para executar os outros exercícios.

## Usando PDM

Caso você tenha o PDM instalado você pode seguir as seguintes instruções:

Instale os pacotes:

```sh
pdm install
```

Execute o servidor:

```sh
pdm run at1
```
