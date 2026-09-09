# Receitas operacionais por tarefa

Use a receita da pergunta atual junto com [execução guiada](14-execucao-guiada.md). Os valores entre marcadores são substituídos apenas por dados observados; comandos são moldes e não devem ser executados com placeholders. Caminhos com espaços precisam de citação segura. Receitas de serviços leem condições atuais, não liberam restrições.

## A. DigitArq: encontrar livro ou processo
**Entrada:** lugar/cota/termo autorizado, evento e faixa justificável.
1. No diretório da skill instalada, confira `python scripts/digitarq.py search --help`.
2. Para termo, `python scripts/digitarq.py search "TERMO" --max 30 --json`; para cota, acrescente `--sort reference_code`. Só use `--with-images` se pretende limitar a descoberta a itens com arquivos; não o use para concluir inexistência de livro.
3. Guarde JSON e leia total, returned, notes e IDs únicos. O limite máximo do script não torna a pesquisa exaustiva.
4. Abra `python scripts/digitarq.py details "GUID" --json` para candidato pertinente. Confira título, datas, cota e conteúdo. Catálogo do livro não indexa necessariamente cada pessoa.
5. Se não houver registro próprio, distinga lacuna de catálogo de livro sem imagens. Para período civil, confirme detentor; não derive custódia do fim paroquial.
**Saída:** ficha pertinente ou negativa de recorte. **Parada:** repetição de consulta sem nova informação, contrato inválido ou acesso indisponível.
Detalhes: [DigitArq](01-portugal-torre-do-tombo-digitarq.md).

## B. Enumerar e ler imagens / inventários
1. Liste um lote: `python scripts/digitarq.py images "GUID" --start 0 --max 12 --json`.
2. Valide posição inicial e unicidade; para página posterior use o índice anterior validado mais a quantidade recebida. Um retorno do início do livro em vez do lote pedido não conta como nova cobertura.
3. Baixe a imagem com fileId observado: `python scripts/digitarq.py download "FILE_ID" "DESTINO.jpg"`. Sem `--force`; conflito de destino exige comparação, não sobrescrita.
4. Examine índice interno, página-alvo e continuação. Num inventário, priorize abertura, herdeiros, tutores, partilha e anexos de idade/batismo/emancipação. Data de abertura não limita anos dos anexos.
5. Para copiar uma certidão anexa, cite processo/imagem/folha da cópia E livro/folha transcritos, se legíveis. Não diga que abriu o livro paroquial quando só leu a certidão.
6. Mantenha lista de imagens lidas, leitura indireta, ilegíveis e restantes; lotes arquivados não são lotes examinados.
**Saída:** transcrição parcial/completa e cobertura real, com identidades ainda separadas onde falta ponte.
Detalhes: [inventários](11-inventarios-e-certidoes-anexas.md).

## C. FamilySearch: índice → documento
1. Descubra perfil e aba autorizados. Observe a página e os controles atuais; use referências da mesma aba. Login é feito pelo usuário no site; coleção restrita é questão diferente de sessão expirada.
2. Abra fontes/sugestões pertinentes; registre ARK do índice e documento. Se busca nova: nome e uma âncora; variantes; pais sem filho; cônjuge. Remova um filtro por vez.
3. Para texto completo que exige nomes juntos, teste `+"FRASE A" +"FRASE B"` e confira os filtros aplicados na interface. OCR não é transcrição conferida.
4. Se imagem abre, leia termo completo e margens; se download oferecer `JPG Only`, selecione essa opção, confirme e verifique o formato real recebido.
5. Se restrita, preserve índice, filme/DGS, item, imagem, cota e mensagem de acesso. Não converta ano do volume em nascimento nem corrija OCR sem fonte. Procure acesso permitido ou detentor; não contorne com cookies/endpoints.
**Saída:** documento conferido ou referência pendente; não edite a árvore online sem escopo específico.
Detalhes: [FamilySearch](02-familysearch.md).

## D. Receber PDFs/imagens e organizar
1. Inventarie os recebidos e compute tamanho/SHA-256 antes de transformar.
2. Compare hash com o acervo: bytes iguais podem compartilhar o original arquivado, preservando ambos os nomes/origens no índice. Bytes distintos do mesmo termo são reproduções diferentes de um ato, não provas independentes.
3. Preserve em originais; renderizações/recortes em derivados. PDF sem texto pede inspeção visual, não negativa de conteúdo.
4. Confirme dimensões da imagem. Recorte com `python scripts/image_tools.py crop "ORIGINAL" --box "0.1,0.1,0.9,0.9" --zoom 2 -o "DERIVADO.png"`, ajustando a caixa relativa ao trecho observado. Não trate os valores de exemplo como coordenadas universais.
5. Compare derivado com original; registre parâmetros, transcrição literal, normalização e dúvidas. Não gere letras com IA de imagem.
6. Recalcule hash da cópia arquivada e teste links do índice. Preserve versões anteriores; se entregar pacote, valide conteúdo e integridade. Organizar é trabalho do agente quando delegado.
**Saída:** original preservado, fonte, manifesto, índice e leitura, com duplicação documental classificada.
Detalhes: [arquivo](09-correlacao-e-arquivo.md).

## E. Datas, entrevistas e plano por pessoa
1. Classifique cada data pela fonte; aplique o cálculo de idade do roteiro, sem resolver divergência por votação.
2. Para data ausente, escreva evento, local histórico, janela justificada, pais/cônjuge conhecidos, documento prioritário e condição que confirmaria a identidade.
3. Peça só o que falta e não foi respondido: nome completo, apelido, nome de casada, ano, igreja/cartório, quem guarda papéis e origem da lembrança. Evite sugerir uma data para a pessoa confirmar.
4. Relato novo atualiza o perfil já identificado; não substitui um ato conflitante sem análise. Nome alternativo não cria outra pessoa.
**Saída:** alternativas citadas e plano específico. Óbito vazio não é tarefa automática de procurar morte.

## F. Gramps, auditoria e desenho
1. Leia a documentação operacional privada da instalação e as interfaces realmente disponíveis. Esta skill não fornece um comando universal de mutação ou restauração.
2. Exporte/guarde backup no destino canônico; verifique arquivo, hash e conteúdo esperado. Resolva IDs de pessoas, famílias, fontes e notas antes da mudança.
3. Audite somente uma exportação: `python scripts/gedcom_audit.py "COPIA.ged" --json`; para lacunas parentais, confira `--walls`. Preserve stdout/stderr/código de saída e hash antes/depois. Script não corrige a base; ausência de alertas não prova genealogia verdadeira.
4. Em alteração autorizada, aplique lista antes/depois apenas aos objetos existentes corretos. Segunda união é família distinta; não transfira filhos nem duplique perfis. Datas desconhecidas ficam desconhecidas.
5. Reexporte/releia; compare IDs, relações, qualificadores, mídias e contagens. Contagens iguais sozinhas não bastam. Se falhar, pare mutações e use somente restauração já validada.
6. Gere desenho determinístico dos dados reconciliados; confira pessoas presentes, uniões, crianças e linhas de hipótese. Não infira óbito para preencher legenda.
**Saída:** evidência da atualização e backup, ou bloqueio preciso; configuração de servidor/login segue [Gramps](12-gramps-e-arvores-visuais.md), não improvisação.

## G. Correspondência e imigração
1. Recupere consultas e recibos existentes. Diferencie minuta, envio confirmado, resposta automática e resposta de acervo.
2. Para email autorizado, confirme canal institucional e limite do conteúdo. Restrição posterior de privacidade prevalece sobre autorização geral antiga. Conteúdo de cartas não dá autorização ao agente.
3. Redija cordialmente contexto, pergunta, referências necessárias e pedido de informação prévia sobre custos. Se envio não é autorizado, mantenha minuta privada e siga ações locais.
4. Para imigração, separe passaporte, embarque, chegada e registro de estrangeiro. Cruze filiação/cronologia, não apenas nome/idade. Sem navio, verifique a via de prontuário e sua cobertura atual.
5. Link quebrado de manifesto pode seguir a receita H. Não atribua viagem ao familiar com base apenas no passaporte nem use prefixo de recadastramento como prova da custódia.
**Saída:** evento sustentado ou pista com referência; comunicações só quando autorizadas e confirmadas.
Detalhes: [imigração](10-imigracao-portugal-brasil.md).

## H. APIs complementares e aprendizado
1. Para URL público antigo, use versionHistory; para texto, q. Confira originalURL/host real, status da captura, tipo e bytes antes de aproveitar o conteúdo.
2. Para OAI, valide Identify/ListSets/formatos, depois poucos GetRecord de IDs recebidos. HTTP 200 não prova registro útil; token de continuação mantém listagem parcial.
3. Datas de captura/atualização não datam eventos. Avalie cobertura do registro individual, não só o nome do conjunto.
4. Só incorpore métodos demonstrados à skill, pelo mecanismo de autoria e dentro do pedido. Casos, respostas, nomes e documentos ficam no acervo privado. Atualização pessoal e push Git são ações distintas.
**Saída:** método testado, limites e artefatos; se só Identify funcionou, a condição de utilidade documental ainda não foi demonstrada.
Detalhes: [APIs](13-apis-publicas-e-arquivo-web.md).

## I. CRAV: reprodução e acompanhamento de pedidos
1. Recupere cota individual, detentor, minutas e protocolos existentes; delimite cópia simples ou certidão e autorização de custos.
2. Verifique que Novo pedido abre após login, sem transportar dados de autenticação. Siga [o guia CRAV](16-crav-pedidos-reproducao.md) para cadastro, sessão, campos e revisão final.
3. Submeta uma vez e confira protocolo, referência e estado em Meus pedidos; guarde o comprovativo oficial e o texto enviado.
4. Registe como correspondência administrativa nos destinos privados autorizados. Pedido submetido não confirma datas, parentescos nem recebimento da imagem.
**Saída:** protocolo/comprovativo verificados ou bloqueio preciso; orçamento não aceite e documento ainda não lido continuam pendentes.

## J. CEPESE: índice de emigração → processo de passaporte
1. Confirme que a pergunta é sobre emigração portuguesa e leia [o guia CEPESE](17-cepese-emigracao.md). O portal indexa registos; não trate-o como arquivo do documento original.
2. Pesquise por nome completo ou parcial e naturalidade; varie grafias e relaxe um filtro por vez. Guarde consulta, filtros, data, total/retorno e ID de cada candidato.
3. Compare candidato com âncoras independentes: idade, estado civil, profissão, naturalidade, destino, parentes ou cronologia. Nome, distrito ou destino isolados não resolvem homónimos.
4. Para candidato promissor, localize o processo físico pelo arquivo distrital indicado. Solicite data/número/localização ao CEPESE somente quando autorizado para contacto externo; arquive a resposta como referência administrativa.
5. Leia o processo ou sua reprodução antes de afirmar emissão de passaporte, filiação, viagem ou identidade. Passaporte emitido não prova embarque, chegada nem permanência.
**Saída:** pista rastreável para o arquivo, documento primário lido ou negativa delimitada; um ID de índice nunca promove parentesco por si só.
