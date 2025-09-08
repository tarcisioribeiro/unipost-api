### 1.2. Funcionalidade de Webhook

A API deve expor um endpoint de webhook que reaja a um sinal externo para atualizar o status de aprovação de um texto. Este endpoint deve receber o id do texto e um status (True para aprovado, False para negado/regerado) e atualizar o campo is_approved no modelo Text correspondente.