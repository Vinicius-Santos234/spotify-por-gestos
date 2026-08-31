# 002 — Rolagem por arrasto, no lugar do gesto discreto

**Status:** aceita · **Data:** 2026-08-31 · **Substitui:** a parte vertical da [spec 001](001-controller-youtube.md)

## Por que mudar uma coisa que passou nos testes

A spec 001 entregou rolagem por **swipe vertical discreto**: move a mão para baixo além
do limiar, dispara um passo de rolagem. Passou nos 23 testes e funcionou exatamente como
especificado.

**E no uso real não serve.** O relato, depois de testar com a webcam:

> *"tenho que arrastar minha palma aberta pra baixo pra descer um pouquinho, e no gesto de
> subir a mão de novo pra ela aparecer na câmera, ele já reconhece pra subir a tela, então
> acaba que fico parado no mesmo lugar."*

## O defeito é de desenho, não de calibragem

**Gesto discreto tem catraca.** Para repetir o comando é preciso voltar a mão à posição
inicial, e esse retorno é um movimento igualmente válido no sentido contrário. Não existe
limiar que resolva: o problema é que **a mão não tem como "sair da tela"** entre um gesto
e outro.

O cooldown foi a tentativa de contornar — descarta o histórico enquanto corre. Mas aí vira
escolha entre dois males: cooldown curto e o retorno dispara; cooldown longo e a rolagem
fica lenta demais para servir.

> É o mesmo tipo de erro de 08/08, quando "palma aberta parada" foi escolhida para
> play/pause e disparava sozinha — **a pose escolhida era a que a mão faz naturalmente**.
> Aqui: o movimento de rearme é o próprio comando invertido. Nos dois casos a correção não
> é mexer no número, é trocar o mapeamento.

## O desenho novo: dedo na tela, arrasta, solta

Metáfora de celular, que é o que se quer imitar:

| Celular | Aqui |
|---|---|
| encostar o dedo na tela | **fechar a pinça** (polegar encosta no indicador) |
| arrastar | mover a mão, ainda em pinça |
| tirar o dedo | **abrir a pinça** |

**A catraca some porque o retorno acontece com a pinça aberta**, e pinça aberta não rola
nada. É exatamente como no celular: você arrasta, solta, reposiciona o dedo, arrasta de
novo.

### Por que pinça, e não a mão apontando
Pela lição de 08/08, escrita no cabeçalho do `gestures.py`: *"fechar a mão é deliberado;
esticar os dedos não é"*. A mão em repouso fica com os dedos esticados — qualquer pose
baseada em dedo esticado dispara sozinha. **Encostar o polegar no indicador nunca acontece
por acaso.** E o ponto entre os dois dedos é literalmente a "ponta do dedo" pedida.

## Requisitos

### R1 — Pinça é o "dedo na tela"
A pinça é detectada pela distância entre a ponta do polegar e a do indicador,
**normalizada pelo tamanho da mão** (pulso → base do médio). Sem normalizar, a mão longe
da câmera nunca fecharia a pinça e a mão perto viveria em pinça.

### R2 — Rolagem contínua e proporcional
Com a pinça fechada, cada frame converte o deslocamento vertical do ponto da pinça em
rolagem. O movimento é **proporcional**: arrastar o dobro rola o dobro.

### R3 — Fração não se perde
O deslocamento por frame é pequeno e a roda do mouse só aceita passos inteiros. A sobra
**acumula** entre frames, senão um arrasto lento vira zero para sempre.

### R4 — Soltar não rola. **Este é o requisito que motivou a spec.**
Com a pinça aberta, nenhum movimento vertical produz rolagem — não importa o tamanho.
Voltar a mão para cima com a pinça aberta deve produzir **zero**.

### R5 — Conteúdo acompanha o dedo
Como no celular: arrastar para baixo traz o conteúdo para baixo, ou seja, mostra o que
estava acima. Configurável por `scroll_natural`, porque é gosto — mas o padrão é o do
celular, que foi o pedido.

### R6 — Pinça não dispara os gestos de música
Com a pinça fechada, o swipe horizontal e o play/pause ficam suspensos. Sem isso, um
arrasto com qualquer desvio lateral pularia faixa no meio da rolagem.

### R7 — O modo música não muda em nada
`--controller media` e `--controller spotify` continuam idênticos. Nenhum limiar
horizontal alterado.

### R8 — O HUD mostra que está agarrado
Sem retorno visual não dá para saber se a pinça foi reconhecida — é a mesma lição da barra
de progresso, que foi o que permitiu calibrar em 08/08.

## Fora de escopo
- Rolagem horizontal.
- Zoom por pinça de duas mãos.
- Inércia / rolagem com impulso ao soltar.
- A extensão de navegador, que segue sendo o destino final da spec 001.

## O que é removido
`Action.SCROLL_UP` e `Action.SCROLL_DOWN`, a detecção de swipe vertical, `swipe_min_dy`,
`swipe_vertical_ratio` e `scroll_cooldown_s`. **Junto com os testes que os cobriam** — eles
verificavam um comportamento que decidimos não querer mais. Ficam no histórico do git.

## Critério de aceite
1. Arrastar em pinça rola de forma contínua e proporcional.
2. Voltar com a pinça aberta **não rola nada** — teste explícito.
3. `python test_gestures.py` passa, incluindo o teste da catraca.
4. Os testes de música seguem passando sem alteração.
