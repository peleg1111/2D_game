__author__ = 'Peleg Etzioni'
import pygame, os , sys

sys.path.insert(0, os.path.dirname(__file__))# רשימת הקבצים שimport מחפש בהם קבצים להרצה
#  מכניס את התיקייה שבה נמצא הקובץ לרשימה כך שimport יוכל למצוא אותו ולהריץ מתוך הcmd


class Slider:
    def __init__(self, x, y, width, min_val, max_val, start_val, txt = None):
        self.x = x
        self.y = y
        self.width = width
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.dragging = False

        self.txt = txt

        self.rect = pygame.Rect(x, y, width, 9)
        self.handle_radius = 12
        self.current_x = self.get_x_by_val(start_val)

    def get_x_by_val(self, val):
        percent = (val - self.min_val) / (self.max_val - self.min_val)
        return self.x + percent * self.width

    def get_val(self):
        x = self.current_x
        percent = (x - self.x) / self.width # (current - start) / width == value [percent]
        percent = max(0, min(1, percent)) # מונע יציא מהגבולות
        return self.min_val + percent * (self.max_val - self.min_val)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos

            # האם השחקן לחץ בעיגול הקטן של ה slider
            if abs(mx - self.current_x) < self.handle_radius + 4 and abs(my - self.y) < self.handle_radius + 4:
                self.dragging = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.current_x = max(self.x, min(self.x + self.width, event.pos[0])) # מעדכן את המיקום תוך שמירה על הגבולות
            self.val = self.get_val()


    def draw(self, screen):
        pygame.draw.rect(screen, (80, 80, 80), self.rect, border_radius=3)

        x = pygame.Rect(self.x, self.y, self.current_x - self.x, 9)
        pygame.draw.rect(screen, (100, 150, 255), x, border_radius=3)

        pygame.draw.circle(screen, (200, 200, 200), (int(self.current_x), self.y + 3), self.handle_radius)

        if self.txt:
            font = pygame.font.SysFont("Arial", 50)
            text = font.render(self.txt, True, (255, 255, 255))
            screen.blit(text, (self.x * 0.4, self.y - 30))


    def is_dragging(self):
        return self.dragging