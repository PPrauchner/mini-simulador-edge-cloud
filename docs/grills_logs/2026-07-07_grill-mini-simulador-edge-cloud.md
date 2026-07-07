# Log de Sessão — Grill with Docs

**Projeto:** Mini-Simulador: Alocação de Tarefas em Edge-Cloud (Desafio técnico para bolsa — AI Horizon Labs)
**Data de início:** 2026-07-07 12:41 (-03)
**Fonte da sessão:** `docs/bolsa.jpeg` (brief oficial) + `docs/transcricao_audios.md` (áudios do coordenador explicando a intenção real)

> Este arquivo é atualizado a cada iteração da sessão. Registra todas as perguntas
> e respostas, mais as decisões que forem cristalizando em `CONTEXT.md` / `docs/adr/`.

---

## Material de origem (resumo)

### Brief oficial (imagem)
- **Título:** Mini-Simulador — Alocação de Tarefas em Edge-Cloud.
- **Chamada:** "Construa um mini-simulador em Python para decidir onde executar tarefas
  em uma infraestrutura Edge-Cloud."
- **Diagrama:** Borda 1 ⇄ Nuvem ⇄ Borda 2, com "Tarefas" fluindo entre borda e nuvem.
- **1. Objetivo:** protótipo simples de alocação de tarefas entre servidores de borda e nuvem.
- **2. Entregáveis:** repositório público no GitHub + vídeo de apresentação explicando o projeto.
- **3. Será avaliado:** clareza da lógica; organização do código; capacidade de análise.
- **4. Importante:** não é obrigatório concluir tudo; classificação pela avaliação do coordenador,
  considerando a qualidade dos entregáveis.
- **Prazo:** 07/07/2026 às 23h59. **Envio:** paulosilas@unipampa.edu.br.

### Áudios do coordenador (intenção real)
- Ferramenta de **simulação em tempo discreto** (o tempo avança em unidades discretas).
- Modela **infraestrutura** (estações radiobase, servidores) e **aplicações**.
- Uma entidade "aplicação", quando instanciada, gera várias aplicações que são hospedadas
  em **servidores** para serem executadas.
- A decisão de **qual aplicação vai em qual servidor** deve ser **programática** — permitir
  construir **diversos algoritmos** de posicionamento.
- Como há liberdade de algoritmos, é preciso uma **estrutura de monitoramento** para
  **comparar estratégias**.

---

## Perguntas e Respostas

### Q1 — Unidade alocável: Tarefa ou Aplicação?
Conflito de fontes: o brief diz sempre "Tarefa"; o áudio só diz "aplicação". Três leituras:
(1) mesmo conceito; (2) Aplicação é *fonte* que emite Tasks ao longo do tempo; (3) Aplicação
é a unidade e "Tarefa" foi simplificação do brief.

**Recomendação:** leitura 1 no MVP, canonizando **Task** (termo do brief oficial).

**Resposta do usuário:** MVP na leitura 1; se sobrar tempo, evoluir para a leitura 2
(Application como gerador de Tasks). Precisa ser um trabalho bem feito e útil.

**Decidido:** unidade alocável canônica = **Task**. "Application" fica reservado para um
conceito futuro (fonte que emite Tasks). Registrado em `CONTEXT.md`.

---

### Q2 — Modelo de infraestrutura: Server, Borda vs Nuvem
(a) Estação radiobase é entidade de primeira classe? (b) Que atributos distinguem Borda de
Nuvem — capacidade escalar única + latência, ou um segundo eixo de recurso (ex.: memória)?

**Recomendação:** (a) descartar estação radiobase — o servidor de borda já representa o site.
(b) **um recurso escalar (unidades de computação) + latência**; investir a "riqueza" na
dimensão **temporal** (Task ocupa capacidade por uma duração em ticks e libera), não num
segundo eixo de recurso. É onde moram as métricas de análise e é o que o áudio (tempo
discreto) pediu.

**Resposta do usuário:** (a) concorda em descartar. (b) "Sim" ao recurso único + modelo temporal.

**Decidido:** sem estação radiobase. **Server** = capacidade (inteiro de unidades de
computação) + latência; roda Tasks concorrentes enquanto Σ demanda ≤ capacidade. **Task** =
demanda (default 1) + duração (ticks). Riqueza vem do tempo. Termos Server/Edge/Cloud
registrados em `CONTEXT.md`.

---

### Q3 — Ciclo de vida da Task e loop de cada tick
(a) Chegada em lote (t=0) vs ao longo do tempo (`arrival`); (b) estados do ciclo de vida;
(c) sob contenção, esperar (fila) vs rejeitar.

**Recomendação:** (a) lista fixa de Tasks, cada uma com tick de `arrival` (ainda leitura 1);
(b) `PENDING → RUNNING → DONE`; (c) **esperar** (fila) — gera métrica de tempo de espera.
Loop do tick: chegadas → alocação (Q4) → progresso/liberação → métricas. Latência entra no
tempo de resposta: `resposta = espera + latência + duração`.

**Resposta do usuário:** "Concordo com os 3".

**Decidido:** chegada por `arrival`; ciclo PENDING→RUNNING→DONE; contenção = esperar na fila;
`resposta = espera + latência + duração`. **Tick** registrado em `CONTEXT.md`.

---

### Q4 — Interface do algoritmo de alocação (núcleo)
(a) Uma Task por vez vs em lote; (b) assinatura e o que enxerga; (c) stateless vs com estado.
Recomendação inicial foi por-tarefa; usuário questionou "por que não em lote?".

**Recomendação (revisada):** interface **em formato de lote** `place(pending, servers) ->
list[(Task, Server|None)]` com base **`GreedyStrategy`** que reduz a `place_one` por Task.
Simples herdam a base (trivial); ambiciosas sobrescrevem o lote (otimização global). Motor
valida viabilidade. `None` = esperar de propósito (aceito). Destrava a comparação
heurística×ótima (critério "capacidade de análise").

**Resposta do usuário:** concorda com `None`; questionou o lote; após a interface híbrida,
"Concordo".

**Decidido:** interface híbrida lote+base gulosa. Termos **Placement Strategy** e
**Placement** em `CONTEXT.md`. Criado **ADR-0001**.

---

### Q5 — Monitoramento e métricas (comparar estratégias)
(a) O que medir; (b) como coletar; (c) como reportar/comparar. Matplotlib como MVP ou extra?

**Recomendação:** métricas = tempo de resposta médio, tempo de espera médio, distribuição
borda×nuvem, utilização média por Server, makespan. Coletor = objeto **`Monitor`** (observador,
guarda série por tick). Relatório = tabela comparativa no console + análise no README; gráfico
matplotlib como extra opcional.

**Resposta do usuário:** matplotlib como extra opcional, "mas acho muito interessante".

**Decidido:** conjunto de métricas + `Monitor` aceitos. Relatório núcleo = tabela comparativa
+ análise no README. Gráfico matplotlib = extra opcional (desejado). **Monitor** em `CONTEXT.md`.

---

### Q6 — Topologia de latência e catálogo de estratégias
(a) Topologia restrita (borda-local-ou-nuvem) vs geral (qualquer Server, latência por origem);
(b) quais estratégias entregar.

**Recomendação:** (a) topologia **geral** — latência local `1` / vizinha `3` / nuvem `8`
(configurável); (b) núcleo = **AllCloud**, **EdgeFirst**, **LeastLoaded**; esticada =
**GlobalOptimal** (em lote, fecha a narrativa heurística×ótima e justifica o ADR-0001).

**Resposta do usuário:** "Se essas forem as melhores opções eu concordo contigo" → confirmado
como as melhores dadas as metas (completo/útil/claro/no prazo).

**Decidido:** topologia geral com latência por origem; Task ganha atributo **origin**.
Catálogo: AllCloud + EdgeFirst + LeastLoaded (núcleo) + GlobalOptimal (esticada). `origin`
registrado na definição de Task em `CONTEXT.md`.

---

### Q7 — Formato de entrada do cenário e reprodutibilidade
(a) Python/dataclasses vs YAML/JSON; (b) determinismo.

**Recomendação:** (a) cenários em Python/dataclasses (YAML como extra); (b) determinístico,
qualquer aleatoriedade com `seed` explícita.

**Resposta do usuário:** concorda com as duas; requisito extra: **altamente configurável**,
poder definir a **seed sem mexer no arquivo**.

**Decidido:** cenários = **fábricas parametrizadas** em Python (dataclasses tipadas), dirigidas
por uma **CLI** (`--scenario`, `--seed`, `--strategy`/`--compare`, `--ticks`, params de carga,
`--chart` opcional). Determinístico dada a seed. **Scenario** registrado em `CONTEXT.md`.

---

### Q8 — Estrutura do repositório
Layout proposto: pacote `sim/` top-level, um módulo por conceito (`model`, `engine`,
`strategies`, `monitor`, `scenarios`, `report`, `__main__`), núcleo **stdlib-only**
(matplotlib opcional), `tests/` cobrindo invariantes do motor e comportamento das estratégias.

**Resposta do usuário:** "concordo".

**Decidido:** layout acima aprovado. Núcleo sem dependências externas; matplotlib só para
`--chart`. Testes desde o início (invariantes: capacidade nunca excedida, toda Task conclui).

---

### Fechamento — trava de escopo e housekeeping

**MVP (travado, entrega hoje):** `model` (Task/Server/Scenario) · `engine` (tick, fila,
PENDING→RUNNING→DONE) · `strategies` (PlacementStrategy + GreedyStrategy + AllCloud +
EdgeFirst + LeastLoaded) · `monitor` (métricas) · `scenarios` (≥2 cargas, determinísticas) ·
CLI + tabela comparativa · testes · README com seção de análise · vídeo explicativo.

**Esticado (se sobrar tempo):** GlobalOptimal (heurística global por tick, não ótimo sobre
todo o tempo) · `--chart` matplotlib · loader YAML/JSON · "leitura 2" (Application gerando
Tasks em runtime).

**Resposta do usuário:** trava o escopo; manda corrigir o `code-conventions.md`; pede um
`to-prd` em seguida.

**Housekeeping:** `.claude/rules/code-conventions.md` **já estava** limpo do conteúdo do
Novelas IA (o alerta inicial veio de contexto de sessão desatualizado, não do arquivo em
disco). O arquivo era um stub aguardando o grill — preenchida a seção "Restrições deste
projeto" com as decisões desta sessão e atualizado o cabeçalho.

---

## Estado dos artefatos ao fim da sessão
- `CONTEXT.md`: glossário com Task, Server, Edge, Cloud, Tick, Placement Strategy, Placement,
  Monitor, Scenario.
- `docs/adr/0001-interface-de-alocacao-em-lote-com-base-gulosa.md`: interface de alocação.
- `.claude/rules/code-conventions.md`: seção "Restrições deste projeto" preenchida.
- Próximo passo pedido: rodar `to-prd`.
