# Mini-Simulador: Alocação de Tarefas em Edge-Cloud

Simulador em tempo discreto (Python, biblioteca padrão) que decide, de forma
programática, em qual servidor — de **borda** (Edge) ou de **nuvem** (Cloud) —
cada Task é executada, monitora o resultado e permite **comparar estratégias de
alocação** sobre a mesma carga.

O vocabulário de domínio (Task, Server, Edge/Cloud, Wait, Response Time,
Makespan, Utilization, Scenario, Placement Strategy) está definido em
[`CONTEXT.md`](CONTEXT.md); as decisões de arquitetura e seus porquês em
[`docs/adr/`](docs/adr/).

## Requisitos

- **Python 3.10+**. Só isso.
- **Nenhuma dependência externa** para rodar: o núcleo usa apenas a biblioteca
  padrão (`argparse`, `dataclasses`, `random`, `statistics`). Não há `pip install`.
- **`matplotlib` é dependência opcional**, usada só pela flag `--chart`. Está
  declarada como o *extra* `chart` no `pyproject.toml`; instale com
  `uv pip install ".[chart]"` (ou `pip install ".[chart]"`). Sem `--chart`, nada a
  importa e o núcleo roda sem ela.

## Como rodar

A partir da raiz do repositório:

```bash
python -m sim
```

Sem argumentos, roda o Scenario `minimal` sob a estratégia `AllCloud` e imprime as
métricas de uma execução:

```
scenario: minimal | strategy: AllCloud
mean response time: 10.50 ticks
mean wait: 0.50 ticks
split edge/cloud: 0 / 4 tasks
utilization per server:
  edge-a: 0%
  cloud: 100%
makespan: tick 3
```

### Flags da CLI

| Flag | Valores | Default | Efeito |
|------|---------|---------|--------|
| `--scenario` | `minimal`, `low`, `high` | `minimal` | Scenario a rodar: o fixo `minimal` ou um preset de carga (`low`/`high`). |
| `--seed` | inteiro | `0` | Semente de reprodutibilidade da carga aleatória. Mesma seed → mesma carga → mesmas métricas. Ignorada por `minimal` (carga fixa). |
| `--strategy` | `allcloud`, `edgefirst`, `leastloaded` | `allcloud` | Placement Strategy a rodar (quando **não** se usa `--compare`). |
| `--compare` | — (flag) | desligada | Roda **todas** as estratégias sobre o mesmo Scenario/seed e imprime a tabela comparativa. Ignora `--strategy`. |
| `--ticks` | inteiro | `10000` | Teto de segurança de ticks simulados; a simulação aborta com erro se ultrapassar. |
| `--chart` | caminho (PNG) | desligada | Salva um gráfico da execução: ocupação por Server ao longo dos Ticks (execução única) ou barras de response/wait/makespan por estratégia (com `--compare`). Um caminho relativo é gravado na pasta `charts/` (criada sob demanda e **fora do versionamento**, no `.gitignore`); um caminho absoluto é respeitado como está. Requer `matplotlib`. |

**Parâmetros de carga** (sobrescrevem o preset selecionado; ignorados por
`minimal`, que tem carga fixa):

| Flag | Efeito |
|------|--------|
| `--num-tasks` | Número de Tasks geradas. |
| `--arrival-window` | Tasks chegam uniformemente em ticks `[0, janela]`; janela estreita concentra chegadas e cria contenção. |
| `--duration-min` / `--duration-max` | Faixa (inclusiva) da duração de cada Task, em ticks. |
| `--demand-min` / `--demand-max` | Faixa (inclusiva) da demanda de capacidade de cada Task, em unidades. |

`python -m sim --help` lista tudo isso na própria CLI.

### Exemplos

```bash
# Uma estratégia num preset de carga alta
python -m sim --scenario high --strategy edgefirst

# Comparar as três estratégias na carga baixa
python -m sim --scenario low --compare

# Reproduzir/variar a carga aleatória com a seed
python -m sim --scenario high --seed 1 --compare

# Ajustar o preset: mesma infra, 30 Tasks em vez das 24 padrão
python -m sim --scenario high --num-tasks 30 --compare

# Salvar um gráfico (requer matplotlib): ocupação por Server ao longo dos Ticks.
# O caminho relativo cai em charts/ (fora do versionamento) -> charts/ocupacao.png
python -m sim --scenario high --chart ocupacao.png

# Com --compare, o gráfico vira as barras de métricas por estratégia
python -m sim --scenario high --compare --chart comparacao.png
```

### As métricas impressas

Todas seguem a semântica de [`CONTEXT.md`](CONTEXT.md):

- **response** — *Response Time* médio: `espera + latência + duração` por Task. É a
  métrica principal de comparação; numeriza o trade-off Edge×Cloud.
- **wait** — *Wait* médio: ticks em `PENDING` entre a chegada e a alocação. Revela
  contenção; zero quando a Task é alocada no tick em que chega.
- **edge/cloud** — o *split* do Monitor: quantas Tasks (por contagem) rodaram na
  borda vs. na nuvem.
- **util:\<server\>** — *Utilization* média de cada Server (fração da capacidade
  ocupada por tick, até o makespan).
- **makespan** — tick em que a última Task conclui. A latência **não** entra no
  makespan — ela é contábil (ver [ADR-0002](docs/adr/0002-latencia-contabil-nao-transito-simulado.md)).

## Análise dos resultados

A infraestrutura é a **mesma** nos dois presets de carga — uma borda `edge-a`
(capacidade 2) e uma nuvem `cloud` (capacidade 4) — para isolar a variável em
estudo: só a carga muda, então a mudança no ranking das estratégias se atribui à
contenção, não à topologia. As latências são contábeis: borda local = 1 tick,
nuvem = 8 ticks ([ADR-0002](docs/adr/0002-latencia-contabil-nao-transito-simulado.md)).

As três estratégias (ver [ADR-0001](docs/adr/0001-interface-de-alocacao-em-lote-com-base-gulosa.md)
e `sim/strategies.py`):

- **AllCloud** — manda toda Task para a nuvem. Paga a latência alta (8) em **toda**
  resposta.
- **EdgeFirst** — prefere a borda local; só cai para a nuvem quando a borda não
  cabe. Sob carga, satura a borda.
- **LeastLoaded** — coloca a Task no Server com **mais capacidade livre** (borda ou
  nuvem). Balanceia, mas só passa a usar a borda quando a nuvem enche.

### Carga baixa — `python -m sim --scenario low --compare`

6 Tasks curtas (duração 1–2), chegadas espalhadas em 15 ticks: **sem contenção**.

```
strategy     response  wait  edge/cloud  util:edge-a  util:cloud  makespan
AllCloud         9.67  0.00         0/6           0%         18%        13
EdgeFirst        2.67  0.00         6/0          36%          0%        13
LeastLoaded      9.67  0.00         0/6           0%         18%        13
```

Ninguém espera (`wait 0.00` nas três): há capacidade de sobra, então o Response
Time é **latência pura + duração**. O único diferenciador é *onde* a Task roda:

- **EdgeFirst vence com folga** (2.67): tudo cabe em `edge-a`, latência 1.
- **AllCloud** (9.67) paga a latência 8 da nuvem em cada uma das 6 Tasks.
- **LeastLoaded empata com AllCloud** (9.67, split `0/6`): com a nuvem (capacidade
  4) sempre mostrando mais capacidade livre que a borda (capacidade 2) e sem
  contenção para virar esse jogo, o "menos carregado" é **sempre** a nuvem. Sob
  carga baixa, LeastLoaded degenera em AllCloud.

**Ranking (carga baixa):** EdgeFirst ≫ AllCloud = LeastLoaded.

### Carga alta — `python -m sim --scenario high --compare`

24 Tasks mais longas (duração 3–6, demanda 1–2), chegando em rajada (janela de 3
ticks): a **contenção aparece como espera**.

```
strategy     response   wait  edge/cloud  util:edge-a  util:cloud  makespan
AllCloud        31.71  19.00        0/24           0%         93%        44
EdgeFirst       22.54  12.46        9/15          87%         92%        30
LeastLoaded     23.00  12.62        8/16          90%         90%        30
```

Agora a **espera domina a resposta** (12–19 dos ~22–32 ticks). O que importa deixou
de ser a latência e passou a ser usar **os dois servidores em paralelo**:

- **AllCloud despenca para último** (31.71): funila 24 Tasks pela capacidade 4 da
  nuvem, a fila `PENDING` estoura (`wait 19.00`) e o makespan estica para 44 —
  serialização auto-infligida. A borda fica ociosa (`util:edge-a 0%`).
- **EdgeFirst e LeastLoaded quase empatam no topo** (22.54 e 23.00): ambos rodam
  borda e nuvem em paralelo (`util` ~90% nos dois Servers), cortam a espera pela
  metade e encurtam o makespan para 30.
- **LeastLoaded "acorda":** assim que a rajada enche a nuvem, `edge-a` vira o Server
  com mais capacidade livre e LeastLoaded começa a alocar na borda — o split sai de
  `0/6` (carga baixa) para `8/16`. Ele recupera quase todo o ganho da borda.

**Ranking (carga alta):** EdgeFirst ≈ LeastLoaded ≫ AllCloud.

### A mudança de ranking, e o porquê

O que muda entre os dois cenários é **a posição de LeastLoaded**:

| Estratégia | Carga baixa | Carga alta |
|------------|-------------|------------|
| EdgeFirst | 1º (2.67) | 1º (22.54) |
| LeastLoaded | **empatado em último** (9.67) | **2º, colado no 1º** (23.00) |
| AllCloud | empatado em último (9.67) | último isolado (31.71) |

LeastLoaded sobe do fundo (indistinguível de AllCloud) para quase o topo. A causa é
o **gatilho da contenção**: ele só usa a borda quando a nuvem enche. Sob carga baixa
a nuvem nunca enche, então ele nunca toca a borda; sob carga alta a nuvem satura em
segundos e ele passa a balancear.

O trade-off Edge×Cloud, portanto, tem dois regimes:

- **Sem contenção**, o custo é só **latência** → vence quem coloca na borda de
  propósito (EdgeFirst). Estratégias reativas à carga (LeastLoaded) não têm sinal
  para agir e caem no baseline.
- **Com contenção**, o custo passa a ser **espera** → vence quem **paraleliza**
  borda e nuvem (EdgeFirst *e* LeastLoaded), e quem ignora a borda (AllCloud) paga a
  fila que ele mesmo cria.

EdgeFirst é robusto nos dois regimes porque usa a borda incondicionalmente; é a
estratégia a bater. A ordem exata entre EdgeFirst e LeastLoaded na carga alta é
sensível à seed — com `--seed 1`, por exemplo, LeastLoaded passa EdgeFirst — mas o
resultado qualitativo é estável: **AllCloud é sempre o pior sob carga, e as duas
estratégias que usam a borda dominam.** Troque a seed com `--seed N` para conferir.
