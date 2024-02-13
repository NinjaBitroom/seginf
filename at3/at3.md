# Título: Desenvolvimento de Sistema de Transferência Bancária com Login Simples

## Descrição:

Neste exercício, você deve aprimorar o sistema de login que desenvolveu anteriormente, adicionando a capacidade de realizar transferências entre usuários logados, simulando uma conta bancária básica.

## Requisitos:

Utilize o sistema de login que você desenvolveu no exercício "Desenvolvimento de Sistema de Login com Banco de Dados" como base.
Amplie o banco de dados para incluir informações adicionais para cada usuário, como saldo da conta bancária.
Para o cadastro da conta bancária, pense em algo simples, como:

 - **Número da Conta**: Um número único atribuído à conta bancária.
 - **Tipo de Conta**: O tipo de conta bancária, como conta corrente, poupança, etc.
 - **Agência**: O número da agência bancária onde a conta está registrada.
 - **Saldo Inicial**: O valor inicial depositado na conta.
 - **Histórico de Transações**: Um registro das transações anteriores feitas na conta, incluindo depósitos, saques, transferências, etc.


Após um login bem-sucedido, redirecione o usuário para uma página que mostra os dados da sua conta bancária e saldo atual.
Implemente uma funcionalidade que permita ao usuário logado realizar transferências para outro usuário. Para isso, você deve incluir um formulário onde o usuário possa inserir a conta do usuário de destino e o valor da transferência.
Ao realizar uma transferência, verifique se o usuário tem saldo suficiente para a transação. Se o saldo for insuficiente, exiba uma mensagem de erro.
Atualize os saldos das contas dos usuários envolvidos na transferência.
Após uma transferência bem-sucedida, exiba uma mensagem de confirmação e atualize os saldos exibidos nas páginas relevantes.

## Observações:

Continue utilizando a linguagem de programação e o sistema de gerenciamento de banco de dados que você escolheu anteriormente.
Certifique-se de implementar validações adequadas para garantir que as transferências sejam feitas apenas entre usuários logados e que os saldos sejam atualizados corretamente.
Foque na funcionalidade de transferência bancária neste exercício. Você pode manter os estilos simples das páginas, desde que a lógica de transferência e atualização de saldos funcione corretamente.

## Entrega:
Você deve entregar o código fonte atualizado do sistema, incluindo todos os arquivos necessários e as instruções para executá-lo localmente.
Além disso, forneça um breve relatório descrevendo como você implementou a funcionalidade de transferência, as escolhas feitas durante o desenvolvimento e como o sistema atende aos requisitos listados acima.
Este exercício visa expandir suas habilidades de desenvolvimento web, bancos de dados e lógica de programação ao implementar uma funcionalidade de transferência bancária em um sistema com autenticação básica. Boa codificação!