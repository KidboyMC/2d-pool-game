import pygame
import pymunk
import math
from config import GameConfig
from physics.physics_objects import Ball, Cushion, COLLISION_TYPE_BALL, COLLISION_TYPE_CUSHION
from ui.ui_objects import Cue, PowerMeter, Pocket
from ui.renderer import GameRenderer


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
        self.current_player = 1                # 1 untuk Player 1, 2 untuk Player 2
        self.player_1_target = None            # Akan berisi 'Solid' atau 'Stripe' nanti
        self.player_2_target = None
        self.foul_committed = False
        self.game_running = True               # Flag: game masih berjalan?
        self.taking_shot = True                # Flag: siap untuk shot berikutnya?
        self.cue_ball_potted = False           # Flag: bola putih masuk lubang?
        self.powering_up = False               # Flag: pemain sedang power up?
        self.run = True                        # Flag: main loop harus terus berjalan?
        self.ball_potted_this_turn = False     # Flag: bola masuk pada giliran ini
        self.winner = None                     # Akan berisi 1 atau 2 jika game selesai
        self.ball_in_hand = False
        self.in_main_menu = True

        # ========== POWER METER ==========
        # Untuk track kekuatan shot
        self.power_meter = PowerMeter(GameConfig.RED)
        
        # ========== LOAD ASSETS ==========
        self._load_assets()

        # ========== SETUP GAME OBJECTS ==========
        # Inisialisasi bola, dinding, dan lubang
        self._setup_balls()
        self._setup_cushions()
        self._setup_pockets()
        
        # ========== COLLISION HANDLER (SOUND EFFECT) ==========
        # Daftarkan handler agar suara tabrakan otomatis terpicu oleh pymunk
        self._setup_collision_handlers()
        
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

        # ========== LOAD AUDIO ==========
        pygame.mixer.init()
        
        # Gunakan Try-Except agar game tidak crash jika file audio belum ada
        try:
            self.hit_sfx = pygame.mixer.Sound(GameConfig.HIT_SOUND)
            self.pocket_sfx = pygame.mixer.Sound(GameConfig.POCKET_SOUND)
            
        except AttributeError:
            print("Warning: Path audio (HIT_SOUND / POCKET_SOUND) belum ditulis di config.py!")
            self._create_dummy_sounds()
        except FileNotFoundError:
            print("Warning: File audio tidak ditemukan di folder assets! Game berjalan tanpa suara.")
            self._create_dummy_sounds()
        except Exception as e:
            print(f"Warning: Audio error -> {e}. Game berjalan tanpa suara.")
            self._create_dummy_sounds()
        
        pygame.mixer.music.load("assets/audio/lofi_bgm.mp3")
        pygame.mixer.music.play(-1)

    def _create_dummy_sounds(self):
        """Membuat fungsi .play() palsu agar game tidak crash saat audio dipanggil"""
        class DummySound:
            def play(self): 
                pass
        
        self.hit_sfx = DummySound()
        self.pocket_sfx = DummySound()
    
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
                current_ball_number = len(self.balls) + 1
                new_ball = Ball(self.space, self.static_body, GameConfig.BALL_DIA / 2, pos, is_cue=False, number=current_ball_number)
                
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

    def _setup_collision_handlers(self):
        """
        Mendaftarkan collision handler pymunk untuk memutar sound effect
        secara otomatis saat terjadi tabrakan, bukan dicek manual tiap frame.
        
        Ada 2 jenis tabrakan yang dideteksi:
        1. Bola vs Bola (ball-to-ball)      -> suara click bola lebih nyaring
        2. Bola vs Cushion (ball-to-rail)   -> suara pantulan dinding lebih pelan
        
        Volume suara disesuaikan dengan kekuatan tabrakan (impulse),
        supaya tabrakan pelan tidak terdengar sekeras tabrakan break/keras.
        
        Catatan kompatibilitas:
        Pymunk >= 7.0 menghapus Space.add_collision_handler() dan menggantinya
        dengan Space.on_collision(collision_type_a, collision_type_b, post_solve=...).
        Callback signature pada kedua versi sama: func(arbiter, space, data).
        Method ini mendukung KEDUANYA agar game tetap berjalan baik di pymunk
        versi lama maupun baru.
        """
        if hasattr(self.space, "on_collision"):
            # ========== PYMUNK >= 7.0 ==========
            self.space.on_collision(
                COLLISION_TYPE_BALL, COLLISION_TYPE_BALL,
                post_solve=self._on_ball_ball_collision
            )
        else:
            # ========== PYMUNK < 7.0 (API lama) ==========
            # Hanya mendaftarkan handler ball-to-ball.
            ball_handler = self.space.add_collision_handler(
                COLLISION_TYPE_BALL, COLLISION_TYPE_BALL
            )
            ball_handler.post_solve = self._on_ball_ball_collision

    def _impulse_to_volume(self, arbiter, min_impulse=200, max_impulse=4000):
        """
        Mengubah kekuatan tabrakan (impulse) menjadi nilai volume (0.0 - 1.0).
        
        Tabrakan lemah -> volume kecil (atau diabaikan jika di bawah ambang batas)
        Tabrakan kuat  -> volume mendekati maksimal
        
        Args:
            arbiter: pymunk Arbiter object, berisi info tabrakan
            min_impulse: ambang batas minimal agar suara mulai terdengar
            max_impulse: titik impulse yang dianggap volume penuh (1.0)
        
        Returns:
            float: volume 0.0 - 1.0, atau None jika tabrakan terlalu lemah (diabaikan)
        """
        impulse = arbiter.total_impulse.length
        
        if impulse < min_impulse:
            return None  # Terlalu lemah, jangan mainkan suara (hindari noise berisik)
        
        # Normalisasi ke rentang 0.0 - 1.0
        volume = min((impulse - min_impulse) / (max_impulse - min_impulse), 1.0)
        
        # Volume minimal 0.2 agar tetap terdengar meski tabrakan ringan
        return max(volume, 0.2)

    def _on_ball_ball_collision(self, arbiter, space, data):
        """
        Dipanggil otomatis oleh pymunk setiap kali dua bola bertabrakan.
        Memutar suara hit dengan volume proporsional terhadap kekuatan tabrakan.
        """
        volume = self._impulse_to_volume(arbiter)
        if volume is not None:
            self.hit_sfx.set_volume(volume)
            self.hit_sfx.play()
    
    def check_potted_balls(self):
        balls_to_remove = []
        eight_ball_potted = False  # FLAG BARU: Catat dulu, jangan langsung dieksekusi

        for ball in self.balls:
            if ball in balls_to_remove: continue
            
            for pocket in self.pockets:
                if pocket.is_ball_in_pocket(ball.get_position()):
                    if ball.is_cue:
                        if self.ball_in_hand:
                            continue 
                        self.foul_committed = True
                        self.cue_ball_potted = True
                        ball.reset_position((-100, -100))
                        self.pocket_sfx.play()  # Bola putih masuk lubang -> mainkan suara
                    elif ball.number == 8:
                        eight_ball_potted = True  # Aktifkan flag bola 8
                        balls_to_remove.append(ball)
                        self.pocket_sfx.play()  # Bola 8 masuk lubang -> mainkan suara
                    else:
                        self.process_target_ball(ball)
                        balls_to_remove.append(ball)
                        self.pocket_sfx.play()  # Bola target masuk lubang -> mainkan suara
                        
        # Eksekusi penghapusan bola
        for ball in balls_to_remove:
            if ball in self.balls:
                self.balls.remove(ball)
                try:
                    self.space.remove(ball.body, ball.shape, ball.pivot)
                except (ValueError, KeyError) as e:
                    print(f"Warning Pymunk Removal: {e}") 
                if ball.image:
                    self.potted_balls.append(ball.image)
                    
        # Evaluasi menang/kalah di akhir, SETELAH status foul bola putih dipastikan
        if eight_ball_potted:
            self.check_win_condition()
    
    def process_target_ball(self, ball):
        """Menentukan target (Solid/Stripe) dan mengecek apakah bola sah"""
        if ball.is_cue: 
            return
        
        ball_type = 'Solid' if ball.number <= 7 else 'Stripe'
        
        # Jika belum ada target, tentukan target berdasarkan bola pertama yang masuk
        if self.player_1_target is None:
            if self.current_player == 1:
                self.player_1_target = ball_type
                self.player_2_target = 'Stripe' if ball_type == 'Solid' else 'Solid'
            else:
                self.player_2_target = ball_type
                self.player_1_target = 'Stripe' if ball_type == 'Solid' else 'Solid'
                
        # Cek apakah bola yang masuk sesuai dengan target pemain saat ini
        current_target = self.player_1_target if self.current_player == 1 else self.player_2_target
        if current_target == ball_type:
            self.ball_potted_this_turn = True
        else:
            self.foul_committed = True  # Memasukkan bola lawan dianggap Foul

    def check_win_condition(self):
        """Mengecek kondisi saat bola 8 masuk (Menang atau Kalah)"""
        current_target = self.player_1_target if self.current_player == 1 else self.player_2_target
                      
        self.game_running = False

        if current_target is None:
            self.winner = 2 if self.current_player == 1 else 1 # Lawan otomatis menang
            return
        
        # Hitung sisa bola target milik pemain saat ini
        remaining_balls = 0
        for b in self.balls:
            if not b.is_cue and b.number != 8:
                b_type = 'Solid' if b.number <= 7 else 'Stripe'
                if b_type == current_target:
                    remaining_balls += 1
        
        # MENANG: Jika bolanya sudah habis DAN tidak melakukan foul (bola putih tidak ikut masuk)
        if remaining_balls == 0 and not self.foul_committed and not self.cue_ball_potted:
            self.winner = self.current_player
        else:
            # KALAH: Bola 8 masuk tapi bola targetnya masih ada, ATAU foul bersamaan dengan bola 8
            self.winner = 2 if self.current_player == 1 else 1

    def end_turn(self):
        """Mengeksekusi perpindahan giliran"""
        # Pindah ke pemain lawan jika terjadi Foul ATAU tidak ada bola miliknya yang masuk
        if self.foul_committed:
            self.ball_in_hand = True
            self.balls[-1].shape.sensor = True
        
        if self.foul_committed or not self.ball_potted_this_turn:
            self.current_player = 2 if self.current_player == 1 else 1
            
        # Reset flag turn untuk giliran selanjutnya
        self.foul_committed = False
        self.ball_potted_this_turn = False

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
        all_stopped = True
        for ball in self.balls:
            if ball.is_moving():
                all_stopped = False
                break
                
        # Jika sebelumnya bola bergerak, dan SEKARANG semua berhenti
        if all_stopped and not self.taking_shot:
            self.taking_shot = True
            self.end_turn()  # Panggil eksekusi evaluasi giliran
            
        elif not all_stopped:
            self.taking_shot = False
    
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
            self.hit_sfx.play()
            self.taking_shot = False 
            self.ball_potted_this_turn = False
        
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
        self.game_running = True
        self.taking_shot = True
        self.cue_ball_potted = False
        self.powering_up = False
        self.current_player = 1
        self.player_1_target = None
        self.player_2_target = None
        self.winner = None
        self.foul_committed = False
        self.ball_potted_this_turn = False
        self.ball_in_hand = False
        
        # ========== RESET POWER METER ==========
        self.power_meter.reset()
        
        # ========== SETUP GAME OBJECTS ==========
        self._setup_balls()
        self._setup_cushions()
        self._setup_pockets()
        
        # ========== COLLISION HANDLER (SOUND EFFECT) ==========
        # Wajib didaftarkan ulang karena self.space adalah instance baru
        self._setup_collision_handlers()
        
        # ========== UPDATE RENDERER ==========
        self.renderer.ball_images = self.ball_images
        
        # ========== RESET TRACKING ==========
        self.potted_balls = []
    
    def update(self, dt=1/120.0):
        """
        Update game state setiap frame.
        
        Proses:
        1. Step physics simulation (Pymunk)
        2. Check potted balls
        3. Check apakah semua bola berhenti
        4. Update power meter
        """
        if self.in_main_menu:
            return
        
        # Step physics simulation dengan delta time
        self.space.step(dt)
        
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
        if self.in_main_menu:
            self.renderer.draw_main_menu()
            pygame.display.update()
            return
        
        # Clear screen
        self.screen.fill(GameConfig.BG)
        
        # Draw table background
        self.renderer.draw_table()
        
        # Draw semua bola
        self.renderer.draw_balls(self.balls)
        
        # ========== BALL IN HAND LOGIC ==========
        # Jika status ball in hand aktif, bola putih menempel di mouse
        if self.ball_in_hand and self.game_running:
            mouse_pos = pygame.mouse.get_pos()
            self.balls[-1].reset_position(mouse_pos)
            # Catatan: Kita tidak menggambar stick saat sedang menaruh bola

        # ========== DRAW CUE DAN PREDICTIVE LINE ==========
        # Jika TIDAK SEDANG ball in hand, gambar stik biliar seperti biasa
        elif self.taking_shot and self.game_running:
            
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
        
        # ========== DRAW FOUL ALERT ==========
        if (self.foul_committed or self.ball_in_hand) and self.game_running:
            self.renderer.draw_foul_alert()

        # ========== DRAW BOTTOM PANEL ==========
        self.renderer.draw_bottom_panel(self.current_player, self.potted_balls, self.player_1_target, self.player_2_target)
        
        # ========== DRAW GAME OVER/WIN SCREEN ==========
        if not self.game_running:
            self.powering_up = False
            if self.winner:
                self.renderer.draw_win(self.winner) # Tampilkan siapa yang menang
            else:
                self.renderer.draw_game_over()      # Jaga-jaga jika drow/error
        
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
        
        # ========== MAIN MENU STATE ==========
        if self.in_main_menu:
            self.renderer.start_button.update(mouse_pos, mouse_pressed)
            self.renderer.quit_button.update(mouse_pos, mouse_pressed)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.renderer.start_button.is_clicked(mouse_pos):
                        self.in_main_menu = False
                        self.reset_game()  # Pastikan meja di-reset rapi sebelum mulai
                    elif self.renderer.quit_button.is_clicked(mouse_pos):
                        return False  # Keluar dari game
            return True
            
        # ========== UPDATE RETRY & MENU BUTTONS ==========
        if not self.game_running:
            self.renderer.retry_button.update(mouse_pos, mouse_pressed)
            self.renderer.menu_button.update(mouse_pos, mouse_pressed) # Update tombol menu
        
        # ========== PROCESS EVENTS (GAMEPLAY) ==========
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False  # Signal untuk quit
            
            # ========== GAME OVER STATE ==========
            if not self.game_running:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Jika klik RETRY -> Langsung in-game reset (Mulai ulang instant)
                    if self.renderer.retry_button.is_clicked(mouse_pos):
                        self.reset_game()
                    
                    # Jika klik MAIN MENU -> Kembalikan ke halaman depan menu utama
                    elif self.renderer.menu_button.is_clicked(mouse_pos):
                        self.in_main_menu = True
            
            # ========== GAME RUNNING STATE ==========
            else:
                # 1. MOUSE BUTTON DOWN: Mulai isi kekuatan ATAU letakkan bola putih
                if event.type == pygame.MOUSEBUTTONDOWN and self.taking_shot:
                    if self.ball_in_hand:
                        radius = GameConfig.BALL_DIA / 2
                        play_area = GameConfig.TABLE_PLAY_AREA
                        
                        # Validasi Batas Meja (Cushions)
                        valid_x = play_area[0] + radius <= mouse_pos[0] <= play_area[2] - radius
                        valid_y = play_area[1] + radius <= mouse_pos[1] <= play_area[3] - radius
                        
                        if not (valid_x and valid_y):
                            continue  # Abaikan klik jika di luar area meja
                            
                        # Validasi Tumpukan Bola (Overlap)
                        is_overlapping = False
                        for b in self.balls:
                            if not b.is_cue:
                                b_pos = b.get_position()
                                dist = math.sqrt((mouse_pos[0]-b_pos[0])**2 + (mouse_pos[1]-b_pos[1])**2)
                                if dist <= GameConfig.BALL_DIA:
                                    is_overlapping = True
                                    break
                                    
                        if is_overlapping:
                            continue  # Abaikan klik jika menabrak bola lain
                            
                        # Jika posisi valid, letakkan bola putih
                        self.ball_in_hand = False
                        self.cue_ball_potted = False
                        self.balls[-1].shape.sensor = False
                        self.balls[-1].body.velocity = (0, 0)
                    else:
                        self.powering_up = True
                
                # 2. MOUSE BUTTON UP: Lepaskan tembakan (Shoot!)
                elif event.type == pygame.MOUSEBUTTONUP and self.taking_shot:
                    if self.powering_up:
                        mouse_pos = pygame.mouse.get_pos()
                        cue_ball_pos = self.balls[-1].get_position()
                        
                        # Hitung arah tembakan
                        x_dist = cue_ball_pos[0] - mouse_pos[0]
                        y_dist = -(cue_ball_pos[1] - mouse_pos[1])
                        cue_angle = math.degrees(math.atan2(y_dist, x_dist))
                        
                        # Tembak bola!
                        self.apply_shot(cue_angle)
                    
                    self.powering_up = False
        
        return True
    
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
            dt = self.clock.tick(GameConfig.FPS) / 1000.0
            
            # Handle input (return False jika quit)
            self.run = self.handle_input()
            
            # Update game state
            self.update(dt)
            
            # Render game
            self.render()
        
        # Game selesai, quit pygame
        pygame.quit()