import pygame


class GameConfig:
    """
    Kelas untuk menyimpan semua konstanta dan konfigurasi game.
    Menggunakan prinsip encapsulation untuk mengelola nilai-nilai yang digunakan
    di seluruh aplikasi.
    """
    
    # ========== KONFIGURASI LAYAR ==========
    SCREEN_WIDTH = 1200        # Lebar layar game (pixel)
    SCREEN_HEIGHT = 678        # Tinggi layar game (pixel)
    BOTTOM_PANEL = 50          # Tinggi panel bawah untuk info lives dan bola potted
    FPS = 120                  # Frame per second untuk smooth gameplay
    
    # ========== KONFIGURASI PHYSICS ==========
    BALL_DIA = 36              # Diameter bola dalam pixel
    MAX_FORCE = 10000          # Kekuatan maksimal yang bisa diberikan ke bola
    
    # ========== WARNA ==========
    BG = (50, 50, 50)          # Warna background (RGB)
    RED = (255, 0, 0)          # Warna merah untuk teks game over/win
    WHITE = (255, 255, 255)    # Warna putih untuk teks normal
    BUTTON_COLOR = (70, 150, 200)          # Warna tombol normal (biru muda)
    BUTTON_HOVER_COLOR = (90, 170, 220)    # Warna tombol saat cursor di atas
    BUTTON_ACTIVE_COLOR = (50, 130, 180)   # Warna tombol saat ditekan
    
    # ========== ASSETS (FILE GAMBAR) ==========
    TABLE_IMAGE = "assets/table.png"              # Gambar meja pool
    CUE_IMAGE = "assets/cue.png"                  # Gambar stick pool
    BALL_IMAGE_PATH = "assets/balls/pool_ball_outline_{}.png"  # Path template untuk gambar bola
    
    # ========== KONFIGURASI LUBANG (POCKET) ==========
    POCKET_DIA = 66  # Diameter default lubang samping
    POCKET_DIAS = [80, 66, 80, 80, 66, 80]  # [TL, TM, TR, BL, BM, BR]
    # TL=Top Left (sudut atas kiri), TM=Top Middle (tengah atas), dst

    # ========== POSISI LUBANG ==========
    # Enam lubang di meja pool: 2 di tengah (atas/bawah), 4 di sudut
    POCKETS = [
        (55, 63),      # Top Left (sudut atas kiri)
        (592, 48),     # Top Middle (tengah atas)
        (1134, 64),    # Top Right (sudut atas kanan)
        (55, 616),     # Bottom Left (sudut bawah kiri)
        (592, 629),    # Bottom Middle (tengah bawah)
        (1134, 616)    # Bottom Right (sudut bawah kanan)
    ]
    
    # ========== POSISI BANTALAN (CUSHION) ==========
    # Bantalan adalah dinding elastis yang memantulkan bola
    CUSHIONS = [
        # Rail atas (pembatas atas)
        [(100, 56), (130, 77), (560, 77), (570, 56)],
        [(630, 56), (640, 77), (1070, 77), (1100, 56)],

        # Rail bawah (pembatas bawah)
        [(100, 622), (130, 600), (560, 600), (570, 622)],
        [(630, 622), (640, 600), (1070, 600), (1100, 622)],

        # Rail kiri (pembatas kiri)
        [(56, 100), (77, 130), (77, 548), (56, 578)],
        
        # Rail kanan (pembatas kanan)
        [(1143, 100), (1122, 130), (1122, 548), (1143, 578)],
    ]

    # ========== AREA BERMAIN (PLAY AREA) ==========
    # Batas aman untuk meletakkan bola (x_min, y_min, x_max, y_max)
    TABLE_PLAY_AREA = (100, 56, 1100, 622)

    # ========== ASSETS (FILE AUDIO) ==========
    HIT_SOUND = "assets/audio/hit.wav"          # Suara stik memukul bola
    POCKET_SOUND = "assets/audio/pocket.wav"    # Suara bola masuk lubang