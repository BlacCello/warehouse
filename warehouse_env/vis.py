import numpy as np
import pygame

GRAY = (150, 150, 150)
WHITE = (255, 255, 255)
GUI_SCALING = 60
BLACK = (0, 0, 0)
BIN = (139, 69, 16)
ITEM = (200, 80, 40)


class WarehouseGui:
    def __init__(self, grid_size, max_items_in_env):
        self.scale = GUI_SCALING
        self.warehouse_display_size = self.scale * np.array(grid_size)

        pygame.init()

        self.screen = pygame.display.set_mode(
            (self.warehouse_display_size[1], self.warehouse_display_size[0] + 30)
        )
        self.basic_font = pygame.font.Font("freesansbold.ttf", 18)
        self.item_size = self.scale / max_items_in_env
        pygame.display.set_caption("Chaotic Warehouse")
        self._make_background()
        pygame.display.update()

    def close(self):
        pygame.display.quit()
        pygame.quit()

    def _make_background(self):
        self.screen.fill(WHITE)
        pygame.draw.rect(
            self.screen,
            GRAY,
            pygame.Rect(
                0, self.warehouse_display_size[0], self.warehouse_display_size[1], 30
            ),
        )

    def frame_step(self, agent, bins, staging_in, staging_out, transaction):
        pygame.event.get()
        self._make_background()
        self._draw_agent(agent)
        for b in bins:
            self._draw_bins(b)
        self._draw_bins(staging_in)
        self._draw_bins(staging_out, use_slots=False)
        self._draw_incoming(staging_out)
        self._print_text(transaction.to_string(), 0, self.warehouse_display_size[0])

        pygame.display.update()

        image_data = pygame.surfarray.array3d(pygame.display.get_surface())
        return image_data

    @staticmethod
    def _make_text_objects(text, font, color):
        surf = font.render(text, True, color)
        return surf, surf.get_rect()

    def _draw_agent(self, agent):
        agent_picture = pygame.image.load("warehouse_env/img/agent.png")
        agent_picture = pygame.transform.scale(agent_picture, (self.scale, self.scale))
        agent_rectangle = agent_picture.get_rect()
        agent_rectangle = agent_rectangle.move(
            (agent.agent_pos[1] * self.scale, agent.agent_pos[0] * self.scale)
        )  # needs to be flipped for pygame coordinates
        self.screen.blit(agent_picture, agent_rectangle)
        if agent.loaded_item is not None:
            left = agent.agent_pos[1] * self.scale + int(self.scale / 2)
            top = agent.agent_pos[0] * self.scale + int(self.scale / 2)
            ws_pic = pygame.image.load("warehouse_env/img/item.png")
            ws_pic = pygame.transform.scale(
                ws_pic, (int(self.scale / 2), int(self.scale / 2))
            )
            ws_rectangle = ws_pic.get_rect()
            ws_rectangle = ws_rectangle.move(
                (left, top)
            )  # needs to be flipped for pygame coordinates
            self.screen.blit(ws_pic, ws_rectangle)

            self._print_text(agent.loaded_item.slot, left, top)

    def _draw_bins(self, bin, use_slots=True):
        pygame.draw.rect(
            self.screen,
            BIN,
            pygame.Rect(
                bin.pos[1] * self.scale, bin.pos[0] * self.scale, self.scale, self.scale
            ),
        )
        if use_slots:  # staging out is block to get slots, just skip
            index = 1
            for item in bin.get_slots().values():
                left = bin.pos[1] * self.scale + 0.1 * self.scale
                top = bin.pos[0] * self.scale + self.scale - self.item_size * index
                pygame.draw.rect(
                    self.screen,
                    ITEM,
                    pygame.Rect(
                        left,
                        top,
                        self.scale - 0.2 * self.scale,
                        self.item_size - 0.1 * self.scale,
                    ),
                )
                index += 1

                self._print_text(item.slot, left, top)

    def _draw_incoming(self, staging_out):
        left = staging_out.pos[1] * self.scale + 0.1 * self.scale
        index = 1
        for item_id in staging_out.incoming:
            top = staging_out.pos[0] * self.scale + self.scale - self.item_size * index
            self._print_text("->"+str(item_id), left, top)
            index += 1


    def _print_text(self, text, left, top):
        item_id_text, item_id_rectangle = self._make_text_objects(
            str(text), self.basic_font, BLACK
        )
        item_id_rectangle = item_id_rectangle.move(
            left, top
        )  # needs to be flipped for pygame coordinates
        self.screen.blit(item_id_text, item_id_rectangle)
