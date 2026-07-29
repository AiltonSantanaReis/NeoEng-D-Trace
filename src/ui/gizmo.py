# src/ui/gizmo.py
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QFont
from PySide6.QtCore import Qt, QPointF


class TransformGizmo:
    """
    Gizmo de Transformação 2D (Move Tool).
    Renderiza em Screen Space para manter tamanho constante e usabilidade.
    """

    # Enum de Estados
    NONE = 0
    AXIS_X = 1
    AXIS_Y = 2
    CENTER = 3

    def __init__(self):
        self.active_axis = self.NONE
        self.hover_axis = self.NONE

        # Posição na TELA (Pixels)
        self.screen_pos = QPointF(0, 0)

        # Configuração Visual (Estilo Engine)
        self.arm_length = 80.0  # Comprimento da haste
        self.arrow_size = 18.0  # Tamanho da ponta (Aumentado)
        self.handle_thickness = 5.0  # Espessura da linha para clique

        # Cores Padrão da Indústria (RGB = XYZ)
        self.color_x = QColor(255, 60, 60)  # Vermelho
        self.color_y = QColor(60, 255, 60)  # Verde
        self.color_center = QColor(255, 255, 255)  # Branco
        self.color_hover = QColor(255, 255, 0)  # Amarelo
        self.color_dimmed = QColor(100, 100, 100, 150) # Cor para eixos inativos

    def set_screen_position(self, pos: QPointF):
        """Atualiza a posição onde o gizmo será desenhado na tela."""
        self.screen_pos = pos

    def hit_test(self, mouse_pos: QPointF) -> int:
        """
        Verifica colisão do mouse com o Gizmo.
        mouse_pos: Coordenadas da tela.
        """
        dx = mouse_pos.x() - self.screen_pos.x()
        dy = mouse_pos.y() - self.screen_pos.y()

        # 1. Teste do Centro (Prioridade máxima)
        # Raio de clique do centro: 15px
        if (dx * dx + dy * dy) <= (15 * 15):
            return self.CENTER

        # Tolerância para clicar nas linhas
        hit_width = 15.0 

        # 2. Teste Eixo X (Horizontal para direita)
        # Mouse deve estar entre 0 e Length no X, e perto de 0 no Y
        if (0 <= dx <= self.arm_length + self.arrow_size) and (
            abs(dy) <= hit_width
        ):
            return self.AXIS_X

        # 3. Teste Eixo Y (Vertical para baixo/cima dependendo da coord)
        # Assumindo Y+ para baixo (padrão Qt Widget)
        if (0 <= dy <= self.arm_length + self.arrow_size) and (
            abs(dx) <= hit_width
        ):
            return self.AXIS_Y

        return self.NONE

    def update_hover(self, mouse_pos: QPointF):
        prev = self.hover_axis
        self.hover_axis = self.hit_test(mouse_pos)
        return prev != self.hover_axis

    def draw(self, painter: QPainter):
        """Desenha o gizmo. O Painter DEVE estar em coordenadas de tela."""
        painter.save()
        # Move a origem para o centro do objeto na tela
        painter.translate(self.screen_pos)

        # Configuração de Renderização
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Determina opacidade baseada na atividade
        # Se um eixo está ativo, o outro fica apagado (dimmed)
        opacity_x = 1.0
        opacity_y = 1.0
        
        if self.active_axis != self.NONE:
            if self.active_axis == self.AXIS_X: opacity_y = 0.3
            if self.active_axis == self.AXIS_Y: opacity_x = 0.3

        # --- EIXO X (Vermelho) ---
        is_hover_x = (self.hover_axis == self.AXIS_X) or (
            self.active_axis == self.AXIS_X
        )
        color_x = self.color_hover if is_hover_x else self.color_x
        if opacity_x < 1.0: 
            color_x = QColor(color_x) # Clone to modify alpha
            color_x.setAlphaF(opacity_x)

        pen_x = QPen(color_x, 3)
        pen_x.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_x)
        painter.setBrush(QBrush(color_x))

        # Linha
        painter.drawLine(0, 0, int(self.arm_length), 0)

        # Seta (Cone)
        arrow_x = QPolygonF(
            [
                QPointF(self.arm_length + self.arrow_size, 0),
                QPointF(self.arm_length, -self.arrow_size / 2.5),
                QPointF(self.arm_length, self.arrow_size / 2.5),
            ]
        )
        painter.drawPolygon(arrow_x)

        # Label X
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(int(self.arm_length + 20), 5, "X")

        # --- EIXO Y (Verde) ---
        is_hover_y = (self.hover_axis == self.AXIS_Y) or (
            self.active_axis == self.AXIS_Y
        )
        color_y = self.color_hover if is_hover_y else self.color_y
        if opacity_y < 1.0: 
            color_y = QColor(color_y)
            color_y.setAlphaF(opacity_y)

        pen_y = QPen(color_y, 3)
        pen_y.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_y)
        painter.setBrush(QBrush(color_y))

        # Linha (Y+ para baixo no Qt Screen Space)
        painter.drawLine(0, 0, 0, int(self.arm_length))

        # Seta
        arrow_y = QPolygonF(
            [
                QPointF(0, self.arm_length + self.arrow_size),
                QPointF(-self.arrow_size / 2.5, self.arm_length),
                QPointF(self.arrow_size / 2.5, self.arm_length),
            ]
        )
        painter.drawPolygon(arrow_y)

        # Label Y
        painter.drawText(-5, int(self.arm_length + 25), "Y")

        # --- CENTRO (Letra C de arraste livre) ---
        # Desenha por último para ficar no topo
        is_hover_c = (self.hover_axis == self.CENTER) or (
            self.active_axis == self.CENTER
        )
        color_c = self.color_hover if is_hover_c else self.color_center

        # Fundo circular para destacar e facilitar clique
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawEllipse(-15, -15, 30, 30)

        # Borda e Texto
        painter.setPen(QPen(color_c, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(-15, -15, 30, 30) # Circle outline
        
        painter.setPen(color_c)
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        # Centraliza texto (aprox)
        painter.drawText(-6, 5, "C")

        painter.restore()