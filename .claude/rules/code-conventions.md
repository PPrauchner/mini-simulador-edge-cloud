# Convenções de Código

> Lido pelo agente ao escrever ou revisar código. Para o modelo de domínio, ver
> `CONTEXT.md`; para as decisões de arquitetura e seus porquês, `docs/adr/`.
>
> As restrições específicas deste projeto foram definidas na sessão de *grill with
> docs* (2026-07-07, log em `docs/grills_logs/`) e estão na seção
> [Restrições deste projeto](#restrições-deste-projeto) abaixo.

---

## Idioma

- **Código** (módulos, identificadores, docstrings) em **inglês**.
- **Documentação** (ADRs, `CONTEXT.md`, README, log) em **português**.
- O glossário em `CONTEXT.md` faz a ponte entre o termo de domínio (pt-BR) e o
  identificador no código (inglês).

---

## Python — Docstrings (Google Style)

Três níveis:

**1. Módulo** — todo `.py` começa com um bloco descritivo:
```python
"""
Resumo de uma linha do que o módulo faz.

Responsabilidades:
- Primeira responsabilidade do módulo.
- Segunda responsabilidade do módulo.
"""
```

**2. Função / método** — obrigatório quando há ≥ 2 parâmetros ou o retorno não é
óbvio:
```python
def process_item(item: Item, options: Options) -> Result:
    """Processa um item de acordo com as opções fornecidas.

    Args:
        item: Item de entrada a ser processado.
        options: Opções que controlam o processamento.

    Returns:
        O resultado do processamento.
    """
```

**3. Classe** — docstring na classe e nos métodos públicos não-triviais:
```python
class Pipeline:
    """Orquestra as etapas de execução de um processo.

    Attributes:
        steps: Etapas na ordem de execução.
    """
```

---

## Python — Type Hints

- **Todo parâmetro e retorno** de função/método devem ser tipados — sem exceção.
- Sintaxe nativa Python 3.10+: `X | None` em vez de `Optional[X]`; `list[int]` em
  vez de `List[int]`.
- Para forward references (ex.: um tipo que referencia a si mesmo), adicionar
  `from __future__ import annotations` no topo.
- Evitar `Any` — ele encobre erros.

```python
# ✅ correto
def process(item: Item) -> Result: ...
def publish(resource: Resource, target: str) -> bool: ...

# ❌ errado
def process(item):          # sem anotações
def publish(...) -> Any:    # Any encobre erros
```

---

## Clean Code

- Funções com responsabilidade única — se o nome precisar de "e"/"ou", dividir.
- Nomes descritivos: sem abreviações opacas (`nd` → `node`, `sz` → `size`).
- Constantes em `UPPER_SNAKE_CASE`; variáveis e funções em `snake_case`; classes em
  `PascalCase`.
- Comentários explicam *por quê*, não *o quê*.
- Ver também `.claude/rules/karpathy-principles.md` (simplicidade primeiro,
  mudanças cirúrgicas, execução orientada a metas).

---

## Restrições deste projeto

> Definidas na sessão de *grill with docs* (2026-07-07). Modelo de domínio em
> [`CONTEXT.md`](../../CONTEXT.md); decisões e porquês em [`docs/adr/`](../../docs/adr/).

- **Linguagem**: Python 3.10+ (type hints nativos: `X | None`, `list[int]`).
- **Núcleo sem dependências externas**: apenas biblioteca padrão (`argparse`,
  `dataclasses`, `statistics`). `python -m sim` roda sem instalar nada.
- **`matplotlib` é dependência opcional** — usada só na flag `--chart`.
- **Interface**: CLI (`python -m sim`) — sem framework web, sem GUI.
- **Simulação em tempo discreto** (baseada em *ticks*); execução síncrona, um
  Scenario por vez. Sem **fila de mensagens / processamento assíncrono** (infra).
  A **fila de espera** de Tasks `PENDING` (conceito de domínio, FIFO) existe e é
  central — não confundir as duas.
- **Sem banco de dados**: cenários vivem em memória como dataclasses
  parametrizadas; nada persistido no MVP.
- **Estratégias de alocação plugáveis** via interface em formato de lote com base
  gulosa (ver [ADR-0001](../../docs/adr/0001-interface-de-alocacao-em-lote-com-base-gulosa.md)).
- **Reprodutibilidade**: qualquer aleatoriedade recebe uma `seed` explícita
  (default determinístico); a `seed` é configurável pela CLI, sem editar código.
- **Estrutura**: pacote `sim/`, um módulo por conceito (`model`, `engine`,
  `strategies`, `monitor`, `scenarios`, `report`, `__main__`); testes em `tests/`.
