# Desenvolvimento de Sistema de Autenticação e Autorização com Banco de Dados

## Descrição

Neste exercício, você deve desenvolver um sistema completo de autenticação e autorização utilizando um banco de dados. O objetivo é criar um sistema que permita aos usuários realizar o login, seja autenticado com sucesso e tenha acesso somente a determinadas páginas com base em suas permissões.

## Requisitos

Crie um banco de dados que armazenará as informações de login e autorização dos usuários. O banco de dados deve conter, pelo menos, as seguintes colunas: **id**, **login**, **senha**, **papel** ou **função do usuário** (por exemplo: *administrador*, *usuário comum*) e *permissões associadas*.

Desenvolva uma página de registro onde os usuários possam criar suas contas. Eles devem fornecer um nome de usuário único, uma senha e selecionar uma função (como administrador ou usuário comum) durante o registro.

Se considerar melhor, o cadastro de usuários pode ser realizado apenas pelo administrador do sistema.

Implemente uma página de login onde os usuários possam inserir suas credenciais para acessar o sistema.

O sistema deve verificar se o nome de usuário existe no banco de dados e se a senha inserida corresponde à senha associada a esse nome de usuário.

Após um login bem-sucedido, redirecione o usuário para uma página personalizada com base na função do usuário. Por exemplo, um administrador pode ser redirecionado para um painel de administração enquanto um usuário comum pode ser redirecionado para uma página de perfil.

Implemente autorização para controlar o acesso dos usuários às páginas. Cada usuário deve ter permissões associadas à sua função. Por exemplo, um administrador pode ter permissão para acessar todas as páginas, enquanto um usuário comum pode ter acesso limitado.

Se um usuário tentar acessar uma página para a qual não tenha permissão, exiba uma mensagem de erro ou redirecione-o para uma página de acesso negado.

Implemente uma funcionalidade de logout que permita ao usuário encerrar sua sessão e retornar à página de login.

## Observações

Você é livre para escolher a linguagem de programação e o sistema de gerenciamento de banco de dados que deseja utilizar.

Certifique-se de que as senhas sejam armazenadas de forma segura no banco de dados, por exemplo, usando técnicas de hash.

Foque na funcionalidade de autenticação e autorização neste exercício.

Você pode usar estilos simples para as páginas, desde que a lógica de login, autorização e redirecionamento funcione corretamente.

## Entrega
Você deve entregar o código fonte do sistema, incluindo todos os arquivos necessários e as instruções para executá-lo localmente.

Além disso, forneça um breve relatório descrevendo as escolhas que você fez durante o desenvolvimento e como o sistema atende aos requisitos listados acima.

Este exercício visa aprofundar suas habilidades de desenvolvimento web, bancos de dados e segurança ao implementar funcionalidades de autenticação e autorização. Boa codificação!
