# Spotify por gestos

Controla o Spotify com gestos da mão pela webcam, usando MediaPipe + OpenCV.

## Como abrir

**Dê duplo clique em `Iniciar.bat`.**

> ⚠️ **Não abra o `main.py` com duplo clique** — a janela fecha na hora.
> Esta máquina tem 3 versões do Python (3.10, 3.13 e 3.14), e o duplo clique
> em `.py` usa o **3.14**, que não tem as bibliotecas instaladas. O erro
> aparece e o console fecha antes de dar para ler.
> O `Iniciar.bat` chama o **Python 3.10** (`C:\Python310\python.exe`), que é
> onde `mediapipe` e `opencv` estão, e segura a janela aberta no final.

Use `Iniciar (debug).bat` para ver dedo por dedo o que a câmera está
reconhecendo — é o que ajuda a calibrar os limiares.

**Para rolar o YouTube, use `Iniciar YouTube.bat`.**

> ⚠️ O `Iniciar.bat` sem argumento abre no modo **música** (`--controller
> media`), que **não rola página**. Nesse modo os gestos verticais aparecem
> na tela — a barra enche normalmente — e nada acontece, porque o
> controlador de música não atende rolagem. O programa avisa uma vez no
> console: `[teclas de mídia] não atende 'rolar para baixo'`.

### Como rolar

Como no celular: **junte o polegar e o indicador** (a pinça é o dedo
encostando na tela), **arraste** para onde quiser rolar e **solte os dedos**.
O círculo verde no meio da tela mostra que a pinça foi reconhecida.

O movimento de volta com os dedos soltos **não rola nada** — é o que evita
ficar parado no mesmo lugar. Ver `specs/002-rolagem-por-arrasto.md`.

Sensibilidade em `config.py`:

| Campo | O que faz |
|---|---|
| `scroll_ticks_por_tela` | quanto rola um arrasto da altura inteira da tela. Aumente se estiver preguiçoso |
| `pinca_ratio` | quão perto os dedos precisam estar para contar como pinça |
| `pinca_dedos_livres` | quantos dos três dedos livres precisam estar esticados. É o que impede o punho de virar pinça |
| `scroll_natural` | `True` = conteúdo acompanha o dedo, como no celular. `False` = sentido da roda do mouse |

**Para controlar o Spotify com jogo aberto, use `Iniciar Spotify.bat`.**

> Este modo fala HTTP com a Web API em vez de injetar tecla no Windows, então
> **funciona em segundo plano** — foco e privilégio da janela em primeiro plano
> não importam. O `--controller media` não: quando o jogo em foco roda elevado,
> o Windows bloqueia o `SendInput` e o gesto é detectado mas não passa.
>
> Abre **sem janela de vídeo** de propósito: é o modo para usar por cima de
> outra coisa. A câmera continua ligada, porque é ela que detecta os gestos.
> Para ver o vídeo, use o `Iniciar (debug).bat`. Sai com Ctrl+C.

Pelo terminal, o equivalente é:

```bash
C:\Python310\python.exe main.py
```

## Instalação (só se for para outra máquina)

```bash
pip install -r requirements.txt
```

Na primeira execução o modelo de detecção de mãos (~8 MB) é baixado
automaticamente para `models/` — nesta máquina ele já está lá.

## Gestos

| Gesto | Ação |
|---|---|
| Deslizar a mão para a **direita** | Próxima faixa |
| Deslizar a mão para a **esquerda** | Faixa anterior |
| **Punho fechado parado** por ~0,8 s | Play / Pause |
| **Mão aberta** | Descanso (rearma o play/pause) |

O play/pause só dispara uma vez por punho. Para pausar e voltar a tocar, abra
a mão entre um comando e outro.

**Por que o punho e não a palma aberta:** a mão em repouso — na mesa, no braço
da cadeira — fica naturalmente com os dedos esticados. Qualquer comando ligado
à palma aberta dispara sozinho o tempo todo. Fechar a mão é deliberado;
esticar os dedos não é.

Pelo mesmo motivo o programa **não tenta distinguir palma de dorso**: contando
dedos esticados os dois são idênticos, e com este mapeamento isso não faz
diferença — nenhum dos dois dispara nada parado.

O swipe funciona com a mão em qualquer pose, **menos** o punho fechado (mão
"guardada"). Exigir a mão aberta no swipe não funciona na prática: no meio do
movimento a mão borra e inclina, e a pose vira "indefinido" bem na hora em que
o gesto está acontecendo.

## Modos de controle

**`--controller media` (padrão)** — envia as teclas de mídia do sistema
(Play/Pause, Next, Previous). Funciona com o Spotify desktop, o web player e
qualquer outro player. Não precisa de login nem de Premium.

```bash
python main.py
```

**`--controller spotify`** — usa a Web API oficial. Precisa de conta Premium
e de credenciais de app:

1. Crie um app em <https://developer.spotify.com/dashboard>
2. Em *Redirect URIs*, adicione `http://127.0.0.1:8888/callback`
3. Copie `.env.example` para `.env` e preencha o client id/secret
4. `python main.py --controller spotify` — o navegador abre uma vez para autorizar

```bash
python main.py --controller spotify
```

Vantagem da API: comanda o Spotify mesmo quando ele está em outro dispositivo
(celular, outro PC). Desvantagem: exige Premium, internet e configuração.

## Outras opções

```
--camera N      escolhe a webcam (padrão 0)
--no-preview    roda sem a janela de vídeo, só o console
--no-mirror     desliga o espelhamento da imagem
--debug         mostra quais dedos foram detectados como esticados
```

Sair: tecla `Q` na janela de vídeo, ou `Ctrl+C` no terminal.

## Ajustes finos

Todos os limiares ficam em `config.py`:

- Pulando faixa sem querer? Aumente `swipe_min_dx` (ex.: `0.24`).
- **Swipe difícil de reconhecer?** Diminua `swipe_min_dx` (ex.: `0.12`) e/ou
  aumente `swipe_window_s` (ex.: `0.9`) — a janela é o tempo que você tem para
  completar o movimento, então movimento devagar precisa de janela maior.
  A **barra no meio da tela** mostra o quanto do deslocamento já foi feito:
  ela fica **verde** quando já dá para pular. Se ela nem aparece, o problema
  não é o limiar — é a mão não estar sendo detectada, ou estar fechada.
- Movimento na diagonal não pega? Diminua `swipe_horizontal_ratio` para `1.2`.
- Play/Pause disparando rápido demais? Aumente `hold_duration_s`.
- Mão tremida quebrando o play/pause? Aumente `hold_max_movement`.
- Quer o play/pause na palma aberta em vez do punho? `pose_play_pause = "palma"`
  — mas leia antes o aviso na seção **Gestos**.
- Palma aberta não reconhecida? Diminua `finger_extended_margin` para `1.0`.
  Use `--debug` para ver dedo por dedo o que está sendo detectado.

Depois de mexer nos limiares, `python test_gestures.py` simula os gestos com
landmarks sintéticos e diz se cada um ainda dispara como esperado — sem câmera.

## Estrutura

```
main.py               loop de vídeo, HUD e disparo das ações
hand_tracker.py       wrapper do MediaPipe HandLandmarker
gestures.py           landmarks -> pose e swipe -> ação
config.py             todos os limiares ajustáveis
controllers/
  media_keys.py       teclas de mídia (Windows via SendInput, outros via pynput)
  spotify_api.py      Spotify Web API via spotipy
```

Para adicionar um gesto novo: crie o valor em `Action` (`gestures.py`),
detecte-o em `GestureEngine.update`, e trate-o no `if` de ações em `main.py`.
