"""Testa a lógica de gestos com landmarks sintéticos, sem precisar de câmera.

Rode depois de mexer nos limiares do config.py:  python test_gestures.py
"""
import sys

from config import Config
from gestures import Action, GestureEngine, Pose, classify_pose
from hand_tracker import Hand

W, H = 640, 480

OPEN_OFFSETS = [
    (0.0, 0.15),  # 0 wrist
    (-0.05, 0.10), (-0.09, 0.06), (-0.12, 0.03), (-0.15, 0.00),  # polegar
    (-0.04, 0.02), (-0.045, -0.04), (-0.05, -0.08), (-0.05, -0.12),  # indicador
    (0.0, 0.0), (0.0, -0.06), (0.0, -0.10), (0.0, -0.14),  # médio
    (0.035, 0.005), (0.04, -0.05), (0.045, -0.09), (0.05, -0.12),  # anelar
    (0.07, 0.02), (0.08, -0.02), (0.085, -0.05), (0.09, -0.08),  # mínimo
]

# Punho: pontas dobradas de volta para perto do pulso.
FIST_OFFSETS = list(OPEN_OFFSETS)
for base, pip, dip, tip in [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]:
    bx, by = OPEN_OFFSETS[base]
    FIST_OFFSETS[pip] = (bx, by + 0.02)
    FIST_OFFSETS[dip] = (bx, by + 0.06)
    FIST_OFFSETS[tip] = (bx, by + 0.08)
FIST_OFFSETS[3] = (-0.02, 0.06)
FIST_OFFSETS[4] = (0.01, 0.06)

# Pose indefinida: indicador e médio esticados, anelar e mínimo dobrados.
# É o que a mão vira no meio de um movimento rápido.
OTHER_OFFSETS = list(OPEN_OFFSETS)
for base, pip, dip, tip in [(13, 14, 15, 16), (17, 18, 19, 20)]:
    bx, by = OPEN_OFFSETS[base]
    OTHER_OFFSETS[pip] = (bx, by + 0.02)
    OTHER_OFFSETS[dip] = (bx, by + 0.06)
    OTHER_OFFSETS[tip] = (bx, by + 0.08)


def make_hand(cx, cy, offsets):
    norm = [(cx + dx, cy + dy) for dx, dy in offsets]
    px = [(x * W, y * H) for x, y in norm]
    return Hand(norm=norm, px=px, label="Right")


cfg = Config()
print("pose mão aberta:", classify_pose(make_hand(0.5, 0.5, OPEN_OFFSETS), cfg))
print("pose punho:     ", classify_pose(make_hand(0.5, 0.5, FIST_OFFSETS), cfg))

FPS = 30.0
STEP = 1 / FPS


def run(engine, t, frames):
    """frames = [(cx, offsets), ...] -> lista de ações disparadas."""
    fired = []
    for cx, offsets in frames:
        t += STEP
        a = engine.update(make_hand(cx, 0.5, offsets), t)
        if a:
            fired.append(a)
    return t, fired


def swipe_frames(x0, x1, n=9, offsets=OPEN_OFFSETS):
    return [(x0 + (x1 - x0) * i / (n - 1), offsets) for i in range(n)]


def still_frames(cx, seconds, offsets=OPEN_OFFSETS):
    return [(cx, offsets)] * int(seconds * FPS)


ok = True


def check(name, got, want):
    global ok
    good = got == want
    ok = ok and good
    print(f"{'PASS' if good else 'FALHOU'}  {name}: {got} (esperado {want})")


# 1. swipe para a direita -> NEXT
e = GestureEngine(cfg)
t, fired = run(e, 0.0, swipe_frames(0.3, 0.65))
check("swipe direita", fired, [Action.NEXT])

# 2. swipe para a esquerda -> PREV
e = GestureEngine(cfg)
t, fired = run(e, 0.0, swipe_frames(0.7, 0.35))
check("swipe esquerda", fired, [Action.PREV])

# 3. punho parado -> PLAY_PAUSE uma única vez (mesmo ficando 3 s parado)
e = GestureEngine(cfg)
t, fired = run(e, 0.0, still_frames(0.5, 3.0, FIST_OFFSETS))
check("punho parado", fired, [Action.PLAY_PAUSE])

# 4. rearme: punho -> mão aberta -> punho dispara de novo
e = GestureEngine(cfg)
t, f1 = run(e, 0.0, still_frames(0.5, 1.2, FIST_OFFSETS))
t, f2 = run(e, t, still_frames(0.5, 0.5))
t, f3 = run(e, t, still_frames(0.5, 1.7, FIST_OFFSETS))
check("rearme com mao aberta", f1 + f3, [Action.PLAY_PAUSE, Action.PLAY_PAUSE])

# 5. MÃO ABERTA PARADA NÃO DISPARA NADA (mão em repouso na cadeira/mesa)
e = GestureEngine(cfg)
t, fired = run(e, 0.0, still_frames(0.5, 4.0))
check("mao aberta em repouso nao dispara", fired, [])

# 5b. o mesmo para uma pose indefinida parada (dedos meio esticados)
e = GestureEngine(cfg)
t, fired = run(e, 0.0, still_frames(0.5, 4.0, OTHER_OFFSETS))
check("pose indefinida parada nao dispara", fired, [])

# 6. swipe com punho fechado não pula faixa (mão "guardada")
e = GestureEngine(cfg)
t, fired = run(e, 0.0, swipe_frames(0.3, 0.7, offsets=FIST_OFFSETS))
check("swipe de punho ignorado", fired, [])

# 6b. swipe vale mesmo se a pose virar "indefinido" no meio do movimento
#     (é o que acontece de verdade: a mão borra e inclina ao deslizar)
e = GestureEngine(cfg)
frames = swipe_frames(0.3, 0.65)
frames = [(x, OTHER_OFFSETS if 2 <= i <= 6 else o) for i, (x, o) in enumerate(frames)]
t, fired = run(e, 0.0, frames)
check("swipe com pose indefinida no meio", fired, [Action.NEXT])

# 7. fechar a mão logo depois de um swipe não dispara play/pause (lockout)
e = GestureEngine(cfg)
t, f1 = run(e, 0.0, swipe_frames(0.3, 0.65))
t, f2 = run(e, t, still_frames(0.65, 0.9, FIST_OFFSETS))
check("sem play/pause logo apos swipe", f1 + f2, [Action.NEXT])

# 8. movimento vertical de mao aberta (sem pinca) nao rola nada: rolar exige
# o "dedo na tela". Ver specs/002-rolagem-por-arrasto.md
e = GestureEngine(cfg)
fired = []
t = 0.0
for i in range(9):
    t += STEP
    a = e.update(make_hand(0.5, 0.25 + 0.4 * i / 8, OPEN_OFFSETS), t)
    if a:
        fired.append(a)
check("vertical sem pinca nao rola", fired, [])
# 9. movimento lento/curto não conta como swipe
e = GestureEngine(cfg)
t, fired = run(e, 0.0, swipe_frames(0.48, 0.55, n=15))
check("movimento curto ignorado", fired, [])

# 10. dois swipes seguidos funcionam (com o cooldown respeitado)
e = GestureEngine(cfg)
t, f1 = run(e, 0.0, swipe_frames(0.3, 0.65))
t, f2 = run(e, t, still_frames(0.65, 1.2))
t, f3 = run(e, t, swipe_frames(0.3, 0.65))
check("dois swipes seguidos", f1 + f2 + f3, [Action.NEXT, Action.NEXT])

# 11. voltar a mão aberta para a posição inicial não dispara o gesto contrário
e = GestureEngine(cfg)
t, f1 = run(e, 0.0, swipe_frames(0.3, 0.65))
t, f2 = run(e, t, swipe_frames(0.65, 0.3, n=12))  # retorno, mão ainda aberta
t, f3 = run(e, t, still_frames(0.3, 0.3))
check("retorno nao dispara contrario", f1 + f2 + f3, [Action.NEXT])


# 13. o horizontal mantem o cooldown longo: a MESMA pausa curta nao repete.
e = GestureEngine(cfg)
t, f1 = run(e, 0.0, swipe_frames(0.3, 0.65))
t, f2 = run(e, t, still_frames(0.65, 0.5))
t, f3 = run(e, t, swipe_frames(0.3, 0.65))
check("faixa nao repete com pausa curta", f1 + f2 + f3, [Action.NEXT])

# 14. as interfaces voltaram a garantir: controlador incompleto nem instancia.
from controllers.base import PlayerController, ScrollController


class _PlayerIncompleto(PlayerController):
    def play_pause(self):
        return "x"
    # next_track e previous_track faltando de proposito


class _ScrollIncompleto(ScrollController):
    def scroll_up(self):
        return "x"
    # scroll_down faltando de proposito


for nome, cls in [("player", _PlayerIncompleto), ("scroll", _ScrollIncompleto)]:
    try:
        cls()
        resultado = "instanciou"
    except TypeError:
        resultado = "TypeError"
    check(f"{nome} incompleto nao instancia", resultado, "TypeError")

# --- rolagem por arrasto (spec 002) ---------------------------------------
# Pinca: ponta do indicador (8) encostada na do polegar (4).
PINCA_OFFSETS = list(OPEN_OFFSETS)
PINCA_OFFSETS[8] = OPEN_OFFSETS[4]

from gestures import esta_em_pinca

check("pinca reconhecida", esta_em_pinca(make_hand(0.5, 0.5, PINCA_OFFSETS), cfg), True)
check("mao aberta nao e pinca", esta_em_pinca(make_hand(0.5, 0.5, OPEN_OFFSETS), cfg), False)


def arrastar(engine, t, y0, y1, offsets=PINCA_OFFSETS, n=10):
    """Move a mao de y0 a y1 e soma os ticks de rolagem produzidos."""
    total = 0
    for k in range(n):
        t += STEP
        y = y0 + (y1 - y0) * k / (n - 1)
        if engine.update(make_hand(0.5, y, offsets), t) is Action.SCROLL:
            total += engine.scroll_ticks
    return t, total


# 15. arrastar em pinca rola, e no sentido do celular: para baixo mostra o
# que estava acima, que na roda e o sentido positivo.
e = GestureEngine(cfg)
t, total = arrastar(e, 0.0, 0.3, 0.7)
check("arrasto para baixo rola", total > 0, True)

e = GestureEngine(cfg)
t, total_cima = arrastar(e, 0.0, 0.7, 0.3)
check("arrasto para cima rola ao contrario", total_cima < 0, True)

# 16. proporcional: o dobro do caminho rola aproximadamente o dobro.
e = GestureEngine(cfg)
t, curto = arrastar(e, 0.0, 0.4, 0.5)
e = GestureEngine(cfg)
t, longo = arrastar(e, 0.0, 0.4, 0.6)
check("arrasto dobrado rola ~o dobro", abs(longo - 2 * curto) <= 1, True)

# 17. A CATRACA. E o motivo da spec 002 existir: com a pinca aberta, o
# movimento de volta nao pode desfazer o que o arrasto fez.
e = GestureEngine(cfg)
t, ida = arrastar(e, 0.0, 0.3, 0.7)                          # arrasta agarrado
t, volta = arrastar(e, t, 0.7, 0.3, offsets=OPEN_OFFSETS)    # volta com a mao solta
check("arrasto rolou", ida > 0, True)
check("volta sem pinca nao desfaz", volta, 0)

# 18. soltar e agarrar de novo continua no mesmo sentido, sem se anular.
e = GestureEngine(cfg)
t, a1 = arrastar(e, 0.0, 0.3, 0.7)
t, _ = arrastar(e, t, 0.7, 0.3, offsets=OPEN_OFFSETS)
t, a2 = arrastar(e, t, 0.3, 0.7)
check("dois arrastos somam", a1 > 0 and a2 > 0, True)

# 19. pinca suspende os gestos de musica: arrasto torto nao pula faixa.
e = GestureEngine(cfg)
fired = []
t = 0.0
for k in range(10):
    t += STEP
    off = list(PINCA_OFFSETS)
    a = e.update(make_hand(0.3 + 0.4 * k / 9, 0.5, off), t)   # movimento horizontal amplo
    if a:
        fired.append(a)
check("pinca nao pula faixa", [x for x in fired if x is not Action.SCROLL], [])
print("\n=> TUDO OK" if ok else "\n=> TEM FALHA")
sys.exit(0 if ok else 1)
