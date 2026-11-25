# LLM Wiki em Open Knowledge Format

Este diretório combina o padrão LLM Wiki descrito por Andrej Karpathy com a
especificação Open Knowledge Format (OKF) v0.3:

- https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- https://github.com/open-knowledge-format/open-knowledge-format/blob/main/SPEC.md

O repositório antigo (`GoogleCloudPlatform/knowledge-catalog`, pasta `okf/`)
parou na v0.2 e aponta para o repositório acima. O resumo da spec, do
repositório e do que mudou da v0.2 para a v0.3 está na página
`wiki/padroes/open-knowledge-format.md`. Em dúvida, vale a `SPEC.md`.

## Ideia central

Mantenha uma wiki persistente em Markdown entre o usuário e suas fontes. Em vez
de reconstruir o conhecimento a partir dos documentos brutos a cada pergunta,
leia as fontes, extraia o que importa e integre esse conteúdo à wiki existente.

A wiki deve acumular valor: novas fontes e novas perguntas podem atualizar
páginas, conexões, comparações e sínteses já existentes.

O usuário seleciona fontes, explora o conteúdo e faz perguntas. O agente mantém
a wiki: resume, organiza, cria relações, atualiza páginas e cuida da
consistência.

## Arquitetura

### `raw/`

Coleção curada de documentos-fonte, como artigos, papers, imagens e arquivos de
dados.

- É a fonte de verdade.
- O agente pode ler seus arquivos, mas nunca deve modificá-los.
- Não faz parte do bundle OKF e, por isso, seus arquivos não precisam seguir o
  formato de documentos de conceito.

### `wiki/`

Bundle de conhecimento OKF v0.3 e diretório de arquivos Markdown gerados e
mantidos pelo agente. Pode conter resumos, páginas de entidades, páginas de
conceitos, comparações, panoramas e sínteses.

- O agente cria e atualiza as páginas.
- O agente mantém referências cruzadas e consistência entre elas.
- O usuário e qualquer consumidor compatível com OKF consultam o resultado.
- A raiz do bundle é `wiki/`; valores iniciados por `/` resolvem a partir dela.
- `raw/` e `output/` ficam **fora** da raiz do bundle. Para o OKF, um caminho
  que aponta para lá (como `../../raw/...`) é um recurso externo: continua
  válido, mas um consumidor OKF não o lê do disco.

### `output/`

Entregáveis pedidos pelo usuário: imagens, anúncios, documentos, planilhas e
qualquer outro arquivo pronto para usar.

- O agente grava aqui todo arquivo que o usuário pedir como resultado.
- Não faz parte do bundle OKF, como `raw/`: um `.md` aqui não precisa de
  frontmatter.
- A wiki registra o pedido num documento de conceito e aponta para os arquivos
  daqui.

### `CLAUDE.md`

Schema operacional usado pelo Claude Code, que carrega este arquivo
automaticamente ao abrir a sessão na raiz do projeto. Define a estrutura, as convenções e os
fluxos seguidos pelo agente. Pode evoluir com o uso, em colaboração com o
usuário. Não faz parte do bundle OKF.

## Documentos de conceito OKF

Na v0.3, um arquivo é **conceito** quando termina em `.md`, não usa um nome
reservado (`index.md`, `log.md`) e tem frontmatter com `type` não vazio. Um
`.md` sem frontmatter ou sem `type` não é conceito: o consumidor o ignora e ele
não quebra a conformidade. Arquivo que não termina em `.md` é **asset**.
Arquivos e pastas começando com `.` (como `.DS_Store`) ficam fora do bundle.

Regra desta wiki, mais estrita que a spec: todo `.md` dentro de `wiki/`, exceto
`index.md` e `log.md`, é um conceito e tem `type`. Não crie `README.md` nem
notas soltas sem frontmatter em `wiki/`. Entregáveis vão para `output/`, não
como asset dentro do bundle.

Cada arquivo representa exatamente um conceito. O caminho sem a extensão `.md`
é o identificador estável desse conceito. Prefira nomes de arquivo descritivos
em `kebab-case`, minúsculos, e nunca dois caminhos que difiram só por
maiúsculas.

Cada documento de conceito deve ser UTF-8 e começar com frontmatter YAML:

```markdown
---
type: Concept
title: Nome legível do conceito
description: Resumo do conceito em uma frase.
resource: https://example.com/recurso-canonico
tags: [tema, contexto]
generated:
  by: claude-code/<versão-do-modelo>
  at: "2026-07-23T12:00:00-03:00"
sources:
  - id: fonte-principal
    resource: https://example.com/fonte
    title: Fonte principal
---

# Visão geral

Conteúdo estruturado e conectado a [outro conceito](/conceitos/outro.md),
conforme a fonte principal.[^fonte-principal]

[^fonte-principal]: Fonte principal

```

### Sintaxe do frontmatter

- O arquivo começa com uma linha exatamente `---`, e o bloco termina na próxima
  linha exatamente `---`.
- O bloco deve parsear como mapping YAML 1.2 (core schema).
- Nunca repita uma chave.
- Ponha entre aspas valores que parecem número ou booleano
  (`okf_version: "0.3"`), além de timestamps e atores em páginas novas.
- Não use tags YAML customizadas.
- Ao editar, não re-serialize valores que você não mudou (mantenha aspas,
  ordem e formato), para o diff ficar pequeno.

### Regras do frontmatter

- `type` é obrigatório, deve ser uma string curta, não vazia e autoexplicativa.
- `title`, `description`, `resource` e `tags` são recomendados quando seus
  valores forem conhecidos.
- `generated` é recomendado para registrar como o conteúdo atual foi produzido
  e quando ocorreu sua última alteração significativa.
- `verified`, `status`, `superseded_by` e `stale_after` são opcionais e devem
  ser usados quando houver confirmação, necessidade de ciclo de vida ou
  política de atualização.
- `sources` é recomendado quando o conceito deriva de fontes identificáveis.
- `description` deve conter uma única frase útil para índices e busca.
- `resource` identifica o recurso canônico descrito pela página; omita-o em
  conceitos abstratos sem recurso correspondente.
- `tags` deve ser uma lista YAML de strings curtas. Um valor escalar vale como
  uma única tag: `tags: a, b` é a tag `"a, b"`, não duas.
- `generated.by` é obrigatório dentro de `generated` e segue a convenção de
  atores: `<producer>/<version>` para agentes e ferramentas, ou
  `<esquema>:<id>`, com os esquemas `human:` (pessoa), `team:` (grupo de
  pessoas) e `process:` (processo automatizado). Outros esquemas são aceitos e
  tratados como não humanos.
- O que o agente escreve leva o próprio agente em `generated.by`, no formato
  `<producer>/<version>`. Use `human:<id>` só para conteúdo escrito ou
  conferido por uma pessoa.
- `generated.at` é o instante da última mudança **de sentido** no conteúdo.
  Correção de formato, espaços ou links não altera `generated.at` nem
  `generated.by`.
- `verified` é uma lista de eventos de verificação, cada um com `by` e `at`,
  ambos obrigatórios (evento sem um deles é ignorado). Um único evento também
  pode ser escrito como um mapeamento sem lista.
- Níveis de confiança: o OKF só considera eventos `verified` **atuais**, com
  `at` igual ou posterior a `generated.at`. Sem evento atual → não verificado;
  só atores não humanos (inclusive `team:`) → confirmado por máquina; algum
  `human:` → revisado por pessoa. Uma mudança de sentido numa página revisada a
  derruba de nível até nova confirmação; avise o usuário quando isso
  acontecer. Eventos antigos ficam no arquivo como histórico.
- Nunca registre verificação que não aconteceu. Não adicione `verified` a
  conteúdo gerado na mesma sessão. Um evento `human:<id>` só entra quando a
  pessoa confirmou o conteúdo, pediu o registro e informou o id; não deduza o
  id do login da máquina.
- Todo campo de tempo (`generated.at`, `verified[].at`,
  `sources[].last_modified`, `usage_window.from`, `usage_window.to` e
  `stale_after`) usa RFC 3339 (perfil da ISO 8601). A v0.3 aceita data-hora
  com fuso (`"2026-07-23T12:00:00-03:00"`) ou só a data (`"2026-07-23"`),
  que significa 00:00 **UTC** — 21:00 da véspera em Brasília. Data-hora sem
  fuso é inválida. Regra desta wiki: use sempre data-hora com fuso
  explícito; data pura só em `last_modified` quando a fonte não informar a
  hora. Os títulos de data do `log.md` usam `YYYY-MM-DD`.
- `status` aceita `draft`, `stable` ou `deprecated`; quando ausente, o
  conceito é considerado `stable`. Qualquer outro valor **não** é `stable`:
  consumidores tiram o conceito do conhecimento atual.
- `superseded_by` é um caminho para o conceito que substitui este e só tem
  sentido com `status: deprecated`.
- `stale_after` é um instante absoluto (nunca um prazo relativo); o conceito
  fica obsoleto quando o momento atual for igual ou posterior a ele. Obsoleto
  significa "conferir de novo", não "falso". Omita o campo quando não houver
  data de revisão conhecida, e nunca escreva um valor que não parseie (o
  consumidor trata como obsoleto).
- Campos adicionais são permitidos em qualquer nível, inclusive dentro de
  `sources`, `generated`, `verified`, `executor` e `attester`. Nomeie os
  **novos** campos desta wiki como `x-r5-<nome>` (versões futuras do OKF nunca
  definirão chaves com prefixo `x-`). Campos já em uso sem o prefixo, como
  `decisions`, ficam como estão. Preserve campos desconhecidos ao editar uma
  página.
- Não invente metadados ausentes apenas para preencher o frontmatter.

Não existe uma taxonomia universal de tipos. Use poucos valores consistentes e
autoexplicativos, como `Source Summary`, `Entity`, `Concept`, `Comparison`,
`Synthesis`, `Playbook`, `Standard`, `Attested Computation` ou tipos
específicos do domínio. Reaproveite os tipos que a wiki já usa.

### Aposentar, mover ou renomear

- Para aposentar um conceito, mantenha o arquivo com o conteúdo e o histórico
  de `verified`, ponha `status: deprecated`, diga o motivo no corpo e, se
  houver substituto, `superseded_by` com o caminho dele.
- Para mover ou renomear, deixe no caminho antigo um conceito curto com
  `status: deprecated` e `superseded_by` apontando o novo caminho, para que
  links e referências guardadas continuem funcionando. Mover não muda o
  sentido: preserve `generated` e `verified`.

### Proveniência e confiança

Quando um conceito for derivado de material externo ou de outro conceito, use
`sources` no frontmatter:

~~~yaml
sources:
  - id: fonte-principal
    resource: https://example.com/fonte
    title: Fonte principal
    author: "human:autor"
    usage_count: 42
    last_modified: "2026-07-23T00:00:00-03:00"
usage_window:
  from: "2026-07-01T00:00:00-03:00"
  to: "2026-07-31T23:59:59-03:00"
~~~

Cada entrada de `sources` deve ter `resource`, que pode ser uma URL absoluta,
um caminho (dentro ou fora do bundle) ou um descritor de escopo que não se
segue, como `todas as consultas do projeto X`. `id`, `title`, `author`,
`usage_count` e `last_modified` são opcionais. `usage_window` é irmão de
`sources` e contextualiza os valores de `usage_count`; uma fonte pode
sobrescrevê-lo localmente.

- `id` deve estar presente sempre que o corpo citar a fonte em nota de rodapé.
- `author` segue a convenção de atores. Use `human:<id>` quando o autor for
  uma pessoa identificável e `team:<id>` quando for um grupo de pessoas
  identificável; se nenhum esquema couber com segurança, omita `author` em vez
  de forçar um valor.
- `last_modified` é quando a própria fonte mudou pela última vez (data de
  publicação ou de revisão informada pela fonte); não confunda com
  `generated.at`, que é quando a página da wiki foi escrita. Sem data na
  fonte, omita o campo.
- Quando `resource` aponta para outro conceito da wiki, a linhagem já está no
  grafo: o consumidor pode ler as `sources` daquele conceito em cadeia.
- Ao citar uma fonte web que muda (repositório, documentação viva), prefira a
  URL fixada numa versão ou commit.

Para atribuir uma afirmação específica a uma fonte, use uma nota de rodapé
com o mesmo identificador de `sources[].id`:

```markdown
O processamento ocorre diariamente.[^fonte-principal]

[^fonte-principal]: Fonte principal
```

O rótulo é a chave de junção com `sources`; nunca use rótulos posicionais
(`[^1]`). Não use uma lista `# Citations` no corpo: é forma da v0.1.

### Autoridade das fontes e conflitos

Nem toda fonte tem o mesmo peso. Ao integrar, comparar ou responder, considere
esta ordem, da mais para a menos autoritativa:

1. documentos normativos ou oficiais de quem define o assunto (regulador,
   especificação, padrão, documentação do próprio produto descrito);
2. documentação técnica de quem implementa ou opera (referência de API,
   changelog, guia de integração);
3. notícias e reportagens;
4. conteúdo de marketing, opinião ou divulgação.

Quando duas fontes divergirem:

- registre as duas afirmações na página, cada uma com sua nota de rodapé;
- diga qual fonte tem mais autoridade e por quê, usando a ordem acima;
- entre fontes do mesmo nível, a mais recente prevalece; marque a afirmação
  superada em vez de apagá-la;
- não apague nem reescreva a afirmação divergente para fazer o conflito sumir.

Quando duas **páginas da wiki** divergirem, a skill `okf-consume` (não a spec)
decide nesta ordem: status (atual vence `deprecated`), nível de confiança,
frescor (`stale_after`) e, por fim, o `generated.at` mais recente.

Não tire conclusões jurídicas, regulatórias ou de conformidade sobre pessoas,
empresas ou produtos a partir das fontes. Quando as fontes sugerirem uma tensão
desse tipo, registre-a como pergunta em aberto, com as citações dos dois lados.

## Corpo, links e citações

- O corpo é CommonMark com tabelas e notas de rodapé `[^rótulo]` do GFM. Não
  dependa de outras extensões.
- Use Markdown estrutural: títulos, listas, tabelas e blocos de código.
- Só `[texto](alvo)` (e links de referência) são links no OKF. `[[wikilinks]]`
  não contam.
- Resolução, igual para links e campos de caminho: valor com esquema
  (`https:`) é URL; valor iniciado por `/` resolve da raiz do bundle
  (`wiki/`); qualquer outro valor resolve **do diretório do arquivo** que o
  contém. Caminhos diferenciam maiúsculas e minúsculas; codifique espaços como
  `%20`.
- As duas formas internas são válidas na v0.3, e a spec não recomenda mais uma
  delas. Estilo desta wiki: links entre páginas com `/` a partir da raiz, como
  `[Conceito](/conceitos/conceito.md)`.
- Campos de caminho (`resource`, `sources[].resource`, `computation`,
  `executor.resource`, `attester.resource` e `superseded_by`): para um alvo
  dentro do bundle, escreva com `/` (`/campanhas/x.md`); um caminho sem `/`
  resolve do diretório do arquivo, não da raiz. Para `raw/`, use o caminho
  relativo ao arquivo, como `../../raw/branding/...`.
- Explique a relação no texto ao redor do link; o link, sozinho, não tipa a
  relação.
- Links quebrados são tolerados pelo OKF, mas devem ser reportados no `LINT` e
  corrigidos quando não representarem conhecimento ainda pendente.
- Afirmações vindas de material externo devem apontar para uma entrada em
  `sources`; quando a atribuição for por afirmação, use uma nota de rodapé
  cujo rótulo corresponda a `sources[].id`.
- Ao citar um arquivo local de `raw/`, use um link Markdown relativo ao arquivo.
  Ao citar uma fonte web, prefira a URL canônica.
- `# Schema`, `# Examples` e `# Computation` têm significado convencional no
  OKF e devem ser usados quando forem adequados ao conceito.

## Computações atestadas

Quando um conceito precisar declarar uma forma sancionada de calcular um valor,
use `type: Attested Computation`, como conceito próprio (um por valor), ligado
por link a partir das páginas que usam o valor.

- `runtime` é obrigatório nesse tipo e define o que `parameters` significam.
- `parameters` é uma lista de `{ name, type, required }`; `name` e `type` são
  obrigatórios, `required` vale `false` quando ausente.
- A computação fica num bloco de código na seção `# Computation` (só um bloco)
  ou num arquivo apontado por `computation`.
- `executor` (`resource` e `receipt`) diz como rodar e que evidência o recibo
  devolve; `attester.resource` aponta para código determinístico (sem LLM) que
  examina o recibo e devolve `{ ok, reason }`.
- Sem `runtime` ou sem `attester`, nenhum valor pode ser apresentado como
  atestado.
- O agente só preenche valores de parâmetros: **nunca escreve nem edita a
  computação**. Copie-a de uma fonte sancionada e cite-a; sem fonte
  sancionada, descreva o valor sem computação e relate a lacuna.

O OKF descreve a computação e como verificá-la, mas não executa o código nem
define seu pacote ou ambiente de execução. `verified` confirma a definição;
a atestação confirma cada execução e não fica gravada no bundle.

Exemplo mínimo:

~~~yaml
---
type: Attested Computation
title: Receita anual
runtime: bigquery
parameters:
  - { name: year, type: integer, required: true }
executor:
  resource: /references/skills/run-query.md
  receipt: [job_id, executed_sql, result]
attester:
  resource: /references/attesters/sql-equality.py
generated:
  by: "human:usuario"
  at: "2026-08-03T12:00:00-03:00"
---

# Computation

```sql
SELECT SUM(amount) AS revenue
FROM finance.recognized_revenue
WHERE fiscal_year = @year
```
~~~

## Operações

### INGEST

Ao processar uma nova fonte adicionada a `raw/`:

1. Leia a fonte sem modificá-la.
2. Discuta com o usuário os principais pontos extraídos.
3. Crie ou atualize os documentos de conceito afetados, incluindo um resumo da
   fonte quando ele tiver valor próprio.
4. Preencha o frontmatter OKF de todo documento criado e atualize
   `generated.at` apenas nas alterações significativas. Preserve `generated.by`
   quando a origem do conteúdo não mudar. Se a alteração mudar o sentido de uma
   página com `verified`, avise o usuário que ela perdeu o nível de confiança.
5. Adicione links entre os conceitos relacionados e citações às fontes.
6. Atualize `wiki/index.md` e os índices de subdiretórios afetados, se existirem.
7. Atualize outras páginas de entidades, conceitos e sínteses afetadas.
8. Registre a operação em `wiki/log.md`.

Uma fonte pode afetar muitas páginas. Preferência deste schema:

- **Uma fonte por vez** (padrão, quando o usuário pede a ingestão de uma fonte):
  siga todos os passos. No passo 2, apresente em poucos itens o que a fonte
  traz de novo, o que confirma e o que contradiz na wiki, e espere o usuário
  antes de escrever.
- **Em lote** (quando o usuário pede várias fontes de uma vez): pule a discussão
  do passo 2, processe as fontes em sequência, da mais para a menos
  autoritativa, e ao final apresente um resumo único com as páginas criadas, as
  atualizadas e os conflitos encontrados.
- **Fonte longa**: leia por partes, seguindo as seções da própria fonte, até o
  fim. Só escreva na wiki depois de ler a fonte inteira; não resuma a partir de
  um trecho.

### QUERY

Ao receber uma pergunta sobre a wiki:

1. Leia `wiki/index.md` para localizar as páginas relevantes.
2. Navegue pelos índices de subdiretórios e links antes de fazer uma busca mais
   ampla.
3. Pesquise e leia os documentos de conceito relevantes.
4. Sintetize uma resposta com citações. Ao usar uma página `draft`,
   `deprecated` (siga `superseded_by`) ou com `stale_after` vencido, diga isso
   na resposta.
5. Produza o formato adequado à pergunta, que pode ser uma página Markdown,
   tabela comparativa, apresentação, gráfico ou canvas.
6. Quando uma resposta, comparação, análise ou conexão tiver valor durável,
   incorpore-a à wiki como um documento de conceito OKF e atualize índice e log.

Consultas úteis também devem contribuir para o acúmulo de conhecimento, em vez
de permanecer apenas no histórico da conversa.

#### Onde ficam os entregáveis: `output/`

Todo arquivo que o usuário pedir como resultado (imagem, anúncio, PDF, planilha,
apresentação, HTML, vídeo, texto pronto para usar) vai para `output/`, na raiz do
projeto, no mesmo nível de `raw/` e `wiki/`. Nunca deixe um entregável só fora do
projeto ou só no scratchpad.

- Se o arquivo precisar ser produzido em outro sistema (um pipeline de build de
  outro projeto, por exemplo), gere lá e **copie o resultado final** para
  `output/`.
- Mantenha os nomes descritivos em `kebab-case`. Quando um pedido gerar vários
  arquivos, eles podem ficar numa subpasta de `output/` com o nome do pedido.
- O documento de conceito que registra o pedido aponta para os arquivos com link
  relativo a partir dele (de `wiki/campanhas/x.md`, por exemplo,
  `../../output/arquivo.png`), com link ou imagem embutida. Esse link sai do
  bundle: é externo para o OKF.

### LINT

Periodicamente, ou quando o usuário pedir, faça uma revisão de saúde e
conformidade da wiki. Verifique, nesta ordem:

**Conteúdo**

1. contradições entre páginas, e se cada conflito segue a regra de
   [autoridade das fontes](#autoridade-das-fontes-e-conflitos);
2. afirmações antigas superadas por fontes mais recentes, e conceitos com
   `stale_after` vencido;
3. lacunas que poderiam ser preenchidas por novas fontes ou pesquisa na web;
4. conceitos importantes mencionados, mas sem página própria;
5. afirmações vindas de fontes sem citação ou com citação ausente.

**Estrutura**

6. páginas órfãs, sem links de entrada;
7. links internos quebrados ou relações sem contexto, e `superseded_by` que não
   resolve;
8. entradas ausentes ou desatualizadas nos índices.

**Conformidade OKF**

9. se todo `.md` de `wiki/` (exceto `index.md` e `log.md`) tem frontmatter YAML
   parseável, sem chave duplicada, e `type` não vazio;
10. se `index.md` e `log.md` são usados somente com seus significados
    reservados: frontmatter só no `index.md` raiz (`okf_version`, `title`,
    `description`, `license`) e nenhum em `log.md` ou nos índices de
    subdiretórios;
11. se todo campo de tempo é RFC 3339 com fuso (ou data pura, onde a regra
    desta wiki permite) e os metadados conhecidos estão consistentes;
12. se `generated`, `verified` (eventos com `by` e `at`), `status` (só os três
    valores), `superseded_by` (só com `deprecated`), `stale_after` e `sources`
    seguem suas convenções, e quais páginas têm `verified` mais antigo que
    `generated.at`;
13. se atores usam `<producer>/<version>` ou `<esquema>:<id>` (`human:`,
    `team:`, `process:`), e se `human:` só aparece para pessoas;
14. se notas de rodapé de atribuição resolvem para um `sources[].id` e se os
    campos de caminho dentro do bundle usam `/`;
15. se `tags` é lista YAML e se chaves de extensão **criadas depois de
    20/11/2026** usam `x-r5-` (as anteriores, como `decisions`, ficam).

Quando possível, rode o validador oficial da skill `okf-generate` (precisa de
Python 3.9+ e PyYAML) e inclua o resultado:

```bash
python3 <caminho-da-skill>/okf-generate/scripts/validate.py wiki
```

Entregue o resultado como um relatório no chat, agrupado nos três blocos acima
e nessa ordem. Para cada achado, diga a página, o problema, as fontes
envolvidas e a correção proposta. Termine com as perguntas que merecem
investigação e as fontes que seria útil adicionar.

O LINT não corrige nada sozinho: espere o usuário dizer quais correções
aplicar. Depois de aplicar, registre o LINT e as correções em `wiki/log.md`. Um
link quebrado não torna o bundle inválido segundo o OKF, mas ainda pode indicar
um problema de manutenção.

## Índices e log

### `wiki/index.md`

Índice raiz do bundle e ponto de entrada para descoberta progressiva. É o único
`index.md` que pode ter frontmatter, e só com metadados do bundle:

```yaml
---
okf_version: "0.3"
title: Nome do bundle
description: Uma frase sobre o escopo do bundle e quando usá-lo.
license: CC-BY-4.0   # SPDX ou caminho para um arquivo de licença; omita se não souber
---
```

Agentes usam `description` para escolher entre bundles. Ao regenerar o índice,
preserve esse frontmatter. Não invente `license`.

Organize as entradas por categorias que emergirem do conteúdo. Cada entrada
deve usar um link relativo e, quando disponível, a `description` do conceito:

```markdown
# Conceitos

- [Nome](conceitos/nome.md) - Resumo do conceito em uma frase.
```

Um `index.md` também pode existir em subdiretórios. Nesses casos, não use
frontmatter, liste conteúdos com links relativos e inclua os subdiretórios
relevantes. Atualize os índices a cada ingestão que afetar seu escopo.

### `wiki/log.md`

Histórico de mudanças do bundle, sem frontmatter, agrupado por data e com as
datas mais recentes primeiro. Entradas antigas são imutáveis; novas entradas
devem ser inseridas no grupo da data correspondente, sem reescrever o
histórico.

Use datas ISO 8601 e um tipo de operação em destaque:

```markdown
# Log de atualizações

## 2026-07-23

- **Ingestão**: Adicionado [nome do conceito](/conceitos/nome.md).
- **Consulta**: Incorporada uma comparação durável à wiki.
- **Lint**: Corrigidos links e metadados inconsistentes.
```

Registre consultas apenas quando produzirem uma alteração durável ou uma
decisão relevante para a manutenção da wiki.

## Conformidade e evolução

Pela v0.3 (§11.1), o bundle está conforme quando:

1. todo bloco de frontmatter de um `.md` sob `wiki/` parseia como mapping YAML;
2. cada `index.md` e `log.md` presente segue sua estrutura reservada.

Um `.md` sem frontmatter ou sem `type` não é conceito e não torna o bundle
não conforme — mas, nesta wiki, é um erro de manutenção (veja a regra da
casa em "Documentos de conceito OKF").

Campos opcionais ausentes, tipos desconhecidos, chaves de extensão, links
quebrados e índices ausentes em subdiretórios não invalidam o bundle. Um
conceito sem `verified` atual é consumível, mas deve ser tratado como não
verificado; um consumidor não deve rejeitá-lo por isso. Valores nulos, string
vazia e lista vazia valem como chave ausente. Não acrescente complexidade antes
que ela seja necessária: o OKF padroniza o intercâmbio, não prescreve taxonomia,
banco, motor de busca, SDK ou plataforma.

Antes da 1.0, uma versão minor do OKF pode trazer mudanças incompatíveis,
listadas na seção "Changes" da spec. Se a especificação-alvo mudar, leia essa
seção, migre o bundle (a skill `okf-generate` traz o roteiro em
`references/migration.md`), atualize `okf_version` no índice raiz, depois este
schema operacional e a página `wiki/padroes/open-knowledge-format.md`, e
registre a migração no log. Em escala moderada, os índices podem ser
suficientes; se a wiki crescer, uma ferramenta de busca local pode ser
adicionada.

### Ferramentas oficiais

O repositório do OKF publica duas skills, instaláveis como plugin no Claude
Code (`/plugin marketplace add open-knowledge-format/open-knowledge-format` e
`/plugin install okf@open-knowledge-format`):

- `okf-generate` — escreve, migra e valida bundles (`scripts/validate.py`);
- `okf-consume` — responde a partir do bundle informando confiança, status,
  frescor e atestação de cada conceito usado.

As regras deste arquivo prevalecem sobre as das skills quando forem mais
estritas (por exemplo, fuso explícito e `type` obrigatório em todo `.md`).
