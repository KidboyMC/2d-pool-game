import pygame
import pymunk
import math
from config import GameConfig
from physics_objects import Ball, Cushion
from ui_objects import Cue, PowerMeter, Pocket
from renderer import GameRenderer


class PoolGame:
    """
    KELAS UTAMA GAME - Mengorkestra seluruh game logic dan state.
    
    Tanggung jawab:
    - Manage game state (lives, game_running, taking_shot, dll)
    - Load dan setup game objects (balls, cushions, pockets)
    - Handle physics simulation
    - Check collision dan potted balls
    - Manage game flow (setup, update, render, input)
    - Reset game saat retry
    
    Pattern: Singleton-like (hanya ada satu instance saat game berjalan)
    """
    
    def __init__(self):
        """
        Inisialisasi game dan semua components.
        
        Proses:
        1. Setup pygame window dan caption
        2. Inisialisasi Pymunk physics space
        3. Inisialisasi game state variables
        4. Load assets (gambar)
        5. Setup game objects (balls, cushions, pockets)
        6. Inisialisasi UI components (cue, power meter, renderer)
        """
        # ========== SETUP PYGAME WINDOW ==========
        self.screen = pygame.display.set_mode(
            (GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT + GameConfig.BOTTOM_PANEL)
        )
        pygame.display.set_caption("Pool")
        
        # ========== PHYSICS SPACE ==========
        # Pymunk space untuk simulasi fisika (gravity, collision, dll)
        self.space = pymunk.Space()
        self.static_body = self.space.static_body  # Reference untuk static objects
        
        # ========== CLOCK ==========
        # Untuk kontrol FPS (frame rate)
        self.clock = pygame.time.Clock()
        
        # ========== GAME STATE ==========
        self.lives = GameConfig.INITIAL_LIVES  # Nyawa sisa (default 3)
        self.game_running = True               # Flag: game masih berjalan?
        self.taking_shot = True                # Flag: siap untuk shot berikutnya?
        self.cue_ball_potted = False           # Flag: bola putih masuk lubang?
        self.powering_up = False               # Flag: pemain sedang power up?
        self.run = True                        # Flag: main loop harus terus berjalan?
        
        # ========== POWER METER ==========
        # Untuk track kekuatan shot
        self.power_meter = PowerMeter(GameConfig.RED)
        
        # ========== LOAD ASSETS ==========
        # Load gambar meja, stick, dan bola
        self._load_assets()
        
        # ========== SETUP GAME OBJECTS ==========
        # Inisialisasi bola, dinding, dan lubang
        self._setup_balls()
        self._setup_cushions()
        self._setup_pockets()
        
        # ========== CUE (STICK) ==========
        # Stick untuk mengarahkan dan melempar bola
        self.cue = Cue(self.cue_image)
        
        # ========== RENDERER ==========
        # Untuk semua operasi rendering/drawing
        self.renderer = GameRenderer(
            self.screen,
            self.table_image,
            self.ball_images,
            {'normal': pygame.font.SysFont("Lato", 30),
             'large': pygame.font.SysFont("Lato", 60)}
        )
        
        # ========== TRACKING POTTED BALLS ==========
        # List untuk menyimpan gambar bola yang sudah potted
        self.potted_balls = []
        self.original_ball_images = self.ball_images.copy()
    
    def _load_assets(self):
        """
        Load semua asset gambar dari file.
        
        Asset yang di-load:
        1. table.png - Gambar meja pool
        2. cue.png - Gambar stick pool
        3. 16 ball images (pool_ball_outline_1.png sampai 16)
        
        Semua gambar di-scale (resize) agar sesuai dengan ukuran game.
        """
        # ========== LOAD TABLE IMAGE ==========
        self.table_image = pygame.image.load(GameConfig.TABLE_IMAGE).convert_alpha()
        # Scale ke ukuran screen
        self.table_image = pygame.transform.scale(
            self.table_image, (GameConfig.SCREEN_WIDTH, GameConfig.SCREEN_HEIGHT)
        )
        
        # ========== LOAD CUE IMAGE ==========
        self.cue_image = pygame.image.load(GameConfig.CUE_IMAGE).convert_alpha()
        # Scale cue menjadi 70% dari ukuran original
        self.cue_image = pygame.transform.scale(
            self.cue_image,
            (int(self.cue_image.get_width() * 0.7),
             int(self.cue_image.get_height() * 0.7))
        )
        
        # ========== LOAD BALL IMAGES ==========
        # Ada 16 bola pool (bola 1-15 + bola putih)
        self.ball_images = []
        for i in range(1, 17):
            # Load gambar bola dari file
            ball_image = pygame.image.load(
                GameConfig.BALL_IMAGE_PATH.format(i)
            ).convert_alpha()
            
            # Scale ke BALL_DIA (36 pixels)
            ball_image = pygame.transform.scale(ball_image, (GameConfig.BALL_DIA, GameConfig.BALL_DIA))
            
            # Tambah ke list
            self.ball_images.append(ball_image)
    
    def _setup_balls(self):
        """
        Inisialisasi semua bola di meja pool.
        
        Setup:
        1. 15 bola potted (bola 1-15) disusun dalam segitiga di bagian kiri
        2. 1 bola putih (cue ball) di bagian kanan
        
        Posisi awal bola berbentuk segitiga (standard pool break formation).
        """
        self.balls = []
        rows = 5  # Bola pertama punya 5 rows, kemudian berkurang
        
        # ========== SETUP BOLA POTTED (15 BOLA) ==========
        # Disusun dalam bentuk segitiga
        for col in range(5):
            for row in range(rows):
                # Hitung posisi bola
                # Kolom bergerak ke kanan, row bergerak ke bawah
                pos = (250 + (col * (GameConfig.BALL_DIA + 1)),
                       267 + (row * (GameConfig.BALL_DIA + 1)) + (col * GameConfig.BALL_DIA / 2))
                
                # Buat ball object
                new_ball = Ball(self.space, self.static_body, GameConfig.BALL_DIA / 2, pos)
                
                # Set gambar untuk bola ini
                new_ball.set_image(self.ball_images[len(self.balls)])
                
                # Tambah ke list
                self.balls.append(new_ball)
            
            # Kurangi rows untuk baris berikutnya (membuat segitiga)
            rows -= 1
        
        # ========== SETUP BOLA PUTIH (CUE BALL) ==========
        pos = (888, GameConfig.SCREEN_HEIGHT / 2)  # Posisi di tengah kanan
        cue_ball = Ball(self.space, self.static_body, GameConfig.BALL_DIA / 2, pos, is_cue=True)
        
        # Bola putih adalah gambar ke-16 (index 15)
        cue_ball.set_image(self.ball_images[-1])
        
        # Tambah ke list
        self.balls.append(cue_ball)
    
    def _setup_cushions(self):
        """
        Inisialisasi semua cushion (dinding elastis) di meja pool.
        
        Ada 6 cushion:
        - 2 di atas (kiri dan kanan dari pocket tengah atas)
        - 2 di bawah (kiri dan kanan dari pocket tengah bawah)
        - 2 di samping (kiri dan kanan)
        
        Cushion adalah polygon (bentuk dengan banyak sudut) untuk
        membuat pantul yang realistis.
        """
        self.cushions = []
        
        # Loop melalui setiap cushion configuration
        for cushion_dims in GameConfig.CUSHIONS:
            # Buat cushion object
            cushion = Cushion(self.space, self.static_body, cushion_dims)
            
            # Tambah ke list
            self.cushions.append(cushion)
    
    def _setup_pockets(self):
        """
        Inisialisasi semua pocket (lubang) di meja pool.
        
        Ada 6 pocket:
        - 4 di sudut (lebih besar)
        - 2 di tengah atas/bawah (lebih kecil)
        
        Pocket digunakan untuk mendeteksi apakah bola sudah masuk.
        """
        self.pockets = []
        
        # Loop melalui setiap pocket position
        for idx, pocket_pos in enumerate(GameConfig.POCKETS):
            # Ambil diameter pocket dari config (berbeda untuk sudut dan tengah)
            dia = GameConfig.POCKET_DIAS[idx]
            
            # Buat pocket object
            pocket = Pocket(pocket_pos, dia)
            
            # Tambah ke list
            self.pockets.append(pocket)
    
    def check_potted_balls(self):
        """
        Mengecek apakah ada bola yang masuk pocket.
        
        Proses:
        1. Loop melalui semua bola
        2. Loop melalui semua pocket
        3. Jika bola dalam pocket:
           - Jika bola putih (cue ball) -> kurangi lives, reset posisi
           - Jika bola lain -> hapus dari physics, hapus dari list, add ke potted_balls
        
        Note: Ball collision dengan pocket adalah geometric check saja,
        bukan physics collision.
        """
        for i, ball in enumerate(self.balls):
            for pocket in self.pockets:
                # Cek apakah bola masuk pocket
                if pocket.is_ball_in_pocket(ball.get_position()):
                    if ball.is_cue:  # Jika bola putih
                        # Kurangi lives
                        self.lives -= 1
                        
                        # Set flag cue ball potted
                        self.cue_ball_potted = True
                        
                        # Reset posisi bola putih ke luar screen
                        ball.reset_position((-100, -100))
                    else:  # Jika bola biasa
                        # Hapus dari physics space
                        self.space.remove(ball.body)
                        
                        # Hapus dari list balls
                        self.balls.remove(ball)
                        
                        # Add gambar bola ke potted_balls (untuk display di bottom panel)
                        self.potted_balls.append(self.ball_images[i])
                        
                        # Remove gambar bola dari ball_images (agar tidak digambar lagi)
                        self.ball_images.pop(i)
    
    def check_all_balls_stopped(self):
        """
        Mengecek apakah semua bola sudah berhenti bergerak.
        
        Ini penting untuk tahu kapan pemain siap melakukan shot berikutnya.
        Jika ada bola yang masih bergerak, pemain tidak bisa melakukan shot.
        
        Proses:
        1. Assume semua bola sudah berhenti (taking_shot = True)
        2. Loop melalui semua bola
        3. Jika ada bola yang bergerak (is_moving = True):
           - Set taking_shot = False
           - Break loop (tidak perlu cek bola lain)
        """
        self.taking_shot = True  # Default: siap untuk shot
        
        for ball in self.balls:
            if ball.is_moving():  # Jika ada bola yang bergerak
                self.taking_shot = False  # Tidak bisa melakukan shot
                break  # Tidak perlu cek bola lain
    
    def apply_shot(self, cue_angle):
        """
        Menerapkan impuls (gaya) ke bola putih sesuai dengan angle dan power.
        
        Proses:
        1. Ambil bola putih (balls[-1])
        2. Ambil kekuatan dari power meter
        3. Hitung x dan y components dari gaya
        4. Apply impulse ke bola menggunakan physics
        5. Reset power meter untuk shot berikutnya
        
        Args:
            cue_angle: float, sudut stick dalam derajat
        """
        cue_ball = self.balls[-1]  # Ambil bola putih
        force = self.power_meter.get_force()  # Ambil kekuatan
        
        # Hanya apply shot jika ada kekuatan
        if force > 0:
            # Hitung impulse components berdasarkan angle
            x_impulse = math.cos(math.radians(cue_angle))
            y_impulse = math.sin(math.radians(cue_angle))
            
            # Apply impulse dengan magnitude = force
            cue_ball.apply_impulse((force * -x_impulse, force * y_impulse))
        
        # Reset power meter untuk shot berikutnya
        self.power_meter.reset()
    
    def reset_game(self):
        """
        Reset game ke state awal untuk play lagi.
        
        Proses:
        1. Reset physics space (buat baru)
        2. Reset game state (lives, flags)
        3. Reload assets
        4. Setup game objects (balls, cushions, pockets)
        5. Reset tracking variables (potted_balls, dll)
        
        Ini dipanggil saat user click RETRY button.
        """
        # ========== RESET PHYSICS SPACE ==========
        self.space = pymunk.Space()
        self.static_body = self.space.static_body
        
        # ========== RESET GAME STATE ==========
        self.lives = GameConfig.INITIAL_LIVES
        self.game_running = True
        self.taking_shot = True
        self.cue_ball_potted = False
        self.powering_up = False
        
        # ========== RESET POWER METER ==========
        self.power_meter.reset()
        
        # ========== RELOAD ASSETS ==========
        self._load_assets()
        
        # ========== SETUP GAME OBJECTS ==========
        self._setup_balls()
        self._setup_cushions()
        self._setup_pockets()
        
        # ========== UPDATE RENDERER ==========
        self.renderer.ball_images = self.ball_images
        
        # ========== RESET TRACKING ==========
        self.potted_balls = []
        self.original_ball_images = self.ball_images.copy()
    
    def update(self):
        """
        Update game state setiap frame.
        
        Proses:
        1. Step physics simulation (Pymunk)
        2. Check potted balls
        3. Check apakah semua bola berhenti
        4. Update power meter
        """
        # Step physics simulation dengan delta time
        self.space.step(1 / GameConfig.FPS)
        
        # Check collision dengan pockets
        self.check_potted_balls()
        
        # Check apakah semua bola berhenti
        self.check_all_balls_stopped()
        
        # Update power meter (naik/turun jika powering up)
        self.power_meter.update(self.powering_up)
    
    def render(self):
        """
        Menggambar semua game elements ke screen.
        
        Proses:
        1. Fill background
        2. Draw table
        3. Draw balls
        4. Draw cue dan predictive line (jika taking shot)
        5. Draw power meter (jika powering up)
        6. Draw bottom panel (lives, potted balls)
        7. Draw game over/win screen (jika game ended)
        8. Update display
        """
        # Clear screen
        self.screen.fill(GameConfig.BG)
        
        # Draw table background
        self.renderer.draw_table()
        
        # Draw semua bola
        self.renderer.draw_balls(self.balls)
        
        # ========== DRAW CUE DAN PREDICTIVE LINE ==========
        if self.taking_shot and self.game_running:
            # Reset cue ball jika potted
            if self.cue_ball_potted:
                self.balls[-1].reset_position((888, GameConfig.SCREEN_HEIGHT / 2))
                self.cue_ball_potted = False
            
            # Ambil mouse position dan cue ball position
            mouse_pos = pygame.mouse.get_pos()
            cue_ball_pos = self.balls[-1].get_position()
            
            # Hitung sudut stick (direction dari bola ke mouse)
            x_dist = cue_ball_pos[0] - mouse_pos[0]
            y_dist = -(cue_ball_pos[1] - mouse_pos[1])
            cue_angle = math.degrees(math.atan2(y_dist, x_dist))
            
            # Draw predictive line
            self.renderer.draw_predictive_line(self.balls[-1], cue_angle)
            
            # Update dan draw cue
            cue_offset = self.power_meter.get_force() / 200
            self.cue.update(cue_angle, cue_offset)
            self.cue.draw(self.screen, cue_ball_pos)
        
        # ========== DRAW POWER METER ==========
        if self.powering_up and self.game_running:
            self.power_meter.draw(self.screen, self.balls[-1].get_position())
        
        # ========== DRAW BOTTOM PANEL ==========
        self.renderer.draw_bottom_panel(self.lives, self.potted_balls)
        
        # ========== DRAW GAME OVER/WIN SCREEN ==========
        if self.lives <= 0:  # Game over (no lives left)
            self.powering_up = False
            self.renderer.draw_game_over()
            self.game_running = False
        elif len(self.balls) == 1:  # Win (hanya bola putih yang tersisa)
            self.powering_up = False
            self.renderer.draw_win()
            self.game_running = False
        
        # Update display
        pygame.display.update()
    
    def handle_input(self):
        """
        Handle semua input events (mouse, keyboard, quit).
        
        Proses:
        1. Ambil mouse position dan button state
        2. Update retry button (jika game over)
        3. Loop melalui semua events:
           - Jika game berjalan: handle shot input
           - Jika game over: handle retry button click
           - Jika QUIT: return False
        
        Returns:
            bool: True jika game harus lanjut, False jika quit
        """
        cue_angle = 0
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        # ========== UPDATE RETRY BUTTON ==========
        if not self.game_running:
            # Update button state hanya jika game over
            self.renderer.retry_button.update(mouse_pos, mouse_pressed)
        
        # ========== PROCESS EVENTS ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # Signal untuk quit
            
            # ========== GAME OVER STATE ==========
            if not self.game_running:
                # Saat game over, hanya handle retry button
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.renderer.retry_button.is_clicked(mouse_pos):
                        self.reset_game()  # Restart game
            
            # ========== GAME RUNNING STATE ==========
            else:
                # Handle shot input
                if event.type == pygame.MOUSEBUTTONDOWN and self.taking_shot:
                    # Pemain mulai power up
                    self.powering_up = True
                
                elif event.type == pygame.MOUSEBUTTONUP and self.taking_shot:
                    # Pemain release mouse -> apply shot
                    if self.powering_up:
                        mouse_pos = pygame.mouse.get_pos()
                        cue_ball_pos = self.balls[-1].get_position()
                        
                        # Hitung angle
                        x_dist = cue_ball_pos[0] - mouse_pos[0]
                        y_dist = -(cue_ball_pos[1] - mouse_pos[1])
                        cue_angle = math.degrees(math.atan2(y_dist, x_dist))
                        
                        # Apply shot
                        self.apply_shot(cue_angle)
                    
                    # Stop power up
                    self.powering_up = False
        
        return True  # Game masih berjalan
    
    def run_game(self):
        """
        Main game loop - loop utama yang berjalan sampai game quit.
        
        Setiap iteration:
        1. Tick clock (kontrol FPS)
        2. Handle input
        3. Update game state
        4. Render game
        5. Repeat sampai self.run = False
        
        Loop berakhir ketika:
        - User close window
        - User press Ctrl+C atau quit event diterima
        """
        while self.run:
            # Tick clock dengan FPS limit
            self.clock.tick(GameConfig.FPS)
            
            # Handle input (return False jika quit)
            self.run = self.handle_input()
            
            # Update game state
            self.update()
            
            # Render game
            self.render()
        
        # Game selesai, quit pygame
        pygame.quit()
