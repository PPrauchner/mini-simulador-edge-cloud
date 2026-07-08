# CLAUDE.md — Mini-Simulador: Alocação de Tarefas em Edge-Cloud

Simulador em **tempo discreto** (Python, biblioteca padrão) que decide, de forma
programática, em qual Server — de **borda** (Edge) ou de **nuvem** (Cloud) — cada
Task é executada, monitora o resultado e permite **comparar estratégias de
alocação** sobre a mesma carga. A comparação de Placement Strategies é o objetivo
do projeto.

Repositório: `PPrauchner/mini-simulador-edge-cloud`.

---

## Fontes da verdade (ler antes de implementar)

A documentação abaixo é a fonte da verdade das decisões — o código as segue, não o
contrário. Consultar antes de escrever ou revisar código.

| Documento | O que é |
|-----------|---------|
| [`CONTEXT.md`](CONTEXT.md) | Glossário de domínio. Faz a ponte entre o termo pt-BR e o identificador em inglês (Task, Server, Edge/Cloud, Wait, Response Time, Makespan, Utilization, Scenario, Placement Strategy, Monitor, Tick). |
| [`docs/adr/`](docs/adr/) | Decisões de arquitetura e seus porquês. **ADR-0001**: interface de alocação em lote com base gulosa. **ADR-0002**: latência é contábil, não trânsito simulado. |
| [`docs/PRD.md`](docs/PRD.md) | O brief/PRD do desafio. |
| [`README.md`](README.md) | Como rodar (todas as flags da CLI) + análise dos resultados dos cenários. |
| [`.claude/rules/code-conventions.md`](.claude/rules/code-conventions.md) | Convenções de código (docstrings Google, type hints nativos) + as restrições deste projeto. |
| [`.claude/rules/karpathy-principles.md`](.claude/rules/karpathy-principles.md) | Princípios de comportamento: simplicidade primeiro, mudanças cirúrgicas, execução orientada a metas. |

As restrições do projeto foram fixadas na sessão de *grill with docs* de
2026-07-07 (log em `docs/grills_logs/`).

---

## Comandos

```bash
python -m sim                 # roda o Scenario minimal sob AllCloud e imprime métricas
python -m sim --help          # lista todas as flags
python -m sim --scenario high --compare   # compara as 3 estratégias na mesma carga
python -m pytest              # roda a suíte de testes
```

Detalhe de cada flag (`--scenario`, `--seed`, `--strategy`, `--compare`,
`--ticks`, parâmetros de carga) está no [README](README.md#flags-da-cli).

---

## Restrições (resumo — detalhe em [code-conventions.md](.claude/rules/code-conventions.md))

- **Python 3.10+**, type hints nativos (`X | None`, `list[int]`).
- **Núcleo sem dependências externas**: apenas a biblioteca padrão. `python -m sim`
  roda sem instalar nada. `matplotlib` é a única dependência opcional (flag
  `--chart`).
- **Interface só CLI** (`python -m sim`) — sem web, sem GUI.
- **Simulação em tempo discreto** (baseada em Ticks); síncrona, um Scenario por vez.
  Sem fila de mensagens / assíncrono. Não confundir com a **fila de espera** de Tasks
  `PENDING` (conceito de domínio, FIFO) — essa existe e é central.
- **Sem banco de dados**: Scenarios vivem em memória como dataclasses; nada persiste.
- **Estratégias de alocação plugáveis** via interface em lote com base gulosa
  (ADR-0001).
- **Reprodutibilidade**: toda aleatoriedade recebe uma `seed` explícita, configurável
  pela CLI (default determinístico) — sem editar código.

---

## Estrutura

```
sim/            # pacote — um módulo por conceito
  model.py        # Task, Server, Scenario e afins (dataclasses)
  engine.py       # motor de simulação em ticks
  strategies.py   # Placement Strategies (AllCloud, EdgeFirst, LeastLoaded)
  monitor.py      # coleta das métricas (só observa)
  scenarios.py    # fábricas de Scenario (minimal + presets low/high)
  report.py       # montagem das saídas de console (tabela --compare)
  __main__.py     # a CLI (argparse)
tests/          # espelha os módulos de sim/
docs/           # PRD, ADRs, logs de grill
```

Separação a respeitar: o **Monitor** só coleta métricas; a **apresentação**
(tabelas, formatação) vive em `report.py`.

---

## Idioma

- **Código** (módulos, identificadores, docstrings): **inglês**.
- **Documentação** (ADRs, `CONTEXT.md`, README, logs): **português**.
- O glossário em `CONTEXT.md` faz a ponte entre os dois.

---

## Fluxo de trabalho

- Trabalho organizado por **issues no GitHub**; implementação via skills
  `/start-issue` → `/tdd` → `/commit`.
- **Commits atômicos**: uma responsabilidade por commit, mensagem convencional
  (`feat`, `test`, `docs`, …) referenciando a issue.
- Branches nomeadas `issueN` — podendo agrupar mais de um número (ex.: `issue345`
  reúne as issues 3, 4 e 5; `issue67` reúne 6 e 7).
