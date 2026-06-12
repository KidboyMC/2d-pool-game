import pygame
import pymunk
import math
from config import GameConfig
from ui_objects import Button


class GameRenderer:
    """
    Kelas untuk menangani semua operasi rendering/drawing di layar.
    Encapsulation: semua logika rendering dikelola di sini.
    
    Tanggung jawab:
    - Draw meja pool, bola, stick
    - Draw UI elements (power meter, text, tombol)
    - Draw prediksi trajectory bola (garis gaya dan pantulan)
    - Draw game over/win screen
    """
    
    def __init__(self, screen, table_image, ball_images, fonts):
        """
        Inisialisasi renderer.
        
        Args:
            screen: pygame display surface (layar game)
            table_image: pygame Surface berisi gambar meja pool
            ball_images: List of pygame Surface berisi gambar setiap bola
            fonts: Dict dengan keys 'normal' dan 'large' (pygame font objects)
        """
        self.screen = screen              # Surface untuk menggambar
        self.table_image = table_image    # Gambar meja pool
        self.ball_images = ball_images    # List gambar bola (16 bola)
        self.font = fonts['normal']       # Font normal (size 30)
        self.large_font = fonts['large']  # Font besar (size 60)
        
        # ========== BUAT RETRY BUTTON ==========
        # Hitung posisi button agar berada di tengah screen
        button_width = 200
        button_height = 60
        button_x = (GameConfig.SCREEN_WIDTH - button_width) // 2    # Center horizontal
        button_y = (GameConfig.SCREEN_HEIGHT - button_height) // 2 + 100  # Center vertical + 100px offset
        
        # Buat button retry dengan konfigurasi warna
        self.retry_button = Button(
            button_x, button_y, button_width, button_height,
            "RETRY",  # Text tombol
            self.large_font,
            GameConfig.BUTTON_COLOR,          # Warna normal
            GameConfig.BUTTON_HOVER_COLOR,    # Warna hover
            GameConfig.BUTTON_ACTIVE_COLOR    # Warna aktif
        )
    
    def draw_text(self, text, font, color, x, y):
        """
        Menggambar text pada posisi (x, y) dengan font dan warna tertentu.
        Utility method untuk rendering text.
        
        Args:
            text: String teks yang akan digambar
            font: pygame font object
            color: tuple RGB warna text
            x, y: Posisi top-left text
        """
        # Render text ke surface
        img = font.render(text, True, color)
        # Gambar ke screen
        self.screen.blit(img, (x, y))
    
    def draw_table(self):
        """
        Menggambar meja pool sebagai background.
        Gambar table_image ditarik ke seluruh area game (0,0) sampai (SCREEN_WIDTH, SCREEN_HEIGHT).
        """
        self.screen.blit(self.table_image, (0, 0))
    
    def draw_balls(self, balls):
        """
        Menggambar semua bola di layar.
        Setiap bola digambar menggunakan posisi dan radius-nya.
        
        Args:
            balls: List of Ball objects yang akan digambar
        """
        for i, ball in enumerate(balls):
            # Cek apakah ball_images tersedia untuk bola ini
            if i < len(self.ball_images):
                # Hitung top-left corner untuk menggambar (center - radius)
                ball_pos = ball.get_position()
                x = ball_pos[0] - ball.radius
                y = ball_pos[1] - ball.radius
                
                # Gambar bola ke screen
                self.screen.blit(self.ball_images[i], (x, y))
    
    def draw_bottom_panel(self, current_player, potted_balls):
        """
        Menggambar panel informasi di bawah meja pool.
        Panel menampilkan:
        - Jumlah lives sisa (nyawa)
        - Gambar-gambar bola yang sudah potted (masuk lubang)
        
        Args:
            lives: int, jumlah nyawa sisa
            potted_balls: List of pygame Surface berisi gambar bola yang sudah potted
        """
        # Draw background panel (dark gray rectangle)
        pygame.draw.rect(self.screen, GameConfig.BG,
            (0, GameConfig.SCREEN_HEIGHT, GameConfig.SCREEN_WIDTH, GameConfig.BOTTOM_PANEL))
        
        turn_text = f"PLAYER {current_player} TURN"
        self.draw_text(turn_text, self.font, GameConfig.WHITE,
            GameConfig.SCREEN_WIDTH - 250, GameConfig.SCREEN_HEIGHT + 10)
        
        # Draw gambar-gambar bola yang sudah potted (kiri ke kanan)
        for i, ball in enumerate(potted_balls):
            self.screen.blit(ball, (10 + (i * 50), GameConfig.SCREEN_HEIGHT + 10))
    
    def draw_predictive_line(self, cue_ball, angle):
        """
        Menggambar garis prediksi trajectory bola saat akan di-shoot.
        Garis ini menunjukkan ke arah mana bola akan bergerak.
        
        Proses:
        1. Hitung arah initial (dari cue angle)
        2. Cari collision point dengan obstacle
        3. Hitung reflected direction (pantulan)
        4. Draw garis dari start ke collision
        5. Draw reflected line dalam warna merah
        
        Args:
            cue_ball: Ball object (bola putih)
            angle: float, sudut stick dalam derajat
        """
        # Convert angle ke radians dan buat direction vector
        physics_angle = -math.radians(angle)
        direction = pymunk.Vec2d(
            -math.cos(physics_angle),
            -math.sin(physics_angle)
        )
        
        # Tentukan start point (dari permukaan bola)
        start = cue_ball.body.position + direction * cue_ball.radius
        
        # Tentukan end point (jauh ke depan, 2000 pixel)
        end = start + direction * 2000
        
        # Query collision dengan segment dari start ke end
        hits = cue_ball.space.segment_query(start, end, 0.1, pymunk.ShapeFilter())
        
        # Cari collision terdekat (closest hit)
        closest_hit = None
        closest_dist = float("inf")
        
        for h in hits:
            # Skip bola cue sendiri
            if h.shape is cue_ball.shape:
                continue
            
            # Hitung distance dari start ke hit point
            dist = (h.point - start).length
            
            # Update closest hit jika collision ini lebih dekat
            if dist < closest_dist:
                closest_dist = dist
                closest_hit = h
        
        # Jika tidak ada collision, gambar garis lurus saja
        if closest_hit is None:
            pygame.draw.line(self.screen, GameConfig.WHITE, start, end, 2)
            return
        
        # Ada collision, gambar garis ke collision point
        collision_point = closest_hit.point
        pygame.draw.line(self.screen, GameConfig.WHITE, start, collision_point, 3)
        
        # ========== HITUNG REFLECTED LINE ==========
        # Ambil normal vector dari collision surface
        normal = closest_hit.normal
        
        # Normalize incoming direction
        incoming = direction.normalized()
        
        # Hitung reflected direction menggunakan formula: r = i - 2(i·n)n
        # Ini adalah reflection formula dalam physics
        reflected = incoming - 2 * incoming.dot(normal) * normal
        
        # Tentukan end point untuk reflected line
        bounce_end = collision_point + reflected * 100
        
        # Gambar reflected line dalam warna merah
        pygame.draw.line(self.screen, GameConfig.RED, collision_point, bounce_end, 2)
    
    def draw_game_over(self):
        """
        Menggambar game over screen.
        Screen menampilkan:
        - Semi-transparent overlay (untuk fade effect)
        - Text "GAME OVER" dalam warna merah
        - Tombol RETRY untuk restart game
        """
        # ========== BUAT SEMI-TRANSPARENT OVERLAY ==========
        overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        overlay.set_alpha(100)  # Alpha = 100 (40% opacity)
        overlay.fill((0, 0, 0))  # Warna hitam
        self.screen.blit(overlay, (0, 0))
        
        # ========== DRAW TEXT "GAME OVER" ==========
        self.draw_text("GAME OVER", self.large_font, GameConfig.RED,
            GameConfig.SCREEN_WIDTH / 2 - 200, GameConfig.SCREEN_HEIGHT / 2 - 100)
        
        # ========== DRAW RETRY BUTTON ==========
        self.retry_button.draw(self.screen)
    
    def draw_win(self):
        """
        Menggambar win screen (ketika semua bola berhasil potted).
        Screen menampilkan:
        - Semi-transparent overlay
        - Text "YOU WIN!" dalam warna merah
        - Tombol RETRY untuk main lagi
        """
        # ========== BUAT SEMI-TRANSPARENT OVERLAY ==========
        overlay = pygame.Surface((GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT))
        overlay.set_alpha(100)  # Alpha = 100 (40% opacity)
        overlay.fill((0, 0, 0))  # Warna hitam
        self.screen.blit(overlay, (0, 0))
        
        # ========== DRAW TEXT "YOU WIN!" ==========
        self.draw_text("YOU WIN!", self.large_font, GameConfig.RED,
            GameConfig.SCREEN_WIDTH / 2 - 200, GameConfig.SCREEN_HEIGHT / 2 - 100)
        
        # ========== DRAW RETRY BUTTON ==========
        self.retry_button.draw(self.screen)
