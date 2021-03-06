# -*- coding: utf8 -*-

from FGAme.mathutils import Vector, dot, area, center_of_mass, clip, pi
from FGAme.mathutils import shadow_x, shadow_y

from FGAme.physics.collision import Collision
from FGAme.physics import Circle, AABB, Poly, Rectangle
from FGAme.util import multifunction

u_x = Vector(1, 0)
DEFAULT_DIRECTIONS = [u_x.rotated(n * pi / 12) for n in
                      [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11]]


class CollisionError(Exception):

    '''Declara que não existem colisões disponíveis para os dois tipos de
    objetos'''
    pass


def get_collision_generic(A, B):
    '''Retorna uma colisão genérica definido pela CBB dos objetos A e B'''

    rA = A.cbb_radius
    rB = B.cbb_radius
    delta = B._pos - A._pos
    if delta.norm() < rA + rB:
        n = delta.normalized()
        D = rA + rB - delta.norm()
        pos = A._pos + (rA - D / 2) * n
        return Collision(A, B, pos=pos, normal=n, delta=D)
    else:
        return None


@multifunction(None, None)
def get_collision(A, B):
    '''Retorna um objeto de colisão caso ocorra uma colisão com o objeto
    other. Caso não haja colisão, retorna None.

    Esta função é implementada por multidispatch. As classes derivadas de
    PhysicsObject devem registrar explicitamente a colisão entre todos os pares
    suportados (ex.: Circle com Circle, Circle com AABB, etc). Caso não tenha
    nenhuma implementação registrada, então utiliza-se a lógica de AABB's.'''

    tA = type(A).__name__
    tB = type(B).__name__
    raise CollisionError('no collision defined for: (%s, %s)' % (tA, tB))


###############################################################################
#                      Colisões entre objetos do mesmo tipo
###############################################################################
@get_collision.dispatch(AABB, AABB)
def collision_aabb(A, B):
    '''Retorna uma colisão com o objeto other considerando apenas a caixas
    de contorno alinhadas ao eixo.'''

    # Detecta colisão pelas sombras das caixas de contorno
    rx, ry = B._pos - A._pos
    shadowx = A._delta_x + B._delta_x - abs(rx)
    shadowy = A._delta_y + B._delta_y - abs(ry)
    if shadowx <= 0 or shadowy <= 0:
        return None

    # Calcula ponto de colisão
    x_col = max(A.xmin, B.xmin) + shadowx / 2.
    y_col = max(A.ymin, B.ymin) + shadowy / 2.
    pos_col = Vector(x_col, y_col)

    # Define sinal dos vetores normais: colisões tipo PONG
    if shadowx > shadowy:
        n = Vector(0, (1 if A.ymin < B.ymin else -1))
        delta = shadowy
    else:
        n = Vector((1 if A.xmin < B.xmin else -1), 0)
        delta = shadowx

    return Collision(A, B, pos=pos_col, normal=n, delta=delta)


@get_collision.dispatch(Circle, Circle)
def collision_circle(A, B):
    '''Testa a colisão pela distância dos centros'''

    rA = A.cbb_radius
    rB = B.cbb_radius
    delta = B._pos - A._pos
    if delta.norm() < rA + rB:
        n = delta.normalized()
        D = rA + rB - delta.norm()
        pos = A._pos + (rA - D / 2) * n
        return Collision(A, B, pos=pos, normal=n, delta=D)
    else:
        return None


@get_collision.dispatch(Poly, Poly)
def collision_poly(A, B, directions=None):
    '''Implementa a colisão entre dois polígonos arbitrários'''

    # Cria a lista de direções a partir das normais do polígono
    if directions is None:
        if A.num_normals + B.num_normals < 9:
            directions = A.get_normals() + B.get_normals()
        else:
            directions = DEFAULT_DIRECTIONS

    # Testa se há superposição de sombras em todas as direções consideradas
    # e calcula o menor valor para sombra e a direção normal
    min_shadow = float('inf')
    norm = None
    for u in directions:
        A_coords = [round(dot(pt, u), 6) for pt in A.vertices]
        B_coords = [round(dot(pt, u), 6) for pt in B.vertices]
        Amax, Amin = max(A_coords), min(A_coords)
        Bmax, Bmin = max(B_coords), min(B_coords)
        minmax, maxmin = min(Amax, Bmax), max(Amin, Bmin)
        shadow = minmax - maxmin
        if shadow < 0:
            return None
        elif shadow < min_shadow:
            min_shadow = shadow
            norm = u

    # Determina o sentido da normal
    if dot(A._pos, norm) > dot(B._pos, norm):
        norm = -norm

    # Computa o polígono de intersecção e usa o seu centro de massa como ponto
    # de colisão
    try:
        clipped = clip(A.vertices, B.vertices)
    # não houve superposição (talvez por usar normais aproximadas)
    except ValueError:
        return None

    if area(clipped) == 0:
        return None
    col_pt = center_of_mass(clipped)
    return Collision(A, B, pos=col_pt, normal=norm, delta=min_shadow)


###############################################################################
#                 Colisões entre objetos de tipos diferentes
###############################################################################

@get_collision.dispatch(Circle, AABB)
def circle_aabb(A, B):
    # TODO: implementar direito, está utilizando AABBs
    r = A.cbb_radius
    x, y = A._pos
    Axmin, Axmax = x - r, x + r
    Aymin, Aymax = y - r, y + r

    x, y = B._pos
    dx, dy = B._delta_x, B._delta_y
    Bxmin, Bxmax = x - dx, x + dx
    Bymin, Bymax = y - dy, y + dy

    shadowx = min(Axmax, Bxmax) - max(Axmin, Bxmin)
    shadowy = min(Aymax, Bymax) - max(Aymin, Bymin)
    if shadowx < 0 or shadowy < 0:
        return None

    # Calcula ponto de colisão
    x_col = max(A.xmin, B.xmin) + shadowx / 2.
    y_col = max(A.ymin, B.ymin) + shadowy / 2.
    pos_col = Vector(x_col, y_col)

    # Define sinal dos vetores normais: colisões tipo PONG
    if shadowx > shadowy:
        n = Vector(0, (1 if A.ymin < B.ymin else -1))
    else:
        n = Vector((1 if A.xmin < B.xmin else -1), 0)

    return Collision(A, B, pos=pos_col, normal=n)


@get_collision.dispatch(Poly, AABB)
def poly_aabb(A, B):
    '''Implementa a colisão entre um polígono arbitrário e uma caixa AABB'''

    if shadow_x(A, B) < 0 or shadow_y(A, B) < 0:
        return None

    B_poly = Rectangle(bbox=B.bbox, density=B.density)
    col = collision_poly(A, B_poly)
    if col is not None:
        col.objects = (A, B)
        return col


@get_collision.dispatch(AABB, Poly)
def aabb_poly(A, B):
    '''Implementa a colisão entre um polígono arbitrário e uma caixa AABB'''

    if shadow_x(A, B) < 0 or shadow_y(A, B) < 0:
        return None

    A_poly = Rectangle(bbox=A.bbox, density=A.density)
    col = collision_poly(A_poly, B)
    if col is not None:
        col.objects = (A, B)
        return col
