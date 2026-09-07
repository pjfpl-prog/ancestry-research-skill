# Correlação familiar e arquivo documental

Leia ao investigar irmãos, variantes de nomes, documentos contraditórios ou ao preparar
o acervo para conferência. Os exemplos são neutros; os casos reais ficam no projeto.

## 1. Usar a família para resolver a pessoa-alvo

- Pesquise pelo casal parental sem o prenome do filho. Depois varie sobrenomes compostos,
  acentos e grafias; relaxe um filtro por vez. Isso pode revelar filhos omitidos do índice.
- Construa uma matriz: pessoa candidata, pais, avós, cônjuge, datas, naturalidades,
  residência na época, testemunhas e fonte de cada campo. Compare com o alvo.
- Endereço recorrente e testemunhas podem ligar registros de irmãos, mas não são prova
  isolada: várias famílias podem morar no mesmo imóvel. Padrinho não é automaticamente avô.
- Para variantes maternas, procure uma ponte documental: nascimento contemporâneo de um
  filho com nome expandido + óbito/casamento da mãe com cônjuge e filiação concordantes.
  Não explique diferença como sobrenome de casada sem evidência.
- Procure o ato contemporâneo quando encontrar registro tardio. Nascimento, batismo,
  lavratura tardia e emissão de certidão são eventos/datas distintos.
- Havendo pais/cônjuge incompatíveis, registre o candidato separado e a razão da exclusão.
  Campo ausente mantém incerteza; não equivale a incompatibilidade.
- Um filho que declara nascimento no país de origem pode orientar busca de migração dos
  pais, mas a cronologia permanece condicional até confirmar identidade. Não suponha uma
  única viagem nem casamento antes do primeiro filho.

## 2. Avaliar afirmações e dependência documental

Um casamento pode documentar bem o casamento e apenas **declarar** um nascimento de décadas
antes. Um óbito pode documentar o falecimento e informar filiação por terceiro. Imagem legível,
informação correta e identidade demonstrada são avaliações distintas.

Para cada afirmação relevante, registre:

- transcrição literal e normalização separadas; `[?]` no incerto e indicação de leitura parcial;
- estado: comprovada / declarada / calculada / hipótese / tradição / candidato excluído;
- confiança justificada, informante quando conhecido, proximidade ao evento e conflitos;
- documento de origem e relação com outras fontes.

Segunda via, fotografia diferente e índice do mesmo termo são manifestações do mesmo ato.
Duas páginas podem compor um único documento. Um nascimento registrado duas vezes pode
produzir dois atos sobre um evento; avalie se a segunda declaração é independente ou
derivada. Conte separadamente arquivos, atos, eventos e vínculos quando pertinente.

Preserve cada valor divergente e sua origem mesmo depois de resolver a identidade. Um novo
registro pode justificar revisão de confiança: atualize a síntese com a razão, sem apagar
a transcrição anterior. Idade permite cálculo/intervalo natal, não uma data comprovada.
Guarde a idade literal e o método; trate limites de mês/ano explicitamente.

## 3. Cobertura e negativas honestas

Guarde fonte, consulta, filtros realmente aplicados, data de acesso, total informado,
itens retornados e imagens efetivamente lidas. Diferencie:

- sem resultado neste índice ou consulta;
- resultado triado por índice/OCR, imagem ainda não examinada;
- intervalo de imagens examinado, com páginas ausentes/ilegíveis;
- catálogo sem livro do período nesta entrada;
- acesso indisponível ou resposta parcial.

Nenhum desses estados sozinho demonstra inexistência de registro. O fim de um fundo
paroquial não determina a custódia atual do registro civil. Consulte o livro/série corretos
e confirme a entidade detentora. Nomes atuais de municípios e cartórios podem diferir dos
usados no ato.

## 4. Preservação reproduzível

Adapte a organização já usada no projeto. Um padrão possível:

```text
documents/
  originais/      arquivos recebidos ou baixados, sem transformação
  transcricoes/  leitura literal, normalização e dúvidas
  derivados/     recortes, ampliações, contraste, renderizações
  notas/         correlações e metadados
  pesquisas/     consultas, resultados e cobertura
  correspondencia/ mensagens genealógicas autorizadas e recibos
  indice.md      fonte → arquivo → leitura → o que sustenta e o que não sustenta
```

1. Preserve a imagem integral disponibilizada pela fonte. “Original” nesta pasta é o
   arquivo recebido, não posse do livro físico. Inclua continuação, verso e margens do ato.
2. Registre origem, nome recebido, ID de fonte, caminho local, tamanho e SHA-256.
   Captura de tela deve ser identificada como captura, não download integral.
3. Renderize PDF escaneado ou TIFF para leitura quando necessário: texto vazio não
   significa documento vazio. Preserve o arquivo recebido; realce cópias e compare com
   a imagem sem tratamento. Não reconstrua conteúdo de documento com geração de imagens.
4. Não sobrescreva originais ao melhorar leituras. Ligue os derivados à página de origem;
   registre parâmetros/comando quando úteis à reprodução.
5. Cite instituição, jurisdição histórica, tipo, livro, folha frente/verso, termo, ARK/GUID,
   grupo/filme e imagem quando disponíveis. Número do visualizador não é fólio. Campo
   ausente fica “não identificado”; não fabrique uma cota.
6. Guarde metadados e transcrição junto das imagens; não dependa só de um link.

## 5. Correspondência como pista e contatos

Com acesso autorizado, buscas dirigidas em mensagens antigas e anexos podem recuperar
certidões, cartórios e números de livro. Preserve data, remetente, assunto, ID da mensagem
e somente o contexto genealógico necessário. Exclua links personalizados de login, tokens
e dados administrativos alheios à pesquisa.

“Certidão localizada/recebida” em email é pista de recuperação, não substitui a imagem.
Uma correção expressa posterior de cidade/nome deve acompanhar a anotação antiga.

Antes de contato externo, confira o destinatário em fonte institucional atual e redija a
consulta com as âncoras disponíveis. Preserve a autorização e seus limites: localização
e informação não contratam emissão ou busca paga. Registre envio confirmado, não apenas
minuta; não duplique pedidos já enviados. Atualizar a skill não autoriza automaticamente
outra ação pendente de aprovação.

## 6. Entrega do arquivo

- Versione os pacotes sem substituir anteriores. Confira hashes dos originais,
  integridade/CRC do ZIP e os caminhos citados no índice.
- Verifique o limite do canal antes de enviar. Quando necessário, divida em ZIPs
  independentes (por exemplo documentos e ampliações), preservando os caminhos relativos.
  Não reduza a qualidade dos originais para caber nem universalize um limite observado.
- Confira que a união das partes cobre o manifesto, sem omissões/versões conflitantes.
  Explique se devem ser extraídas na mesma pasta e qual índice abrir.
- Separe “preparado”, “envio confirmado pela ferramenta” e “lido pelo destinatário”.
  Entrega não comprova leitura. Não inclua segredos ou links de autenticação.

## 7. Entrevistas e lacunas de datas

Prepare perguntas não indutivas, em ordem de utilidade: quem guarda certidões, nomes de
nascimento/casada e apelidos, datas aproximadas, cartório/igreja, viagens e correspondência.
Aceite respostas parciais e pergunte quem recorda ou qual documento sustenta a resposta.
Não ofereça a data que deseja confirmar como sugestão de memória.
Registe informante, data do relato e ambiguidade literal; “ano A ou B” não vira intervalo
contínuo nem escolha silenciosa. Não volte a pedir informação já recebida.

Atualize o plano por pessoa: evento ausente, janela justificada, local, âncoras, fonte
provável e próximo passo. Separe obter uma data desconhecida de obter o assento próprio
de uma data já declarada noutro ato. Um campo de óbito vazio não indica falecimento:
para pessoas possivelmente vivas, confirme o estado antes de planejar busca de óbito.

## 8. Correspondência útil e devolução de resultados

Abra com contexto breve e agradecimento; peça localização, referência e procedimento,
informando que qualquer custo precisa de autorização prévia, quando esse for o limite.
Um encaminhamento institucional informa por onde continuar, não prova existência ou
inexistência do assento. Diferencie confirmação automática de recebimento de resposta
sobre o acervo. Complemente a mesma conversa apenas quando houver informação nova útil.

Quando a organização do acervo estiver delegada, consolide pastas e versões localmente;
não transfira ao usuário a tarefa de juntar complementos. Para entregar, anexe por um
canal autorizado e verifique o recibo. Caminho local clicável pode não abrir no cliente:
ofereça anexo suportado, sem afirmar entrega ou acesso visual não verificado.
Registe condições de reprodução/licença da fonte; a licença da skill não cobre imagens.
