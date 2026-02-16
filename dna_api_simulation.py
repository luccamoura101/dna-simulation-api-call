#Made by Lucca Moura Arantes (ID:100001712), Moaz Ashry(ID:100001739)

import sys
import requests
import random
import math
import tkinter as tk
from tkinter import ttk, scrolledtext

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    import pygame
    from pygame.locals import *
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    print("Warning: PyOpenGL or pygame not found. Install with: pip install PyOpenGL pygame")

# DNA bases
BASES = ['A', 'T', 'G', 'C']

# Complementary base pairing rules
COMPLEMENT = {
    'A': 'T',
    'T': 'A',
    'G': 'C',
    'C': 'G'
}

# Color scheme for bases (RGB float tuples for OpenGL)
BASE_COLORS_GL = {
    'A': (1.0, 0.42, 0.42),   # Red
    'T': (0.31, 0.80, 0.77),  # Cyan
    'G': (1.0, 0.90, 0.43),   # Yellow
    'C': (0.58, 0.88, 0.83),  # Green
}

# Hex colors for tkinter widgets
BASE_COLORS_HEX = {
    'A': '#FF6B6B',
    'T': '#4ECDC4',
    'G': '#FFE66D',
    'C': '#95E1D3',
}

# Animal names from the API (as shown in your screenshot)
ANIMALS = {
    "dog": "Canis lupus familiaris",
    "cat": "Felis catus",
    "horse": "Equus caballus",
    "cow": "Bos taurus",
    "pig": "Sus scrofa",
    "chicken": "Gallus gallus",
    "mouse": "Mus musculus",
    "rat": "Rattus norvegicus",
    "rabbit": "Oryctolagus cuniculus",
    "sheep": "Ovis aries",
    "goat": "Capra hircus",
    "elephant": "Loxodonta africana",
    "lion": "Panthera leo",
    "tiger": "Panthera tigris",
    "bear": "Ursus arctos",
    "wolf": "Canis lupus",
    "dolphin": "Tursiops truncatus",
    "whale": "Balaenoptera musculus",
    "eagle": "Aquila chrysaetos",
    "frog": "Xenopus laevis",
    "human": "Homo sapiens",
    "chimpanzee": "Pan troglodytes",
    "gorilla": "Gorilla gorilla",
    "zebra": "Equus quagga",
    "panda": "Ailuropoda melanoleuca",
    "penguin": "Aptenodytes forsteri",
    "snake": "Python bivittatus",
    "turtle": "Chelonia mydas",
    "salmon": "Salmo salar",
    "shark": "Carcharodon carcharias"
}

def fetch_dna_from_api(api_url, params=None):
    """
    Fetch DNA sequence from API using requests library
    This demonstrates the Request.json method as required
    """
    try:
        print(f"Fetching data from API: {api_url}")
        response = requests.get(api_url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("✓ API request successful!")
            return data
        else:
            print(f"✗ API request failed with status code: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"✗ Error fetching from API: {e}")
        return None


def generate_dna_strand(length):
    """Generate a random DNA strand of specified length"""
    return ''.join(random.choice(BASES) for _ in range(length))


def get_complement_strand(strand):
    """Get the complementary DNA strand"""
    return ''.join(COMPLEMENT[base] for base in strand)


def calculate_gc_content(strand):
    """Calculate GC content percentage"""
    gc_count = strand.count('G') + strand.count('C')
    return (gc_count / len(strand)) * 100


def get_statistics_text(strand, source="Random Generation"):
    """Return a formatted statistics string"""
    gc = calculate_gc_content(strand)
    lines = [
        f"Source: {source}",
        f"Total length: {len(strand)} base pairs",
        f"GC Content: {gc:.2f}%",
        f"AT Content: {100 - gc:.2f}%",
        "",
        "Base counts:",
    ]
    for base in BASES:
        count = strand.count(base)
        comp = COMPLEMENT[base]
        lines.append(f"  {base}–{comp}: {count} pairs ({count / len(strand) * 100:.1f}%)")
    return "\n".join(lines)


def get_text_helix(strand1, strand2, bases_per_line=50):
    """Return a text representation of the DNA double helix"""
    lines = []
    for i in range(0, len(strand1), bases_per_line):
        c1 = strand1[i:i + bases_per_line]
        c2 = strand2[i:i + bases_per_line]
        lines.append(f"Position {i:3d}–{min(i + bases_per_line - 1, len(strand1) - 1):3d}:")
        lines.append(f"5' {c1} 3'")
        lines.append(f"   {'|' * len(c1)}")
        lines.append(f"3' {c2} 5'")
        lines.append("")
    return "\n".join(lines)


def _draw_sphere(x, y, z, r, color, slices=12, stacks=12):
    """Draw a solid sphere at (x, y, z) with radius r."""
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(*color)
    quad = gluNewQuadric()
    gluSphere(quad, r, slices, stacks)
    gluDeleteQuadric(quad)
    glPopMatrix()


def _draw_cylinder_between(p1, p2, radius, color):
    """Draw a cylinder between two 3-D points."""
    dx, dy, dz = p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-6:
        return

    glPushMatrix()
    glTranslatef(*p1)

    # Rotation to align cylinder with direction vector
    if abs(dz / length) > 0.999:
        ax, ay, az, angle = 0, 1, 0, 0 if dz > 0 else 180
    else:
        ax = -dy
        ay = dx
        az = 0
        angle = math.degrees(math.acos(dz / length))
    glRotatef(angle, ax, ay, az)

    glColor3f(*color)
    quad = gluNewQuadric()
    gluCylinder(quad, radius, radius, length, 10, 1)
    gluDeleteQuadric(quad)
    glPopMatrix()


def _render_helix(st):
    """Render the 3-D DNA helix (called each frame)."""
    strand1 = st["strand1"]
    strand2 = st["strand2"]
    length = len(strand1)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, st["zoom"])
    glRotatef(st["rotation_x"], 1, 0, 0)
    glRotatef(st["rotation_y"], 0, 1, 0)

    # Centre the helix vertically
    half = length * 0.5 * 0.5
    glTranslatef(0, -half, 0)

    helix_radius = 3.0
    rise_per_bp = 0.5  # vertical rise per base pair
    twist = 2 * math.pi / 10  # 10 bp per full turn

    prev1, prev2 = None, None
    for i in range(length):
        angle = i * twist
        y = i * rise_per_bp
        x1 = helix_radius * math.cos(angle)
        z1 = helix_radius * math.sin(angle)
        x2 = helix_radius * math.cos(angle + math.pi)
        z2 = helix_radius * math.sin(angle + math.pi)

        p1 = (x1, y, z1)
        p2 = (x2, y, z2)

        c1 = BASE_COLORS_GL[strand1[i]]
        c2 = BASE_COLORS_GL[strand2[i]]

        # Nucleotide spheres
        _draw_sphere(*p1, 0.35, c1)
        _draw_sphere(*p2, 0.35, c2)

        # Hydrogen bond (connector between base pair)
        _draw_cylinder_between(p1, p2, 0.06, (0.6, 0.6, 0.6))

        # Backbone segments
        if prev1 is not None:
            _draw_cylinder_between(prev1, p1, 0.12, (0.25, 0.25, 0.25))
            _draw_cylinder_between(prev2, p2, 0.12, (0.25, 0.25, 0.25))

        prev1, prev2 = p1, p2


def _setup_viewport(w, h):
    """Configure the OpenGL viewport and projection."""
    if h == 0:
        h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, w / h, 0.5, 200.0)
    glMatrixMode(GL_MODELVIEW)


def launch_opengl_helix(strand1, strand2):
    """Open a pygame + OpenGL window showing a 3-D rotating DNA helix."""
    if not OPENGL_AVAILABLE:
        print("Cannot launch OpenGL viewer - PyOpenGL or pygame is not installed.")
        return

    st = {
        "strand1": strand1,
        "strand2": strand2,
        "rotation_y": 0.0,
        "rotation_x": 15.0,
        "zoom": -60.0,
        "auto_rotate": True,
        "dragging": False,
        "mouse_last": None,
    }

    pygame.init()
    screen_w, screen_h = 900, 700
    pygame.display.set_mode((screen_w, screen_h), DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption("DNA Double Helix - OpenGL")

    glClearColor(0.08, 0.08, 0.12, 1.0)
    glEnable(GL_DEPTH_TEST)

    # Basic lighting
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 10.0, 15.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])

    _setup_viewport(screen_w, screen_h)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == VIDEORESIZE:
                screen_w, screen_h = event.w, event.h
                pygame.display.set_mode((screen_w, screen_h), DOUBLEBUF | OPENGL | RESIZABLE)
                _setup_viewport(screen_w, screen_h)

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE:
                    st["auto_rotate"] = not st["auto_rotate"]
                elif event.key in (K_PLUS, K_EQUALS):
                    st["zoom"] += 2
                elif event.key == K_MINUS:
                    st["zoom"] -= 2

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # left click
                    st["dragging"] = True
                    st["mouse_last"] = event.pos
                elif event.button == 4:  # scroll up
                    st["zoom"] += 2
                elif event.button == 5:  # scroll down
                    st["zoom"] -= 2

            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    st["dragging"] = False

            elif event.type == MOUSEMOTION:
                if st["dragging"] and st["mouse_last"]:
                    lx, ly = st["mouse_last"]
                    mx, my = event.pos
                    st["rotation_y"] += (mx - lx) * 0.5
                    st["rotation_x"] += (my - ly) * 0.5
                    st["mouse_last"] = event.pos
                    st["auto_rotate"] = False

        if st["auto_rotate"]:
            st["rotation_y"] += 0.4

        _render_helix(st)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

class DNASimulationApp:
    """Full tkinter GUI for the DNA simulation."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DNA Simulation – API + OpenGL")
        self.root.geometry("960x720")
        self.root.configure(bg="#1e1e2e")

        self.primary_strand = ""
        self.complement_strand = ""

        self._build_ui()

    # ---- UI construction ---------------------------------------------------

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e2e")
        style.configure("TLabel", background="#1e1e2e", foreground="#cdd6f4",
                         font=("Helvetica", 11))
        style.configure("Header.TLabel", font=("Helvetica", 16, "bold"),
                         foreground="#89b4fa")
        style.configure("TButton", font=("Helvetica", 11, "bold"),
                         padding=6)

        # Header
        header = ttk.Label(self.root, text="🧬  DNA Simulation  –  OpenGL + Tkinter",
                           style="Header.TLabel")
        header.pack(pady=(12, 4))

        # Controls frame
        ctrl = ttk.Frame(self.root)
        ctrl.pack(fill=tk.X, padx=16, pady=6)

        ttk.Label(ctrl, text="Base pairs:").pack(side=tk.LEFT, padx=(0, 4))
        self.bp_var = tk.IntVar(value=100)
        bp_spin = ttk.Spinbox(ctrl, from_=10, to=500, width=6,
                              textvariable=self.bp_var)
        bp_spin.pack(side=tk.LEFT, padx=(0, 12))

        gen_btn = ttk.Button(ctrl, text="Generate DNA",
                             command=self._on_generate)
        gen_btn.pack(side=tk.LEFT, padx=4)

        api_btn = ttk.Button(ctrl, text="Demo API Call",
                             command=self._on_api_demo)
        api_btn.pack(side=tk.LEFT, padx=4)

        gl_btn = ttk.Button(ctrl, text="Open 3-D Helix (OpenGL)",
                            command=self._on_open_gl)
        gl_btn.pack(side=tk.LEFT, padx=4)

        # Notebook (tabs) for stats / text helix / api log
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 12))

        # -- Statistics tab --
        stats_frame = ttk.Frame(self.tabs)
        self.tabs.add(stats_frame, text="  Statistics  ")
        self._build_stats_tab(stats_frame)

        # -- Text Helix tab --
        helix_frame = ttk.Frame(self.tabs)
        self.tabs.add(helix_frame, text="  Text Helix  ")
        self.helix_text = scrolledtext.ScrolledText(helix_frame, wrap=tk.NONE,
                                                     font=("Courier", 11),
                                                     bg="#181825", fg="#cdd6f4",
                                                     insertbackground="#cdd6f4")
        self.helix_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # -- API Log tab --
        api_frame = ttk.Frame(self.tabs)
        self.tabs.add(api_frame, text="  API Log  ")
        self.api_text = scrolledtext.ScrolledText(api_frame, wrap=tk.WORD,
                                                   font=("Courier", 11),
                                                   bg="#181825", fg="#a6e3a1",
                                                   insertbackground="#a6e3a1")
        self.api_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # -- Legend at bottom --
        legend = ttk.Frame(self.root)
        legend.pack(fill=tk.X, padx=16, pady=(0, 8))
        ttk.Label(legend, text="Color key:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        for base in BASES:
            lbl = tk.Label(legend, text=f"  {base}–{COMPLEMENT[base]}  ",
                           bg=BASE_COLORS_HEX[base], fg="black",
                           font=("Helvetica", 10, "bold"), padx=6, pady=2,
                           relief=tk.RIDGE)
            lbl.pack(side=tk.LEFT, padx=3)

    def _build_stats_tab(self, parent):
        """Build a visual statistics dashboard inside *parent*."""
        self.stats_canvas = tk.Canvas(parent, bg="#181825", highlightthickness=0)
        self.stats_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.stats_canvas.bind("<Configure>", lambda e: self._draw_stats())

    def _on_generate(self):
        bp = self.bp_var.get()
        self.primary_strand = generate_dna_strand(bp)
        self.complement_strand = get_complement_strand(self.primary_strand)

        # Update text helix tab
        self.helix_text.delete("1.0", tk.END)
        self.helix_text.insert(tk.END, get_text_helix(self.primary_strand,
                                                       self.complement_strand))

        # Update stats
        self._draw_stats()
        self.tabs.select(0)  # switch to stats tab

    def _on_api_demo(self):
        self.api_text.delete("1.0", tk.END)
        self.api_text.insert(tk.END, "Demonstrating API call with requests.json()\n")
        self.api_text.insert(tk.END, "=" * 60 + "\n\n")

        # --- API Call 1: Dog CEO API (breed list) ---
        api_url = "https://dog.ceo/api/breeds/list/all"
        self.api_text.insert(tk.END, f"[1] Endpoint: {api_url}\n")
        self.api_text.insert(tk.END, "Sending GET request…\n\n")
        self.root.update_idletasks()

        data = fetch_dna_from_api(api_url)
        if data is not None:
            self.api_text.insert(tk.END, "✓ Response received (.json() parsed):\n")
            import json
            breeds = list(data.get("message", {}).keys())[:15]
            self.api_text.insert(tk.END, f"   Status field : {data.get('status')}\n")
            self.api_text.insert(tk.END, f"   Total breeds : {len(data.get('message', {}))}\n")
            self.api_text.insert(tk.END, f"   First 15     : {', '.join(breeds)}\n")
        else:
            self.api_text.insert(tk.END, "✗ Request failed - check your internet connection.\n")

        # --- API Call 2: Random dog image ---
        api_url2 = "https://dog.ceo/api/breeds/image/random"
        self.api_text.insert(tk.END, f"\n[2] Endpoint: {api_url2}\n")
        self.api_text.insert(tk.END, "Sending GET request…\n\n")
        self.root.update_idletasks()

        data2 = fetch_dna_from_api(api_url2)
        if data2 is not None:
            self.api_text.insert(tk.END, "✓ Response received (.json() parsed):\n")
            import json
            self.api_text.insert(tk.END, json.dumps(data2, indent=2) + "\n")
        else:
            self.api_text.insert(tk.END, "✗ Request failed - check your internet connection.\n")

        self.api_text.insert(tk.END, "\n\n" + "-" * 60 + "\n")
        self.api_text.insert(tk.END, "AVAILABLE ANIMALS IN DATABASE:\n" + "-" * 60 + "\n")
        for common, scientific in ANIMALS.items():
            self.api_text.insert(tk.END, f"  {common:15} → {scientific}\n")

        self.tabs.select(2)  # switch to API tab

    def _on_open_gl(self):
        if not self.primary_strand:
            self._on_generate()
        # Launch in a separate process so the tkinter loop is not blocked
        import multiprocessing
        p = multiprocessing.Process(target=launch_opengl_helix,
                                    args=(self.primary_strand,
                                          self.complement_strand))
        p.start()

    def _draw_stats(self):
        c = self.stats_canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 10 or h < 10:
            return

        strand = self.primary_strand
        if not strand:
            c.create_text(w // 2, h // 2,
                          text="Press 'Generate DNA' to see statistics",
                          fill="#585b70", font=("Helvetica", 14))
            return

        # ---- Left side: bar chart ----
        counts = {b: strand.count(b) for b in BASES}
        max_count = max(counts.values(), default=1)
        bar_area_w = w * 0.45
        bar_area_h = h * 0.65
        bar_x0 = 40
        bar_y0 = 60
        bar_w = bar_area_w / (len(BASES) * 1.6)
        gap = bar_w * 0.6

        c.create_text(bar_x0 + bar_area_w / 2, 24,
                      text="Base Composition", fill="#89b4fa",
                      font=("Helvetica", 13, "bold"))

        for idx, base in enumerate(BASES):
            x = bar_x0 + idx * (bar_w + gap)
            bar_h = (counts[base] / max_count) * bar_area_h if max_count else 0
            y_top = bar_y0 + bar_area_h - bar_h
            y_bot = bar_y0 + bar_area_h
            c.create_rectangle(x, y_top, x + bar_w, y_bot,
                               fill=BASE_COLORS_HEX[base], outline="black", width=2)
            c.create_text(x + bar_w / 2, y_bot + 16, text=base,
                          fill="#cdd6f4", font=("Helvetica", 12, "bold"))
            c.create_text(x + bar_w / 2, y_top - 12, text=str(counts[base]),
                          fill="#cdd6f4", font=("Helvetica", 11, "bold"))

        # ---- Right side: GC / AT pie ----
        gc = calculate_gc_content(strand)
        at = 100 - gc
        cx_pie = w * 0.72
        cy_pie = h * 0.42
        r = min(w * 0.18, h * 0.30)

        # GC slice (start from top, clockwise)
        gc_extent = 3.6 * gc  # degrees
        c.create_arc(cx_pie - r, cy_pie - r, cx_pie + r, cy_pie + r,
                     start=90, extent=-gc_extent, fill="#FFD93D", outline="black",
                     width=2, style=tk.PIESLICE)
        c.create_arc(cx_pie - r, cy_pie - r, cx_pie + r, cy_pie + r,
                     start=90 - gc_extent, extent=-(360 - gc_extent),
                     fill="#6BCB77", outline="black", width=2, style=tk.PIESLICE)

        c.create_text(cx_pie, cy_pie - r - 18,
                      text="GC / AT Content", fill="#89b4fa",
                      font=("Helvetica", 13, "bold"))
        c.create_text(cx_pie, cy_pie,
                      text=f"GC {gc:.1f}%\nAT {at:.1f}%",
                      fill="black", font=("Helvetica", 12, "bold"))

        # ---- Bottom: summary text ----
        summary = get_statistics_text(strand)
        c.create_text(w // 2, h - 50, text=summary, fill="#a6adc8",
                      font=("Courier", 10), anchor=tk.S, justify=tk.CENTER)

def main():
    """Launch the tkinter GUI."""
    root = tk.Tk()
    DNASimulationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
