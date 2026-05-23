import pygame


class InputHandler:
    """
    Kelas untuk menangani semua event input (mouse, keyboard, quit).
    Encapsulation: semua logika input handling dikelola di sini.
    
    Method ini adalah static, jadi bisa dipanggil tanpa create instance.
    Contoh: InputHandler.handle_events(game)
    """
    
    @staticmethod
    def handle_events(game):
        """
        Memproses semua event pygame.
        Method ini mengecek mouse clicks dan quit event.
        
        Proses:
        1. Loop melalui semua event dalam pygame event queue
        2. Jika MOUSEBUTTONDOWN dan game.taking_shot = True -> set powering_up = True
        3. Jika MOUSEBUTTONUP dan game.taking_shot = True -> set powering_up = False
        4. Jika QUIT event -> return False (stop game loop)
        
        Args:
            game: PoolGame object yang memegang game state
            
        Returns:
            bool: True jika game harus terus berjalan, False jika harus quit
        """
        for event in pygame.event.get():
            # ========== MOUSE BUTTON DOWN ==========
            # Ketika pemain menekan mouse button
            if event.type == pygame.MOUSEBUTTONDOWN and game.taking_shot:
                # Mulai power up (power meter akan mulai naik)
                game.powering_up = True
            
            # ========== MOUSE BUTTON UP ==========
            # Ketika pemain melepas mouse button
            elif event.type == pygame.MOUSEBUTTONUP and game.taking_shot:
                # Stop power up
                game.powering_up = False
            
            # ========== QUIT EVENT ==========
            # Ketika user close window atau press Ctrl+C
            elif event.type == pygame.QUIT:
                return False  # Signal untuk quit game loop
        
        # Game masih berjalan
        return True
