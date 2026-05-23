import pymunk
from config import GameConfig


class PhysicsObject:
    """
    Kelas base (induk) untuk semua object fisika dalam game.
    Menggunakan prinsip inheritance untuk mengurangi duplikasi kode.
    Semua object fisika (Ball, Cushion) akan mewarisi method dari class ini.
    """
    
    def __init__(self, space, static_body):
        """
        Inisialisasi object fisika.
        
        Args:
            space: Pymunk space untuk simulasi fisika
            static_body: Static body untuk reference dalam physics calculations
        """
        self.space = space                  # Ruang fisika Pymunk
        self.static_body = static_body      # Reference untuk static body
        self.body = None                    # Dynamic body (akan dibuat di subclass)
        self.shape = None                   # Shape/bentuk object (lingkaran, polygon, dll)
    
    def create_body(self):
        """
        Template method - method abstrak yang harus diimplementasikan oleh subclass.
        Setiap subclass harus membuat body mereka sendiri sesuai kebutuhan.
        Ini adalah contoh dari Template Method Pattern.
        """
        raise NotImplementedError("Subclass harus mengimplementasikan create_body()")
    
    def get_position(self):
        """
        Mendapatkan posisi object fisika secara aman.
        Encapsulation: mengabstraksi akses langsung ke body.position
        
        Returns:
            tuple: (x, y) posisi object, atau None jika tidak ada body
        """
        return self.body.position if self.body else None
    
    def set_velocity(self, velocity):
        """
        Mengatur kecepatan object secara aman.
        
        Args:
            velocity: tuple (vx, vy) untuk kecepatan x dan y
        """
        if self.body:
            self.body.velocity = velocity
    
    def apply_impulse(self, impulse, local_point=(0, 0)):
        """
        Menerapkan impuls (gaya sesaat) ke object fisika.
        Ini digunakan untuk melempar bola saat pemain melakukan shot.
        
        Args:
            impulse: tuple (fx, fy) untuk gaya x dan y
            local_point: tuple titik aplikasi gaya relative ke center of mass
        """
        if self.body:
            self.body.apply_impulse_at_local_point(impulse, local_point)


class Ball(PhysicsObject):
    """
    Kelas untuk merepresentasikan bola dalam game pool.
    Mewarisi dari PhysicsObject dan mengimplementasikan create_body() khusus untuk bola.
    
    Inheritance: Child class dari PhysicsObject
    Polymorphism: Menggunakan method dari parent dengan cara yang spesifik untuk bola
    """
    
    def __init__(self, space, static_body, radius, pos, is_cue=False):
        """
        Inisialisasi bola pool.
        
        Args:
            space: Pymunk space untuk simulasi
            static_body: Reference static body
            radius: Jari-jari bola (diameter / 2)
            pos: tuple (x, y) posisi awal bola
            is_cue: boolean, True jika ini adalah bola putih (cue ball), False untuk bola lain
        """
        super().__init__(space, static_body)  # Call parent constructor
        self.radius = radius                  # Jari-jari bola
        self.pos = pos                        # Posisi awal
        self.is_cue = is_cue                  # Flag untuk mengidentifikasi bola putih
        self.image = None                     # Gambar bola (akan diset kemudian)
        self.create_body()                    # Buat physics body untuk bola
    
    def create_body(self):
        """
        Membuat physics body untuk bola.
        Mengimplementasikan template method dari parent class.
        
        Proses:
        1. Buat body yang dapat bergerak (dynamic body)
        2. Set posisi awal
        3. Buat shape lingkaran dengan radius yang ditentukan
        4. Set properties fisika: mass (5 kg), elasticity (0.8 untuk pantul)
        5. Tambahkan pivot joint untuk simulasi friction
        6. Daftarkan ke Pymunk space
        """
        # Buat dynamic body (body yang bisa bergerak)
        self.body = pymunk.Body()
        
        # Set posisi awal bola
        self.body.position = self.pos
        
        # Buat shape lingkaran untuk bola
        self.shape = pymunk.Circle(self.body, self.radius)
        
        # Set massa bola (5 kg)
        self.shape.mass = 5
        
        # Set elasticity (pantul) = 0.8 (80% energy kembali setelah tubrukan)
        self.shape.elasticity = 0.8
        
        # Tambahkan pivot joint untuk simulasi gesekan (friction)
        # Ini membuat bola melambat seiring waktu (seperti real pool)
        pivot = pymunk.PivotJoint(self.static_body, self.body, (0, 0), (0, 0))
        pivot.max_bias = 0          # Tidak ada bias correction
        pivot.max_force = 1000      # Gaya maksimal friction
        
        # Set filter untuk collision detection
        self.shape.filter = pymunk.ShapeFilter(categories=0b1)
        
        # Daftarkan body dan shape ke physics space
        self.space.add(self.body, self.shape, pivot)
    
    def is_moving(self):
        """
        Mengecek apakah bola sedang bergerak.
        Digunakan untuk mendeteksi ketika semua bola berhenti (ready untuk shot berikutnya).
        
        Returns:
            bool: True jika bola bergerak (velocity != 0), False jika berhenti
        """
        vx = int(self.body.velocity[0])  # Kecepatan horizontal
        vy = int(self.body.velocity[1])  # Kecepatan vertikal
        return vx != 0 or vy != 0        # Bergerak jika salah satu velocity != 0
    
    def reset_position(self, new_pos):
        """
        Mengembalikan bola ke posisi tertentu dengan velocity = 0.
        Digunakan untuk reset posisi bola putih setelah kena lubang.
        
        Args:
            new_pos: tuple (x, y) posisi baru untuk bola
        """
        self.body.position = new_pos         # Set posisi baru
        self.body.velocity = (0.0, 0.0)      # Reset velocity (berhenti)
    
    def set_image(self, image):
        """
        Mengatur gambar untuk bola ini.
        Digunakan untuk rendering bola di layar.
        
        Args:
            image: pygame Surface object berisi gambar bola
        """
        self.image = image


class Cushion(PhysicsObject):
    """
    Kelas untuk merepresentasikan bantalan (dinding elastis) di meja pool.
    Mewarisi dari PhysicsObject dan mengimplementasikan create_body() khusus untuk cushion.
    
    Cushion adalah static object (tidak bergerak) yang memantulkan bola.
    """
    
    def __init__(self, space, static_body, poly_dims):
        """
        Inisialisasi cushion (dinding/bantalan).
        
        Args:
            space: Pymunk space untuk simulasi
            static_body: Reference static body
            poly_dims: List of tuples berisi koordinat polygon (contoh: [(x1,y1), (x2,y2), ...])
        """
        super().__init__(space, static_body)  # Call parent constructor
        self.poly_dims = poly_dims            # Dimensi polygon untuk bentuk cushion
        self.create_body()                    # Buat physics body
    
    def create_body(self):
        """
        Membuat static physics body untuk cushion.
        Mengimplementasikan template method dari parent class.
        
        Cushion adalah STATIC (tidak bergerak), berbeda dengan Ball yang DYNAMIC.
        Shape adalah polygon (bentuk dengan banyak sudut) bukan lingkaran.
        """
        # Buat static body (body yang tidak bergerak)
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        
        # Set posisi ke origin (0, 0) untuk static body
        self.body.position = (0, 0)
        
        # Buat shape polygon dari koordinat yang diberikan
        # Kurva polygon harus didefinisikan relative ke body position
        self.shape = pymunk.Poly(
            self.body,
            [(x - self.body.position.x, y - self.body.position.y) 
             for (x, y) in self.poly_dims]
        )
        
        # Set elasticity = 0.8 (sama dengan ball, untuk pantul yang baik)
        self.shape.elasticity = 0.8
        
        # Set filter untuk collision detection
        self.shape.filter = pymunk.ShapeFilter(categories=0b10)
        
        # Daftarkan body dan shape ke physics space
        self.space.add(self.body, self.shape)
