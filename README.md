# Spotify por gestos

Controla música e rola páginas com gestos da mão pela webcam, usando MediaPipe + OpenCV.

## Como abrir

**Dê duplo clique em um dos atalhos.** Cada um já abre no modo certo:

| Atalho | O que faz | Janela de vídeo |
|---|---|---|
| **`Iniciar.bat`** | Música pelas **teclas de mídia** do Windows. Funciona com qualquer player e não precisa de nada configurado. É o padrão. | não |
| **`Iniciar Spotify.bat`** | Música pela **Web API do Spotify**. Precisa de Premium e do `.env`. **É o único que funciona com jogo aberto.** | não |
| **`Iniciar YouTube.bat`** | **Rolagem** de página por arrasto da pinça. Não controla música. | não |
| **`Iniciar (debug).bat`** | Mesma coisa do `Iniciar.bat`, mas **com a janela de vídeo** e mostrando dedo por dedo. É o de calibrar. | **sim** |

`_executar.bat` é encanamento compartilhado pelos quatro — acha o Python 3.10 e roda o
programa. Não abra ele direto.

> ⚠️ **Não abra o `src/main.py` com duplo clique** — a janela fecha na hora. Esta máquina
> tem 3 versões do Python (3.10, 3.13 e 3.14), e o duplo clique em `.py` usa o **3.14**,
> que não tem as bibliotecas. O erro aparece e o console fecha antes de dar para ler.
> Os `.bat` chamam o **Python 3.10** (`C:\Python310\python.exe`) explicitamente.

### Três deles abrem sem janela de vídeo

É de propósito: são modos para usar por cima de outra coisa, e uma janela a mais só
atrapalharia. **A câmera continua ligada**, porque é ela que detecta os gestos.

> ⚠️ **Sem janela, feche pelo `Ctrl+C` no console — não pelo X.** Fechando no X, o console
> some mas o Python pode continuar rodando com a câmera presa, e não há nada na tela
> indicando isso. O sinal é a luz da webcam continuar acesa. Se acontecer, encerre o
> `python.exe` pelo Gerenciador de Tarefas.

## Modo normal × modo Premium

Os dois controlam música. A diferença é **como o comando sai daqui** — e é isso que decide
qual usar.

| | `Iniciar.bat` — teclas de mídia | `Iniciar Spotify.bat` — Web API |
|---|---|---|
| Como manda o comando | injeta tecla de mídia no Windows (`SendInput`) | HTTP para o servidor do Spotify |
| Conta Premium | não precisa | **precisa** |
| Configuração | nenhuma | app no dashboard + `.env` + autorizar uma vez |
| Internet | não precisa | precisa |
| Funciona com | qualquer player (Spotify, YouTube, VLC…) | só o Spotify |
| **Com um jogo em primeiro plano** | **falha** | **funciona** |
| Comandar outro aparelho (celular, outro PC) | não | sim |
| Se nada estiver tocando | a tecla vai para o player padrão do sistema | erro 404 — precisa de dispositivo ativo |

**Por que as teclas de mídia falham jogando.** Elas dependem do `SendInput`, que passa
pelo controle de privilégio do Windows. Quando a janela em foco roda como administrador —
o caso de muitos jogos e anticheats —, o Windows **bloqueia** entrada vinda de um processo
com privilégio menor. O sintoma é traiçoeiro: o gesto **é detectado** (a barra na tela
enche normalmente) e simplesmente não acontece nada.

A Web API não passa por nada disso. Ela fala HTTP com o servidor do Spotify, que manda o
comando para o seu dispositivo. Foco, privilégio e janela em primeiro plano deixam de
existir como problema.

**Resumo prático:** use o `Iniciar.bat` no dia a dia; use o `Iniciar Spotify.bat` quando
for jogar.

### Configurar o modo Premium

Uma vez só:

1. Crie um app em <https://developer.spotify.com/dashboard>, marcando **Web API**.
2. Em *Redirect URIs*, adicione exatamente `http://127.0.0.1:8888/callback`.
   ⚠️ Tem que ser `127.0.0.1`. O Spotify **recusa `localhost`** desde abril de 2025, e o
   erro (`INVALID_CLIENT: Insecure redirect URI`) não explica o motivo.
3. Copie `.env.example` para `.env` e preencha `SPOTIPY_CLIENT_ID` e `SPOTIPY_CLIENT_SECRET`.
4. Abra o `Iniciar Spotify.bat`. O navegador abre **uma vez** para você autorizar; o token
   fica guardado em `.spotify_token_cache`.

`.env` e `.spotify_token_cache` estão no `.gitignore` e nunca vão para o GitHub.

**Exige o app do Spotify aberto e tendo tocado alguma coisa.** A Web API comanda um
*dispositivo ativo*; sem isso responde 404, e o programa mostra *nenhum dispositivo
Spotify ativo*. Não é erro de configuração, é como a API funciona.

## Gestos de música

| Gesto | Ação |
|---|---|
| Deslizar a mão para a **direita** | Próxima faixa |
| Deslizar a mão para a **esquerda** | Faixa anterior |
| **Punho fechado parado** por ~0,8 s | Play / Pause |
| **Mão aberta** | Descanso (rearma o play/pause) |

O play/pause só dispara uma vez por punho. Para pausar e voltar a tocar, abra a mão entre
um comando e outro.

**Por que o punho e não a palma aberta:** a mão em repouso — na mesa, no braço da cadeira —
fica naturalmente com os dedos esticados. Qualquer comando ligado à palma aberta dispara
sozinho o tempo todo. Fechar a mão é deliberado; esticar os dedos não é.

Pelo mesmo motivo o programa **não tenta distinguir palma de dorso**: contando dedos
esticados os dois são idênticos, e com este mapeamento isso não faz diferença — nenhum dos
dois dispara nada parado.

O swipe funciona com a mão em qualquer pose, **menos** o punho fechado (mão "guardada").
Exigir a mão aberta no swipe não funciona na prática: no meio do movimento a mão borra e
inclina, e a pose vira "indefinido" bem na hora em que o gesto está acontecendo.

## Rolagem — `Iniciar YouTube.bat`

Como no celular: **junte o polegar e o indicador**, **arraste** para onde quiser rolar e
**solte os dedos**. A pinça fechada é o dedo encostando na tela.

O movimento de volta com os dedos soltos **não rola nada**. É isso que evita ficar parado
no mesmo lugar — que era o defeito do desenho anterior, por gesto discreto. O porquê está
em `specs/002-rolagem-por-arrasto.md`.

Como este modo abre sem janela, **o retorno é a própria página rolando**. Para ver o
círculo verde que confirma a pinça — útil ao calibrar —, rode pelo terminal:

```bash
C:\Python310\python.exe src\main.py --controller youtube --debug
```

Sensibilidade em `src/config.py`:

| Campo | O que faz |
|---|---|
| `scroll_ticks_por_tela` | quanto rola um arrasto da altura inteira da tela. Aumente se estiver preguiçoso |
| `pinca_ratio` | quão perto os dedos precisam estar para contar como pinça |
| `pinca_dedos_livres` | quantos dos três dedos livres precisam estar esticados. É o que impede o punho de virar pinça — o punho também junta polegar e indicador |
| `scroll_natural` | `True` = conteúdo acompanha o dedo, como no celular. `False` = sentido da roda do mouse |

> Os modos de música **não rolam**, e o de rolagem **não toca**. Se você fizer o gesto
> errado para o modo, o programa avisa uma vez no console — por exemplo
> `[teclas de mídia] não atende 'rolar'` — em vez de ficar em silêncio.

## Pelo terminal

Os `.bat` são atalhos para isto, sempre a partir da raiz do projeto:

```bash
C:\Python310\python.exe src\main.py                       # teclas de mídia
C:\Python310\python.exe src\main.py --controller spotify   # Web API
C:\Python310\python.exe src\main.py --controller youtube   # rolagem
```

Opções:

```
--camera N      escolhe a webcam (padrão 0)
--no-preview    roda sem a janela de vídeo, só o console
--no-mirror     desliga o espelhamento da imagem
--debug         mostra quais dedos foram detectados como esticados
```

Os atalhos repassam o que você digitar depois deles, então
`Iniciar (debug).bat --controller youtube` também funciona.

Sair: `Ctrl+C` no console. Com a janela aberta, a tecla `Q` também serve.

## Instalação (só se for para outra máquina)

```bash
pip install -r requirements.txt
```

Na primeira execução o modelo de detecção de mãos (~8 MB) é baixado automaticamente para
`models/`.

## Ajustes finos

Todos os limiares ficam em `src/config.py`. Use o `Iniciar (debug).bat` para calibrar — é
o único que mostra a imagem.

- Pulando faixa sem querer? Aumente `swipe_min_dx` (ex.: `0.24`).
- **Swipe difícil de reconhecer?** Diminua `swipe_min_dx` (ex.: `0.12`) e/ou aumente
  `swipe_window_s` (ex.: `0.9`) — a janela é o tempo que você tem para completar o
  movimento, então movimento devagar precisa de janela maior. A **barra no meio da tela**
  mostra o quanto do deslocamento já foi feito e fica **verde** quando já dá para pular.
  Se ela nem aparece, o problema não é o limiar — é a mão não estar sendo detectada, ou
  estar fechada.
- Movimento na diagonal não pega? Diminua `swipe_horizontal_ratio` para `1.2`.
- Play/Pause disparando rápido demais? Aumente `hold_duration_s`.
- Mão tremida quebrando o play/pause? Aumente `hold_max_movement`.
- Quer o play/pause na palma aberta em vez do punho? `pose_play_pause = "palma"` — mas
  leia antes o aviso na seção **Gestos de música**.
- Palma aberta não reconhecida? Diminua `finger_extended_margin` para `1.0`.
- Punho virando pinça? Aumente `pinca_dedos_livres` para `2`.

Depois de mexer nos limiares:

```bash
C:\Python310\python.exe tests\test_gestures.py
```

Ele simula os gestos com landmarks sintéticos e diz se cada um ainda dispara como
esperado — sem precisar de câmera.

## Estrutura

```
Iniciar.bat           teclas de mídia, sem janela (duplo clique aqui)
Iniciar Spotify.bat   Web API, sem janela — o modo que funciona com jogo aberto
Iniciar YouTube.bat   rolagem por arrasto, sem janela
Iniciar (debug).bat   COM janela e dedo a dedo, para calibrar
_executar.bat         encanamento compartilhado; não use direto

src/
  main.py             loop de vídeo, HUD e disparo das ações
  hand_tracker.py     wrapper do MediaPipe HandLandmarker
  gestures.py         landmarks -> pose, swipe e arrasto -> ação
  config.py           todos os limiares ajustáveis
  controllers/
    base.py           as duas interfaces: player e rolagem
    media_keys.py     teclas de mídia (Windows via SendInput, outros via pynput)
    spotify_api.py    Spotify Web API via spotipy
    youtube.py        rolagem por roda do mouse

tests/
  test_gestures.py    a suíte inteira, com landmarks sintéticos
specs/                o porquê das decisões de desenho
models/               modelo do MediaPipe (baixado sozinho, fora do git)
```

Para adicionar um gesto novo: crie o valor em `Action` (`src/gestures.py`), detecte-o em
`GestureEngine.update`, e trate-o no mapa `ACAO_PARA_METODO` de `src/main.py`. Se ele não
for de música nem de rolagem, provavelmente pede uma interface nova em
`src/controllers/base.py` — veja lá o porquê de serem duas.
