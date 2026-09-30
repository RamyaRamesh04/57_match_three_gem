import random
import pygame

GRID_SIZE = 8
TILE_SIZE = 60
GEM_COLORS = [
    (220, 50, 50),   # Red
    (50, 200, 50),   # Green
    (50, 100, 240),  # Blue
    (240, 200, 40),  # Yellow
    (180, 50, 220),  # Purple
    (240, 130, 40),  # Orange
]


class Gem:

    def __init__(self, color, target_row, col):
        self.color = color
        self.target_row = target_row
        self.col = col

        # Task 3: Bomb Gem properties
        self.is_bomb = False
        self.bomb_direction = None

        # Start higher up to animate falling down
        self.current_y = (target_row - 2) * TILE_SIZE
        self.target_y = target_row * TILE_SIZE
        self.fall_speed = 12.0

    def update(self):
        if self.current_y < self.target_y:
            self.current_y += self.fall_speed

            if self.current_y > self.target_y:
                self.current_y = self.target_y

    def is_animating(self):
        return self.current_y < self.target_y


class Board:
    """Manages animated gem grid, gravity drops, score, and game limits."""

    def __init__(self, offset_x, offset_y, target_score=500, max_moves=20):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.target_score = target_score
        self.max_moves = max_moves

        self.grid = [
            [None for _ in range(GRID_SIZE)]
            for _ in range(GRID_SIZE)
        ]

        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves

        # Task 2: Cascade multiplier
        self.cascade_multiplier = 1

        self.reset()

    def reset(self):
        """Reset board grid, score, and move limits."""

        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None

        # Reset cascade multiplier
        self.cascade_multiplier = 1

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                color = random.choice(GEM_COLORS)

                gem = Gem(color, r, c)
                gem.current_y = gem.target_y

                self.grid[r][c] = gem

        self.resolve_matches()

        # Reset after initial board setup.
        self.cascade_multiplier = 1

    def is_animating(self):
        """Returns True if any gem is currently dropping down."""

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] and self.grid[r][c].is_animating():
                    return True

        return False

    def swap_gems(self, pos1, pos2):
        """Swap positions and target render coordinates of two gems."""

        r1, c1 = pos1
        r2, c2 = pos2

        g1 = self.grid[r1][c1]
        g2 = self.grid[r2][c2]

        self.grid[r1][c1], self.grid[r2][c2] = g2, g1

        if self.grid[r1][c1]:
            self.grid[r1][c1].target_row = r1
            self.grid[r1][c1].target_y = r1 * TILE_SIZE
            self.grid[r1][c1].current_y = r1 * TILE_SIZE
            self.grid[r1][c1].col = c1

        if self.grid[r2][c2]:
            self.grid[r2][c2].target_row = r2
            self.grid[r2][c2].target_y = r2 * TILE_SIZE
            self.grid[r2][c2].current_y = r2 * TILE_SIZE
            self.grid[r2][c2].col = c2

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2

        return abs(r1 - r2) + abs(c1 - c2) == 1

    def find_matches(self):
        """Scan grid for horizontal and vertical 3-in-a-row matches."""

        matched = set()

        # Horizontal matches
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE - 2):

                if (
                    self.grid[r][c]
                    and self.grid[r][c + 1]
                    and self.grid[r][c + 2]
                    and self.grid[r][c].color
                    == self.grid[r][c + 1].color
                    == self.grid[r][c + 2].color
                ):
                    matched.update([
                        (r, c),
                        (r, c + 1),
                        (r, c + 2)
                    ])

        # Vertical matches
        for r in range(GRID_SIZE - 2):
            for c in range(GRID_SIZE):

                if (
                    self.grid[r][c]
                    and self.grid[r + 1][c]
                    and self.grid[r + 2][c]
                    and self.grid[r][c].color
                    == self.grid[r + 1][c].color
                    == self.grid[r + 2][c].color
                ):
                    matched.update([
                        (r, c),
                        (r + 1, c),
                        (r + 2, c)
                    ])

        return matched

    def find_four_matches(self):
        """
        Task 3:
        Find horizontal and vertical runs containing at least 4
        gems of the same color.

        Returns:
            List of tuples:
            (positions, direction)
        """

        four_matches = []

        # Horizontal runs
        for r in range(GRID_SIZE):
            c = 0

            while c < GRID_SIZE:
                if self.grid[r][c] is None:
                    c += 1
                    continue

                color = self.grid[r][c].color
                start = c

                while (
                    c < GRID_SIZE
                    and self.grid[r][c] is not None
                    and self.grid[r][c].color == color
                ):
                    c += 1

                length = c - start

                if length >= 4:
                    positions = [
                        (r, col)
                        for col in range(start, c)
                    ]
                    four_matches.append(
                        (positions, "row")
                    )

        # Vertical runs
        for c in range(GRID_SIZE):
            r = 0

            while r < GRID_SIZE:
                if self.grid[r][c] is None:
                    r += 1
                    continue

                color = self.grid[r][c].color
                start = r

                while (
                    r < GRID_SIZE
                    and self.grid[r][c] is not None
                    and self.grid[r][c].color == color
                ):
                    r += 1

                length = r - start

                if length >= 4:
                    positions = [
                        (row, c)
                        for row in range(start, r)
                    ]
                    four_matches.append(
                        (positions, "column")
                    )

        return four_matches

    def activate_bomb(self, position, matched):
        """
        Task 3:
        Activate a Bomb Gem and add its complete row or column
        to the matched set.
        """

        r, c = position
        gem = self.grid[r][c]

        if not gem or not gem.is_bomb:
            return

        if gem.bomb_direction == "row":

            for col in range(GRID_SIZE):
                if self.grid[r][col]:
                    matched.add((r, col))

        elif gem.bomb_direction == "column":

            for row in range(GRID_SIZE):
                if self.grid[row][c]:
                    matched.add((row, c))

    def create_bomb(self, position, direction):
        """
        Task 3:
        Convert a normal gem into a Bomb Gem.
        """

        r, c = position
        gem = self.grid[r][c]

        if gem:
            gem.is_bomb = True
            gem.bomb_direction = direction

    def drop_and_refill(self):
        """Drop existing gems down and create new gems at the top."""

        for c in range(GRID_SIZE):

            empty_slots = 0

            # Process this column from bottom to top
            for r in range(GRID_SIZE - 1, -1, -1):

                if self.grid[r][c] is None:
                    empty_slots += 1

                elif empty_slots > 0:

                    gem = self.grid[r][c]

                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    gem.col = c

                    self.grid[r + empty_slots][c] = gem
                    self.grid[r][c] = None

            # Create new gems at the top
            for r in range(empty_slots):

                color = random.choice(GEM_COLORS)

                gem = Gem(color, r, c)

                gem.current_y = -(
                    (empty_slots - r) * TILE_SIZE
                )

                self.grid[r][c] = gem

    def resolve_matches(self):
        """
        Resolve all matches created by the current swap.

        Task 2:
        First match  = 1x
        Second match = 2x
        Third match  = 3x

        Task 3:
        A 4-in-a-row creates a Bomb Gem.
        Existing Bomb Gems can clear their row or column.
        """

        total_cleared = 0

        # Start every new chain at 1x
        self.cascade_multiplier = 1

        while True:

            matches = self.find_matches()

            if not matches:
                break

            # -------------------------------------------------
            # Task 3: Detect Bomb Gem activations
            # -------------------------------------------------

            original_matches = set(matches)

            for position in list(original_matches):

                r, c = position
                gem = self.grid[r][c]

                if gem and gem.is_bomb:
                    self.activate_bomb(position, matches)

            # -------------------------------------------------
            # Task 3: Detect 4-in-a-row matches
            # -------------------------------------------------

            four_matches = self.find_four_matches()

            bombs_to_create = []

            for positions, direction in four_matches:

                # If this 4-match already contains an existing
                # bomb, let the existing bomb handle activation.
                existing_bomb = False

                for position in positions:
                    r, c = position
                    gem = self.grid[r][c]

                    if gem and gem.is_bomb:
                        existing_bomb = True
                        break

                if not existing_bomb:
                    # Choose the middle gem as the Bomb Gem.
                    bomb_position = positions[len(positions) // 2]

                    bombs_to_create.append(
                        (bomb_position, direction)
                    )

            # -------------------------------------------------
            # Task 2: Cascade scoring
            # -------------------------------------------------

            cleared = len(matches)

            self.score += (
                cleared
                * 10
                * self.cascade_multiplier
            )

            total_cleared += cleared

            # -------------------------------------------------
            # Remove matched gems
            # -------------------------------------------------

            bomb_positions = set(
                position
                for position, direction in bombs_to_create
            )

            for r, c in matches:

                if (r, c) not in bomb_positions:
                    self.grid[r][c] = None

            # -------------------------------------------------
            # Create Bomb Gems after clearing the match.
            #
            # The selected gem position was kept instead of
            # being removed.
            # -------------------------------------------------

            for position, direction in bombs_to_create:

                r, c = position

                # The original gem is still present because we
                # excluded this position from the clearing step.
                if self.grid[r][c]:

                    self.create_bomb(
                        position,
                        direction
                    )

            # Drop gems and refill empty spaces
            self.drop_and_refill()

            # Next automatic match gets a higher multiplier
            self.cascade_multiplier += 1

        # Chain is finished.
        # Reset multiplier for the next swap.
        self.cascade_multiplier = 1

        return total_cleared

    def process_swap(self, pos1, pos2):
        """
        Process a gem swap.

        Task 1:
        Invalid swaps do not consume a move.

        Task 2:
        Cascade scoring is handled by resolve_matches().

        Task 3:
        Bomb Gems can participate in matches and activate
        their row or column.
        """

        if (
            not self.is_adjacent(pos1, pos2)
            or self.is_game_over()
            or self.is_animating()
        ):
            return False

        # Perform the swap
        self.swap_gems(pos1, pos2)

        # Check whether the swap creates a match
        matches = self.find_matches()

        # Task 3:
        # A Bomb Gem can also be activated when it is involved
        # in a valid swap.
        r1, c1 = pos1
        r2, c2 = pos2

        gem1 = self.grid[r1][c1]
        gem2 = self.grid[r2][c2]

        bomb_swap = (
            (gem1 and gem1.is_bomb)
            or
            (gem2 and gem2.is_bomb)
        )

        # Invalid swap:
        # revert it and do NOT consume a move.
        if not matches and not bomb_swap:
            self.swap_gems(pos1, pos2)
            return False

        # Valid swap:
        # consume exactly one move.
        self.moves_remaining -= 1

        # Resolve the complete cascade.
        # resolve_matches() handles:
        # 1x, 2x, 3x, ...
        # and Bomb Gem activation.
        self.resolve_matches()

        return True

    def is_game_over(self):
        return (
            self.score >= self.target_score
            or self.moves_remaining <= 0
        )

    def check_result(self):

        if self.score >= self.target_score:
            return "WIN"

        if self.moves_remaining <= 0:
            return "LOSS"

        return None

    def update(self):

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):

                if self.grid[r][c]:
                    self.grid[r][c].update()

    def render(self, surface):

        board_rect = pygame.Rect(
            self.offset_x,
            self.offset_y,
            GRID_SIZE * TILE_SIZE,
            GRID_SIZE * TILE_SIZE
        )

        pygame.draw.rect(
            surface,
            (20, 22, 28),
            board_rect,
            border_radius=8
        )

        pygame.draw.rect(
            surface,
            (60, 65, 75),
            board_rect,
            width=3,
            border_radius=8
        )

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):

                gem = self.grid[r][c]

                if gem:

                    x = self.offset_x + c * TILE_SIZE
                    y = self.offset_y + gem.current_y

                    tile_rect = pygame.Rect(
                        x + 2,
                        y + 2,
                        TILE_SIZE - 4,
                        TILE_SIZE - 4
                    )

                    # Normal gem
                    pygame.draw.rect(
                        surface,
                        gem.color,
                        tile_rect,
                        border_radius=10
                    )

                    pygame.draw.rect(
                        surface,
                        (255, 255, 255),
                        tile_rect,
                        width=1,
                        border_radius=10
                    )

                    # -------------------------------------------------
                    # Task 3: Bomb Gem visual
                    # -------------------------------------------------

                    if gem.is_bomb:

                        center_x = x + TILE_SIZE // 2
                        center_y = int(
                            y + TILE_SIZE // 2
                        )

                        # White circle inside the gem
                        pygame.draw.circle(
                            surface,
                            (255, 255, 255),
                            (center_x, center_y),
                            17
                        )

                        # Dark inner circle
                        pygame.draw.circle(
                            surface,
                            (30, 30, 30),
                            (center_x, center_y),
                            11
                        )

                        # Cross to make the Bomb Gem obvious
                        pygame.draw.line(
                            surface,
                            (255, 255, 255),
                            (
                                center_x - 7,
                                center_y - 7
                            ),
                            (
                                center_x + 7,
                                center_y + 7
                            ),
                            3
                        )

                        pygame.draw.line(
                            surface,
                            (255, 255, 255),
                            (
                                center_x + 7,
                                center_y - 7
                            ),
                            (
                                center_x - 7,
                                center_y + 7
                            ),
                            3
                        )

                if self.selected == (r, c):

                    sel_x = self.offset_x + c * TILE_SIZE
                    sel_y = self.offset_y + r * TILE_SIZE

                    sel_rect = pygame.Rect(
                        sel_x + 2,
                        sel_y + 2,
                        TILE_SIZE - 4,
                        TILE_SIZE - 4
                    )

                    pygame.draw.rect(
                        surface,
                        (255, 255, 255),
                        sel_rect,
                        width=4,
                        border_radius=10
                    )