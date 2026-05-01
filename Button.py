import pygame


class Button:
    def __init__(self, x, y, width, height, text, font, color, color_hover):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.color_hover = color_hover

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()

        # שינוי צבע אם העכבר מעל הכפתור
        if self.rect.collidepoint(mouse_pos):
            color = self.color_hover
        else:
            color = self.color

        pygame.draw.rect(screen, color, self.rect, border_radius=10)

        text = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False