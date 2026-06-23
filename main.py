import pygame
import pymunk
from game.game import PoolGame

# ============================================================================
# INISIALISASI PYGAME
# ============================================================================
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
# Initialize pygame library sebelum menggunakan fitur pygame apapun
pygame.init()


# ============================================================================
# MAIN ENTRY POINT - Titik masuk utama program
# ============================================================================
"""
Script ini adalah entry point (pintu masuk) untuk menjalankan game pool.

Alur eksekusi:
1. Python menjalankan script ini (main.py)
2. pygame.init() dipanggil untuk inisialisasi pygame
3. Buat instance PoolGame
4. Panggil game.run_game() untuk start main loop
5. Game berjalan sampai pemain quit/close window

Struktur file project:
- main.py          (file ini) - Entry point
- config.py        - GameConfig class (konstanta dan konfigurasi)
- physics_objects.py - PhysicsObject, Ball, Cushion classes
- ui_objects.py    - Button, Cue, PowerMeter, Pocket classes
- renderer.py      - GameRenderer class
- game.py          - PoolGame class (main game logic)
"""


if __name__ == "__main__":
    """
    __name__ == "__main__" artinya script ini dijalankan langsung (bukan di-import).
    
    Praktik baik: Selalu wrap main code dalam `if __name__ == "__main__":`
    Ini memungkinkan file ini di-import tanpa langsung menjalankan game.
    """
    
    # ========== CREATE GAME INSTANCE ==========
    # Buat satu instance dari PoolGame
    game = PoolGame()
    
    # ========== START GAME LOOP ==========
    # Jalankan main game loop
    # Method ini akan block sampai game di-quit
    game.run_game()
