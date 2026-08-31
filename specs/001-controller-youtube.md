# 001 — `--controller youtube`: rolar a página com gestos verticais

**Status:** proposta · **Data:** 2026-08-31 · **Alvo:** este repositório

## Contexto

Este projeto hoje controla música: deslizar a mão na horizontal pula faixa, punho
fechado parado dá play/pause. Existem dois controllers atrás da mesma interface
(`controllers/base.py`): `media` (teclas de mídia do Windows) e `spotify` (Web API).

Queremos um terceiro modo, `--controller youtube`, que **role a página para cima e para
baixo** com gestos verticais da mão — o "scroll do celular no ar".

## O que NÃO cabe no código de hoje

Três coisas impedem que isso seja só "mais um controller". A spec existe por causa delas.

1. **A detecção de swipe rejeita movimento vertical de propósito.** Em
   `gestures.py::_check_swipe`:
   ```python
   if abs(dx) < abs(dy) * cfg.swipe_horizontal_ratio:
       return None
   ```
   Movimento mais vertical que horizontal é descartado. Não existe detecção vertical.

2. **`Action` só tem ações de música:** `PLAY_PAUSE`, `NEXT`, `PREV`.

3. **A interface `Controller` é moldada para player:** `play_pause()`, `next_track()`,
   `previous_track()`. Um controller de rolagem seria obrigado a implementar três métodos
   que não fazem sentido para ele.

## Escopo

### Dentro
- Detecção de **swipe vertical** (cima/baixo), simétrica à horizontal que já existe.
- Ações novas `SCROLL_UP` / `SCROLL_DOWN`.
- Interface de controller generalizada, de modo que **cada controller declare quais ações
  atende** — sem obrigar ninguém a implementar método que não usa.
- Controller `youtube`, rolando por **entrada de sistema** (roda de mouse / setas) na
  janela em foco.
- Limiares verticais em `config.py`, no mesmo estilo dos horizontais.
- Testes em `test_gestures.py`, com landmarks sintéticos.
- `--controller youtube` no `argparse` e no HUD.

### Fora — não fazer
- **Extensão de navegador e servidor local.** É a arquitetura decidida para o projeto
  `youtube-por-gestos`, e continua sendo o destino final — mas não entra aqui.
- Detectar se o YouTube está em foco.
- Gestos novos além do swipe vertical.
- Rolagem contínua/proporcional ao movimento. Cada swipe é um passo discreto.
- Reescrever a detecção horizontal existente. Ela funciona e foi calibrada em uso real.

> **Por que a rolagem por entrada de sistema é provisória, e está ok assim.**
> Mandar scroll para "a janela em foco" é suposição — pode cair num popup ou na janela
> errada. A saída certa é a extensão rolar a própria página (`window.scrollBy()`), e é o
> que o projeto `youtube-por-gestos` decidiu. Esta spec deixa **a costura pronta**: quando
> a extensão existir, entra um `YouTubeExtensionController` implementando a mesma
> interface, e **nada em `gestures.py` muda**. É o mesmo desenho que já separa `media` de
> `spotify` — mesma interface, mecanismos diferentes.

## Requisitos

### R1 — Swipe vertical detectado
Dado que a mão se desloca verticalmente mais que `swipe_min_dy` dentro de
`swipe_window_s`, e que o movimento é pelo menos `swipe_vertical_ratio` vezes mais
vertical que horizontal, então a engine devolve `Action.SCROLL_DOWN` (mão para baixo) ou
`Action.SCROLL_UP` (mão para cima).

> **Atenção ao sinal.** As coordenadas são normalizadas com **y crescendo para baixo**
> (padrão de imagem). Mão descendo = `dy > 0`. Verifique contra o comportamento real
> antes de fixar: rolar "para baixo" deve mostrar conteúdo mais abaixo na página.

### R2 — Horizontal e vertical não se atropelam
Dado um movimento diagonal ambíguo, então **no máximo uma** ação é disparada por frame.
O critério de desempate deve ser explícito no código e coberto por teste.

### R3 — Punho continua sendo descanso do swipe
Vale para o vertical a mesma regra do horizontal: swipe com o punho fechado **não conta**.
A justificativa está no cabeçalho de `gestures.py` e não muda.

### R4 — Cooldown próprio
Dado um swipe vertical disparado, então novo swipe vertical só é aceito depois de
`swipe_cooldown_s`. Durante o cooldown o histórico é descartado — senão a volta da mão à
posição inicial dispara o gesto contrário. **Esse bug já aconteceu no horizontal**; ver o
comentário dentro de `_check_swipe`.

### R5 — Controllers declaram o que atendem
Dado um controller que não trata uma ação, então o programa **não quebra**: ignora e
segue, ou avisa uma vez. Concretamente: `media` e `spotify` não rolam; `youtube` não
toca música. Não force métodos vazios em ninguém.

### R6 — `--controller youtube` funciona ponta a ponta
Dado `python main.py --controller youtube`, então o programa sobe, o HUD mostra o nome do
controller, e swipes verticais rolam a janela em foco.

### R7 — Limiares configuráveis
Novos campos em `config.py`, com comentário em português explicando o efeito, no mesmo
estilo dos existentes. Sugestão de ponto de partida — **calibrar depois, em uso real**:
`swipe_min_dy = 0.16`, `swipe_vertical_ratio = 1.4`.

### R8 — Testes sem câmera
`test_gestures.py` ganha casos para: swipe para baixo dispara `SCROLL_DOWN`; para cima
dispara `SCROLL_UP`; movimento vertical curto demais **não** dispara; diagonal ambíguo
respeita R2; punho fechado **não** dispara. Use os helpers que já existem
(`make_hand`, `run`, `still_frames`, `check`) e crie o análogo vertical de
`swipe_frames`. Roda com `python test_gestures.py` — **não** é pytest.

### R9 — HUD mostra o vertical
`draw_hud` já desenha uma barra de progresso do swipe horizontal. O vertical precisa de
retorno visual equivalente. **Isso não é enfeite:** a nota do projeto registra que a barra
foi o que transformou tentativa e erro em calibragem — sem ela, "não funciona" é
indistinguível de "faltaram 2 cm de movimento".

## Restrições

- **Python 3.10** (`C:\Python310`). A máquina tem três Pythons; os `.bat` já apontam para o certo.
- **Sem dependência nova** se der para evitar. O projeto usa `ctypes`/`SendInput` direto
  para teclas de mídia — a roda do mouse sai pelo mesmo caminho (`MOUSEEVENTF_WHEEL`), e a
  `struct` `_MouseInput` **já está declarada** em `controllers/media_keys.py`.
  Se precisar mesmo de biblioteca nova, justifique no PR.
- **Não mexer** no mapeamento de gestos horizontal nem nos limiares já calibrados.
- Comentários e mensagens em **português**, como o resto do repositório.
- Windows é o alvo. Se houver caminho fácil para Linux/macOS, siga o padrão de fallback que
  `media_keys.py` já usa com `pynput` — se não houver, saia com mensagem clara.

## Critério de aceite

1. `python test_gestures.py` passa, incluindo os casos novos.
2. `python main.py --controller youtube` sobe sem erro e o HUD mostra o controller.
3. `python main.py` (padrão `media`) e `--controller spotify` continuam funcionando
   **exatamente como antes** — nenhuma regressão no comportamento de música.
4. `git diff` não toca em `models/`, `.env` nem em nada fora do escopo.

## Onde olhar

| Arquivo | O que tem |
|---|---|
| `gestures.py` | `Action`, `GestureEngine`, `_check_swipe` (a lógica horizontal a espelhar) |
| `controllers/base.py` | a interface a generalizar |
| `controllers/__init__.py` | `get_controller()`, o dispatch |
| `controllers/media_keys.py` | `SendInput` por `ctypes` e a `struct` `_MouseInput` já pronta |
| `config.py` | onde entram os limiares novos |
| `main.py` | `argparse` (linha ~112), o mapa ação→controller (~162) e `draw_hud` (~70) |
| `test_gestures.py` | helpers de landmark sintético |
