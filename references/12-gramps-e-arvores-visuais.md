# Gramps e árvores visuais

Aplique quando o usuário autorizar migrar ou atualizar sua base genealógica. Mantenha
os documentos e dados de implantação no projeto privado, fora da skill.

## 1. Preparar a migração

1. Faça backup/exportação verificável e inventarie pessoas, famílias, eventos, fontes,
   citações, notas e mídias. Mapeie IDs estáveis e apelidos/nomes de casada para os perfis
   existentes; nome parecido não autoriza fusão. Separe candidatos e vínculos refutados.
2. Gere o formato aceito pela versão instalada e valide-o com o esquema/importador
   correspondente. Prefira o formato nativo do Gramps quando precisar preservar notas,
   confiança, fontes e objetos de mídia. Não pressuponha equivalência integral com GEDCOM.
3. Mapeie eventos sem perder qualificadores: nascimento, batismo, lavratura, emissão,
   casamento civil/religioso e óbito. Preserve declarações familiares e datas conflitantes
   em eventos/notas citados, sem substituir valores por cálculos ou pelo “mais provável”.
   Não crie óbito para representar um campo desconhecido.
4. Confira que o diretório da base usado pelo importador é o mesmo armazenamento
   persistente lido pelo servidor. Importe uma vez numa base nova/vazia; nas atualizações,
   altere apenas os perfis/objetos identificados, evitando reimportação que os duplique.
5. Reexporte e compare contagens, IDs, relações e qualificadores, além de abrir registros
   de controle. Confira caminhos/bytes das mídias. Validação de XML não prova importação,
   e contagens iguais não provam que os parentescos estejam certos.

## 2. Acesso e operação

- Registe a versão instalada e siga a documentação oficial de [Gramps Web](https://www.grampsweb.org/).
  Mantenha acesso privado e sem cadastro público, salvo escopo explicitamente diferente.
- Diferencie cadastro público, primeiro proprietário e login. “Registration is disabled”
  pode ser o fluxo público bloqueado, não impossibilidade de criar o primeiro proprietário.
  Verifique usuários existentes e associação à árvore antes de orientar o primeiro acesso.
  Não recrie a árvore nem habilite cadastro aberto para resolver uma tela errada.
- A senha é definida pelo usuário na própria interface segura. Não a recolha em chat,
  comandos ou logs. Se testar autenticação, use uma base de contas isolada e descartável,
  sem transportar credenciais para relatórios.
- Confira recusa de acesso não autenticado e acesso autenticado à árvore correta, imagens
  e busca. Relate “servidor verificado, interface não verificada” quando não puder observar
  a tela. Não apresente um endereço local como acessível em outro dispositivo.
- Verifique exportação, restauração e diretórios persistentes antes de depender do backup.
  Backup configurado não significa backup executado, íntegro ou disponível fora do host.
  Hospedagem local depende de o host estar disponível; não contrate serviços por inferência.

## 3. Atualização, datas e desenho

- Antes de uma alteração autorizada, preserve a versão anterior e sua origem. Atualize
  nomes alternativos/apelidos no perfil existente; confira que não confundiu homônimos
  nem sufixos de geração. Reindexe quando necessário à versão instalada e confira a busca.
- Faça auditoria por pessoa e por evento: data disponível, tipo de evidência, divergências,
  fonte e próxima busca. Não conte datas calculadas/familiares como assentos próprios obtidos.
- Vincule a cada perfil um plano enxuto: pergunta, janela/local justificados, âncoras,
  documento prioritário e resposta institucional pendente. Não transforme uma consulta
  enviada em tarefa de reenviar a cada rodada.
- Gere visuais a partir da base reconciliada e compare cobertura de pessoas e famílias.
  Preserve cônjuges, filhos e gerações com ligações explícitas; coloque candidatos em
  painel separado ou use linhas/legenda que não os apresentem como ascendência confirmada.
- Prefira texto e conexões determinísticos para árvores densas, com saída vetorial
  editável e PDF/PNG para leitura. Confira nomes repetidos, datas, ramos e legibilidade;
  geração de imagem pode distorcer texto e inventar conexões.
- Legende datas aproximadas/declaradas e campos ausentes sem sugerir falecimento.
  Preserve versões anteriores e entregue um pacote coerente, sem obrigar o usuário a
  recompor arquivos já organizados no projeto.

## 4. Fechamento de novas entradas numa projeção privada

Quando o projeto mantém acervo, Gramps e site privado, trate cada destino explicitamente:
1. Preserve original, fonte, classificação por afirmação e hash; confira os perfis por IDs ativos.
2. Acrescente fontes, notas e mídias com o procedimento transacional documentado na instalação.
   Protocolo, índice, candidato e negativa delimitada não criam fatos vitais. Documento contextual
   sem familiar identificado entra no acervo de contexto, não num evento de viagem.
3. Execute a sincronização imediata, além de qualquer rotina periódica. Verifique fonte no perfil,
   mídia/caminho/checksum e snapshot; mantenha os bloqueios de visitantes e contas pendentes.
4. Guarde recibo e backups antes/depois e atualize índice, diário e manifestos afetados.
   Em falha, declare o destino pendente e retome o mesmo lote idempotente, sem duplicar fontes.

Não edite diretamente o catálogo derivado para simular sincronização. Não aprove sugestões
familiares pendentes por causa desta rotina. Correções editoriais de notas só se replicam quando
o texto corrigido também existe na base; logs técnicos e credenciais não são fontes genealógicas.
