import pygame
import math
from config import GameConfig


class Button:
    """
    Kelas untuk membuat tombol yang dapat diklik.
    Menangani rendering, deteksi hover, dan deteksi klik pada tombol.
    
    Features:
    - Berubah warna saat di-hover (cursor di atas tombol)
    - Berubah warna saat ditekan
    - Render text di tengah tombol
    - Deteksi klik mouse
    """
    
    def __init__(self, x, y, width, height, text, font, 
                 normal_color, hover_color, active_color):
        """
        Inisialisasi tombol.
        
        Args:
            x, y: Posisi sudut kiri atas tombol (pixel)
            width, height: Lebar dan tinggi tombol (pixel)
            text: Teks yang ditampilkan pada tombol
            font: Font pygame untuk rendering text
            normal_color: Warna RGB saat tombol normal (tidak di-hover)
            hover_color: Warna RGB saat cursor di atas tombol
            active_color: Warna RGB saat tombol ditekan
        """
        self.rect = pygame.Rect(x, y, width, height)  # Bounding box tombol
        self.text = text                               # Teks tombol
        self.font = font                               # Font untuk text
        self.normal_color = normal_color               # Warna normal
        self.hover_color = hover_color                 # Warna hover
        self.active_color = active_color               # Warna saat ditekan
        self.current_color = normal_color              # Warna saat ini (default normal)
        self.is_hovered = False                        # Flag: cursor di atas tombol?
        self.is_pressed = False                        # Flag: tombol sedang ditekan?
    
    def update(self, mouse_pos, is_mouse_pressed):
        """
        Update state tombol berdasarkan posisi mouse dan button status.
        Method ini harus dipanggil setiap frame untuk update warna tombol.
        
        Args:
            mouse_pos: tuple (x, y) posisi cursor mouse saat ini
            is_mouse_pressed: bool, True jika mouse button sedang ditekan
        """
        # Check apakah cursor berada di dalam area tombol
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Set warna berdasarkan state
        if self.is_hovered:
            # Jika cursor di atas tombol
            if is_mouse_pressed:
                self.current_color = self.active_color  # Tombol ditekan -> warna active
            else:
                self.current_color = self.hover_color   # Cursor hover -> warna hover
        else:
            # Cursor tidak di atas tombol
            self.current_color = self.normal_color      # Warna normal
        
        # Set flag is_pressed (tombol diklik)
        self.is_pressed = is_mouse_pressed and self.is_hovered
    
    def is_clicked(self, mouse_pos):
        """
        Cek apakah tombol diklik pada posisi mouse tertentu.
        Biasanya dipanggil saat pygame.MOUSEBUTTONDOWN event terjadi.
        
        Args:
            mouse_pos: tuple (x, y) posisi mouse
            
        Returns:
            bool: True jika mouse_pos berada di dalam area tombol
        """
        return self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface):
        """
        Menggambar tombol ke surface pygame.
        
        Proses:
        1. Draw background rectangle dengan current_color
        2. Draw border (outline) putih
        3. Render text di tengah tombol
        
        Args:
            surface: pygame Surface untuk menggambar
        """
        # Draw background rectangle (isi tombol)
        pygame.draw.rect(surface, self.current_color, self.rect)
        
        # Draw border/outline putih dengan ketebalan 3 pixel
        pygame.draw.rect(surface, GameConfig.WHITE, self.rect, 3)
        
        # Render text
        text_surface = self.font.render(self.text, True, GameConfig.WHITE)
        
        # Posisi text di tengah tombol
        text_rect = text_surface.get_rect(center=self.rect.center)
        
        # Gambar text ke surface
        surface.blit(text_surface, text_rect)


class Cue:
    """
    Kelas untuk merepresentasikan stick pool (cue).
    Stick bergerak mengikuti mouse dan merotasi untuk menunjukkan arah shot.
    
    Features:
    - Rotasi mengikuti sudut antara mouse dan bola
    - Offset (jarak) mengikuti power meter (semakin kuat, semakin jauh stick mundur)
    - Render stick dengan rotasi yang tepat
    """
    
    def __init__(self, image):
        """
        Inisialisasi stick pool.
        
        Args:
            image: pygame Surface berisi gambar stick
        """
        self.original_image = image           # Gambar original stick (tidak di-rotate)
        self.angle = 0                        # Sudut rotasi stick (dalam derajat)
        self.offset = 0                       # Jarak mundur stick (berdasarkan power)
        self.image = self.original_image      # Gambar current (akan di-rotate)
        self.rect = self.image.get_rect()     # Bounding box
    
    def update(self, angle, offset):
        """
        Update sudut dan offset stick.
        Method ini dipanggil setiap frame untuk update posisi stick.
        
        Args:
            angle: Sudut stick dalam derajat (relative ke mouse position)
            offset: Jarak mundur stick (dari power meter)
        """
        self.angle = angle      # Update sudut
        self.offset = offset    # Update offset (seberapa jauh stick mundur)
    
    def draw(self, surface, cue_ball_pos):
        """
        Menggambar stick ke screen.
        
        Proses:
        1. Hitung offset position (berapa pixel stick mundur dari bola)
        2. Tentukan posisi center stick
        3. Rotate gambar stick sesuai angle
        4. Gambar stick ke surface
        
        Args:
            surface: pygame Surface untuk menggambar
            cue_ball_pos: tuple (x, y) posisi bola putih
        """
        # Hitung offset dalam pixel berdasarkan angle dan offset value
        x_offset = math.cos(math.radians(self.angle)) * self.offset
        y_offset = math.sin(math.radians(self.angle)) * self.offset
        
        # Set center position stick (relative ke bola + offset)
        self.rect.center = (cue_ball_pos[0] + x_offset, cue_ball_pos[1] - y_offset)
        
        # Rotate gambar stick sesuai dengan angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        
        # Gambar stick ke surface dengan center di rect.center
        surface.blit(self.image,
            (self.rect.centerx - self.image.get_width() / 2,
             self.rect.centery - self.image.get_height() / 2)
        )


class PowerMeter:
    """
    Kelas untuk menampilkan dan mengelola power meter (power bar).
    Power meter menunjukkan kekuatan yang akan diberikan ke bola saat shot.
    
    Features:
    - Kekuatan naik-turun otomatis (animation)
    - Render bar-bar untuk visualisasi power
    - Max force dibatasi dengan MAX_FORCE
    """
    
    def __init__(self, bar_color):
        """
        Inisialisasi power meter.
        
        Args:
            bar_color: tuple RGB untuk warna bar pada power meter
        """
        # Buat surface kecil untuk satu bar power
        self.bar_surface = pygame.Surface((10, 20))
        self.bar_surface.fill(bar_color)          # Isi dengan warna
        
        self.force = 0                            # Kekuatan saat ini (0 - MAX_FORCE)
        self.max_force = GameConfig.MAX_FORCE     # Kekuatan maksimal (10000)
        self.force_direction = 1                  # 1 untuk naik, -1 untuk turun
    
    def update(self, is_powering_up):
        """
        Update nilai force setiap frame.
        Jika is_powering_up=True, force akan terus bertambah/berkurang (animation).
        
        Args:
            is_powering_up: bool, True jika pemain sedang menekan mouse untuk power up
        """
        if is_powering_up:
            # Tambah force sebesar 100 setiap frame (dikalikan direction)
            self.force += 100 * self.force_direction
            
            # Jika force mencapai min/max, balik arah
            if self.force >= self.max_force or self.force <= 0:
                self.force_direction *= -1  # Ubah arah (-1 menjadi 1 atau sebaliknya)
    
    def get_force(self):
        """
        Mendapatkan nilai force saat ini secara aman.
        Encapsulation: method ini mengabstraksi akses langsung ke self.force
        
        Returns:
            int: Nilai force (0 - MAX_FORCE)
        """
        return self.force
    
    def reset(self):
        """
        Reset power meter ke nilai awal.
        Dipanggil setelah shot dilakukan untuk reset untuk shot berikutnya.
        """
        self.force = 0                # Reset force ke 0
        self.force_direction = 1      # Reset direction ke naik
    
    def draw(self, surface, pos):
        """
        Menggambar power meter bars ke screen.
        Setiap 2000 force = 1 bar (contoh: force 8000 = 4 bars)
        
        Args:
            surface: pygame Surface untuk menggambar
            pos: tuple (x, y) posisi untuk menggambar power meter
        """
        # Hitung jumlah bar yang harus digambar
        num_bars = math.ceil(self.force / 2000)
        
        # Gambar setiap bar
        for b in range(num_bars):
            surface.blit(self.bar_surface,
                (pos[0] - 30 + (b * 15), pos[1] + 30))  # Offset horizontal untuk setiap bar


class Pocket:
    """
    Kelas untuk merepresentasikan lubang (pocket) di meja pool.
    Digunakan untuk mendeteksi apakah bola telah masuk lubang.
    
    Pocket adalah lingkaran, jadi deteksi menggunakan distance antara
    pusat bola dan pusat pocket.
    """
    
    def __init__(self, pos, diameter):
        """
        Inisialisasi pocket.
        
        Args:
            pos: tuple (x, y) posisi pusat pocket
            diameter: diameter pocket dalam pixel
        """
        self.pos = pos              # Posisi pusat pocket
        self.diameter = diameter    # Diameter (untuk berbagai ukuran pocket)
        self.radius = diameter / 2  # Jari-jari (untuk collision detection)
    
    def is_ball_in_pocket(self, ball_pos):
        """
        Mengecek apakah bola berada di dalam pocket.
        Menggunakan distance formula: sqrt((x2-x1)^2 + (y2-y1)^2)
        
        Jika jarak antara pusat bola dan pusat pocket <= radius pocket,
        maka bola dianggap masuk pocket.
        
        Args:
            ball_pos: tuple (x, y) posisi pusat bola
            
        Returns:
            bool: True jika bola dalam pocket, False sebaliknya
        """
        # Hitung jarak horizontal antara bola dan pocket
        ball_x_dist = abs(ball_pos[0] - self.pos[0])
        
        # Hitung jarak vertikal antara bola dan pocket
        ball_y_dist = abs(ball_pos[1] - self.pos[1])
        
        # Hitung total distance menggunakan Pythagoras
        ball_dist = math.sqrt(ball_x_dist**2 + ball_y_dist**2)
        
        # Cek apakah distance <= radius pocket
        return ball_dist <= self.radius
