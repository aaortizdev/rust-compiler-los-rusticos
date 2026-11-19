import os
import re
import sys
import traceback
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)
os.chdir(BASE)

if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")

import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

import nucleo_analisis as na

# ============================================================
# Paleta (tonos claros y suaves)
# ============================================================

DESARROLLADORES = ("aaortizdev", "jonaguilera13", "ChrisPal2307")

C = {
    "app": "#f4f5f9",          # fondo general
    "superficie": "#ffffff",   # tarjetas
    "borde": "#e4e7ef",
    "borde_suave": "#eef0f5",
    "texto": "#2d3142",
    "suave": "#8b91a3",
    "tenue": "#b6bbc8",
    "hover": "#f0f2f7",
    "acento": "#7180cf", "acento_hover": "#6170bf", "acento_tinte": "#eef0fb", "acento_texto": "#4d5aa6",
    "ok": "#3f8f6b", "ok_tinte": "#e7f5ee",
    "error": "#c25563", "error_tinte": "#fdeef0",
    "aviso": "#946812", "aviso_tinte": "#fff7e6",
    "linea_error": "#fff1f2", "token_error": "#f9d3d9",
    "linea_actual": "#f7f8fc", "margen": "#fafbfd",
    "seleccion": "#e3e8fa", "destacado": "#fff3c4",
}

# Cada fase tiene: texto (oscuro), tinte (fondo claro), hover y sólido (marcas)
FASE = {
    na.FASE_LEXICO: {"nombre": "Léxico", "clave": "lex", "texto": "#2f6d8c", "tinte": "#e5f1f8",
                     "hover": "#d6e9f3", "solido": "#72b0cc", "fila": "#f5fafd"},
    na.FASE_SINTACTICO: {"nombre": "Sintáctico", "clave": "sin", "texto": "#8a6421", "tinte": "#f9efdc",
                         "hover": "#f3e4c8", "solido": "#d9aa55", "fila": "#fefaf2"},
    na.FASE_SEMANTICO: {"nombre": "Semántico", "clave": "sem", "texto": "#2f7867", "tinte": "#e2f3ee",
                        "hover": "#d1ebe3", "solido": "#62b5a1", "fila": "#f4fbf8"},
}
FASE_POR_CLAVE = {v["clave"]: k for k, v in FASE.items()}
ORDEN_FASE = {na.FASE_LEXICO: 0, na.FASE_SINTACTICO: 1, na.FASE_SEMANTICO: 2}

PALABRAS_CLAVE = (
    "as async await break const continue crate dyn else enum extern false fn for if impl in "
    "let loop match mod move mut pub ref return self Self static struct super trait true type "
    "union unsafe use where while"
).split()
TIPOS = ("i8 i16 i32 i64 i128 isize u8 u16 u32 u64 u128 usize f32 f64 bool char str "
         "String Vec Option Result").split()

PATRONES_RESALTADO = [
    ("sx_macro", re.compile(r"\b[A-Za-z_]\w*!")),
    ("sx_kw", re.compile(r"\b(?:" + "|".join(PALABRAS_CLAVE) + r")\b")),
    ("sx_tipo", re.compile(r"\b(?:" + "|".join(TIPOS) + r")\b")),
    ("sx_num", re.compile(r"\b\d[\d_]*(?:\.\d[\d_]*)?(?:[iuf](?:8|16|32|64|128|size))?\b")),
    ("sx_fn", re.compile(r"(?<=\bfn )\s*[A-Za-z_]\w*")),
    ("sx_char", re.compile(r"'(?:[^'\\\n]|\\.)'")),
    ("sx_str", re.compile(r'"(?:[^"\\]|\\.)*"?')),
    ("sx_com", re.compile(r"//[^\n]*|/\*[\s\S]*?(?:\*/|$)")),
]

COLORES_SINTAXIS = {
    "sx_kw": "#b4566f", "sx_tipo": "#2f8585", "sx_num": "#b0772a", "sx_fn": "#4a6fbf",
    "sx_macro": "#8763c4", "sx_char": "#4b8b52", "sx_str": "#4b8b52", "sx_com": "#a0a6b5",
}


def fuente_monoespaciada():
    disponibles = set(tkfont.families())
    for nombre in ("Cascadia Mono", "Consolas", "Menlo", "DejaVu Sans Mono", "Courier New"):
        if nombre in disponibles:
            return nombre
    return "TkFixedFont"


def rectangulo_redondeado(canvas, x1, y1, x2, y2, r, **opciones):
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    puntos = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
              x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(puntos, smooth=True, **opciones)


# ============================================================
# Componentes
# ============================================================

def paleta(normal, hover=None, presionado=None, seleccionado=None, deshabilitado=None):
    """Cada estado es (relleno, texto, borde). None en relleno/borde = transparente."""
    hover = hover or normal
    return {
        "normal": normal, "hover": hover, "presionado": presionado or hover,
        "seleccionado": seleccionado or normal,
        "deshabilitado": deshabilitado or (None, C["tenue"], None),
    }


class Pildora(tk.Canvas):
    """Botón / etiqueta con esquinas redondeadas dibujado en un Canvas."""

    def __init__(self, master, texto, fondo, paleta_colores, fuente, comando=None, punto=None,
                 padx=14, pady=6, radio=None, escala=1.0):
        super().__init__(master, background=fondo, highlightthickness=0, borderwidth=0,
                         cursor="hand2" if comando else "")
        self.texto = texto
        self.fondo = fondo
        self.paleta = paleta_colores
        self.fuente = fuente
        self.comando = comando
        self.punto = punto
        self.padx, self.pady = int(padx * escala), int(pady * escala)
        self.radio = radio if radio is None else int(radio * escala)
        self.escala = escala
        self.estado = "normal"
        self.seleccionado = False
        self._hover = False
        self._presionado = False
        if comando:
            self.bind("<Enter>", lambda e: self._set(hover=True))
            self.bind("<Leave>", lambda e: self._set(hover=False, presionado=False))
            self.bind("<ButtonPress-1>", lambda e: self._set(presionado=True))
            self.bind("<ButtonRelease-1>", self._soltar)
        self._dibujar()

    def _set(self, hover=None, presionado=None):
        if hover is not None:
            self._hover = hover
        if presionado is not None:
            self._presionado = presionado
        self._dibujar()

    def _soltar(self, evento):
        dentro = 0 <= evento.x <= self.winfo_width() and 0 <= evento.y <= self.winfo_height()
        self._presionado = False
        self._dibujar()
        if dentro and self.estado == "normal" and self.comando:
            self.comando()

    def _colores(self):
        if self.estado == "disabled":
            return self.paleta["deshabilitado"]
        if self.seleccionado:
            return self.paleta["seleccionado"]
        if self._presionado:
            return self.paleta["presionado"]
        if self._hover:
            return self.paleta["hover"]
        return self.paleta["normal"]

    def _dibujar(self):
        self.delete("all")
        ancho_texto = self.fuente.measure(self.texto)
        alto_texto = self.fuente.metrics("linespace")
        diametro = int(7 * self.escala)
        extra = diametro + int(7 * self.escala) if self.punto else 0
        w = ancho_texto + 2 * self.padx + extra
        h = alto_texto + 2 * self.pady
        if int(self.cget("width")) != w or int(self.cget("height")) != h:
            self.configure(width=w, height=h)
        relleno, color_texto, borde = self._colores()
        radio = h / 2 if self.radio is None else self.radio
        if relleno or borde:
            rectangulo_redondeado(self, 1, 1, w - 1, h - 1, radio,
                                  fill=relleno or self.fondo, outline=borde or relleno or self.fondo)
        x = self.padx
        if self.punto:
            color_punto = self.punto if self.estado == "normal" else C["tenue"]
            cy = h / 2
            self.create_oval(x, cy - diametro / 2, x + diametro, cy + diametro / 2,
                             fill=color_punto, outline="")
            x += extra
        self.create_text(x, h / 2, anchor="w", text=self.texto, fill=color_texto, font=self.fuente)

    # API pública
    def set_texto(self, texto):
        if texto != self.texto:
            self.texto = texto
            self._dibujar()

    def set_estado(self, estado):
        self.estado = estado
        self.configure(cursor="hand2" if (self.comando and estado == "normal") else "")
        self._dibujar()

    def set_seleccionado(self, valor):
        self.seleccionado = valor
        self._dibujar()

    def set_paleta(self, paleta_colores):
        self.paleta = paleta_colores
        self._dibujar()


class PestanasPildora(tk.Frame):
    """Pestañas con forma de píldora (sustituye a ttk.Notebook)."""

    def __init__(self, master, fondo, fuente, escala, al_cambiar=None):
        super().__init__(master, background=fondo)
        self.fondo, self.fuente, self.escala = fondo, fuente, escala
        self.al_cambiar = al_cambiar
        self.cabecera = tk.Frame(self, background=fondo)
        self.cabecera.pack(side="top", fill="x", padx=10, pady=(10, 6))
        tk.Frame(self, background=C["borde_suave"], height=1).pack(side="top", fill="x")
        self.cuerpo = tk.Frame(self, background=fondo)
        self.cuerpo.pack(side="top", fill="both", expand=True)
        self.cuerpo.rowconfigure(0, weight=1)
        self.cuerpo.columnconfigure(0, weight=1)
        self.paginas = []
        self.botones = []
        self.actual = 0
        self._paleta = paleta(
            (None, C["suave"], None), hover=(C["hover"], C["texto"], None),
            seleccionado=(C["acento_tinte"], C["acento_texto"], None))

    def add(self, pagina, text):
        indice = len(self.paginas)
        boton = Pildora(self.cabecera, text, self.fondo, self._paleta, self.fuente,
                        comando=lambda i=indice: self.select(i), padx=14, pady=5, escala=self.escala)
        boton.pack(side="left", padx=(0, 4))
        pagina.grid(row=0, column=0, sticky="nsew", in_=self.cuerpo)
        self.paginas.append(pagina)
        self.botones.append(boton)
        self.select(self.actual if indice else 0)

    def select(self, indice):
        self.actual = indice
        for i, (pagina, boton) in enumerate(zip(self.paginas, self.botones)):
            boton.set_seleccionado(i == indice)
        self.paginas[indice].tkraise()
        if self.al_cambiar:
            self.al_cambiar(indice)

    def tab(self, indice, text):
        self.botones[indice].set_texto(text)


class Tooltip:
    """Pequeño cuadro de ayuda al pasar el mouse por un widget."""

    def __init__(self, widget, texto):
        self.widget, self.texto, self.ventana, self._id = widget, texto, None, None
        widget.bind("<Enter>", self._programar, add="+")
        widget.bind("<Leave>", self._ocultar, add="+")
        widget.bind("<ButtonPress>", self._ocultar, add="+")

    def _programar(self, _):
        self._id = self.widget.after(550, self._mostrar)

    def _mostrar(self):
        if self.ventana:
            return
        x = self.widget.winfo_rootx() + 6
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.ventana = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self.texto, background="#3a3f51", foreground="#f4f5f9",
                 padx=10, pady=5, font=("Segoe UI", 9)).pack()

    def _ocultar(self, _=None):
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None
        if self.ventana:
            self.ventana.destroy()
            self.ventana = None


def tarjeta(master):
    """Contenedor blanco con borde fino."""
    return tk.Frame(master, background=C["superficie"], highlightthickness=1,
                    highlightbackground=C["borde"], highlightcolor=C["borde"])


# ============================================================
# Editor de código con números de línea y marcas de error
# ============================================================

class EditorCodigo(tk.Frame):
    def __init__(self, master, fuente, escala, al_cambiar=None, al_mover_cursor=None):
        super().__init__(master, background=C["superficie"])
        self.fuente = fuente
        self.fuente_cursiva = tkfont.Font(**{**fuente.actual(), "slant": "italic"})
        self.escala = escala
        self.al_cambiar = al_cambiar
        self.al_mover_cursor = al_mover_cursor
        self.marcas = {}          # línea -> fase (barra de color del margen)
        self._id_resaltado = None

        self.margen = tk.Canvas(self, width=52, background=C["margen"],
                                highlightthickness=0, borderwidth=0)
        self.texto = tk.Text(
            self, wrap="none", undo=True, maxundo=-1, autoseparators=True,
            font=fuente, background=C["superficie"], foreground=C["texto"],
            insertbackground=C["acento"], insertwidth=2, selectbackground=C["seleccion"],
            selectforeground=C["texto"], inactiveselectbackground=C["seleccion"],
            borderwidth=0, highlightthickness=0, padx=12, pady=8, spacing1=2, spacing3=2,
            tabs=(fuente.measure("    "),),
        )
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.texto.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.texto.xview)
        self.texto.configure(yscrollcommand=self._yscroll, xscrollcommand=self.hsb.set)

        self.margen.grid(row=0, column=0, sticky="ns")
        self.texto.grid(row=0, column=1, sticky="nsew")
        self.vsb.grid(row=0, column=2, sticky="ns")
        self.hsb.grid(row=1, column=1, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        t = self.texto
        t.tag_configure("linea_actual", background=C["linea_actual"])
        for etiqueta, color in COLORES_SINTAXIS.items():
            t.tag_configure(etiqueta, foreground=color)
        t.tag_configure("sx_com", font=self.fuente_cursiva)
        t.tag_configure("linea_error", background=C["linea_error"])
        t.tag_configure("token_error", background=C["token_error"])
        t.tag_configure("seleccion_destacada", background=C["destacado"])
        t.tag_raise("linea_error", "linea_actual")
        t.tag_raise("token_error")
        t.tag_raise("seleccion_destacada")
        t.tag_raise("sel")

        t.bind("<<Modified>>", self._modificado)
        t.bind("<Tab>", self._tab)
        t.bind("<Shift-Tab>", self._shift_tab)
        t.bind("<Return>", self._enter)
        t.bind("<KeyPress-braceright>", self._llave_cierre)
        t.bind("<Control-y>", lambda e: (self._rehacer(), "break")[1])
        t.bind("<Control-Shift-Z>", lambda e: (self._rehacer(), "break")[1])
        for ev in ("<KeyRelease>", "<ButtonRelease-1>", "<FocusIn>"):
            t.bind(ev, self._cursor_movido, add="+")
        self.margen.bind("<Configure>", lambda e: self.redibujar_margen())
        t.bind("<Configure>", lambda e: self.redibujar_margen(), add="+")

    def cambiar_tamano(self, tam):
        self.fuente.configure(size=tam)
        self.fuente_cursiva.configure(size=tam)
        self.texto.configure(tabs=(self.fuente.measure("    "),))
        self.redibujar_margen()

    # ---------------- contenido ----------------
    def obtener(self):
        return self.texto.get("1.0", "end-1c")

    def establecer(self, codigo):
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", codigo)
        self.texto.edit_reset()
        self.texto.edit_modified(False)
        self.texto.mark_set("insert", "1.0")
        self.texto.see("1.0")
        self.resaltar_sintaxis()
        self.redibujar_margen()
        self._cursor_movido()

    # ---------------- eventos de edición ----------------
    def _rehacer(self):
        try:
            self.texto.edit_redo()
        except tk.TclError:
            pass

    def _modificado(self, _=None):
        if not self.texto.edit_modified():
            return
        self.texto.edit_modified(False)
        if self._id_resaltado:
            self.after_cancel(self._id_resaltado)
        self._id_resaltado = self.after(150, self.resaltar_sintaxis)
        self.redibujar_margen()
        if self.al_cambiar:
            self.al_cambiar()

    def _tab(self, _):
        t = self.texto
        if t.tag_ranges("sel"):
            primera = int(t.index("sel.first").split(".")[0])
            ultima = int(t.index("sel.last").split(".")[0])
            if t.index("sel.last").endswith(".0") and ultima > primera:
                ultima -= 1
            for n in range(primera, ultima + 1):
                t.insert(f"{n}.0", "    ")
        else:
            t.insert("insert", "    ")
        return "break"

    def _shift_tab(self, _):
        t = self.texto
        if t.tag_ranges("sel"):
            primera = int(t.index("sel.first").split(".")[0])
            ultima = int(t.index("sel.last").split(".")[0])
        else:
            primera = ultima = int(t.index("insert").split(".")[0])
        for n in range(primera, ultima + 1):
            inicio = t.get(f"{n}.0", f"{n}.4")
            quitar = len(inicio) - len(inicio.lstrip(" "))
            if quitar:
                t.delete(f"{n}.0", f"{n}.{quitar}")
        return "break"

    def _enter(self, _):
        t = self.texto
        linea = t.get("insert linestart", "insert")
        sangria = re.match(r"[ \t]*", linea).group(0)
        if linea.rstrip().endswith(("{", "(", "[")):
            sangria += "    "
        t.edit_separator()
        t.insert("insert", "\n" + sangria)
        t.see("insert")
        return "break"

    def _llave_cierre(self, _):
        t = self.texto
        antes = t.get("insert linestart", "insert")
        if antes and not antes.strip() and len(antes) >= 4:
            t.delete("insert-4c", "insert")
        return None

    def _cursor_movido(self, _=None):
        t = self.texto
        t.tag_remove("linea_actual", "1.0", "end")
        t.tag_add("linea_actual", "insert linestart", "insert lineend+1c")
        t.tag_remove("seleccion_destacada", "1.0", "end")
        self.redibujar_margen()
        if self.al_mover_cursor:
            linea, columna = t.index("insert").split(".")
            self.al_mover_cursor(int(linea), int(columna) + 1)

    def _yscroll(self, *args):
        self.vsb.set(*args)
        self.redibujar_margen()

    # ---------------- resaltado ----------------
    def resaltar_sintaxis(self):
        self._id_resaltado = None
        t = self.texto
        codigo = self.obtener()
        for etiqueta, _ in PATRONES_RESALTADO:
            t.tag_remove(etiqueta, "1.0", "end")
        for etiqueta, patron in PATRONES_RESALTADO:
            for m in patron.finditer(codigo):
                if m.end() > m.start():
                    t.tag_add(etiqueta, f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        t.tag_raise("sx_str")
        t.tag_raise("sx_com")
        for etiqueta in ("linea_error", "token_error", "seleccion_destacada", "sel"):
            t.tag_raise(etiqueta)

    def redibujar_margen(self):
        c = self.margen
        c.delete("all")
        t = self.texto
        indice = t.index("@0,0")
        ultimo = int(t.index("end-1c").split(".")[0])
        ancho = max(int(48 * self.escala), self.fuente.measure(str(ultimo)) + int(30 * self.escala))
        if int(c.cget("width")) != ancho:
            c.configure(width=ancho)
        c.create_line(ancho - 1, 0, ancho - 1, c.winfo_height(), fill=C["borde_suave"])
        linea_cursor = int(t.index("insert").split(".")[0])
        barra = max(3, int(3 * self.escala))
        while True:
            info = t.dlineinfo(indice)
            if info is None:
                break
            y, alto = info[1], info[3]
            n = int(indice.split(".")[0])
            fase = self.marcas.get(n)
            if fase:
                color = FASE[fase]["texto"]
                rectangulo_redondeado(c, 3, y + 2, 3 + barra, y + alto - 2, barra / 2,
                                      fill=FASE[fase]["solido"], outline=FASE[fase]["solido"])
            else:
                color = C["texto"] if n == linea_cursor else C["tenue"]
            c.create_text(ancho - int(12 * self.escala), y + alto / 2, anchor="e", text=str(n),
                          font=self.fuente, fill=color)
            if n >= ultimo:
                break
            indice = t.index(f"{indice}+1line")

    # ---------------- errores ----------------
    def limpiar_errores(self):
        self.marcas.clear()
        self.texto.tag_remove("linea_error", "1.0", "end")
        self.texto.tag_remove("token_error", "1.0", "end")
        self.redibujar_margen()

    def marcar_errores(self, errores):
        self.limpiar_errores()
        t = self.texto
        total = int(t.index("end-1c").split(".")[0])
        for e in errores:
            if not e.linea or e.linea > total:
                continue
            anterior = self.marcas.get(e.linea)
            if anterior is None or ORDEN_FASE[e.fase] < ORDEN_FASE[anterior]:
                self.marcas[e.linea] = e.fase
            t.tag_add("linea_error", f"{e.linea}.0", f"{e.linea}.0 lineend+1c")
            if e.columna:
                largo = self._largo_token(e)
                t.tag_add("token_error", f"{e.linea}.{e.columna - 1}",
                          f"{e.linea}.{e.columna - 1 + largo}")
        self.redibujar_margen()

    def _largo_token(self, e):
        texto_linea = self.texto.get(f"{e.linea}.0", f"{e.linea}.0 lineend")
        resto = texto_linea[e.columna - 1:]
        citado = re.search(r"'([^']+)'", e.mensaje)
        if citado and resto.startswith(citado.group(1)):
            return len(citado.group(1))
        palabra = re.match(r"[A-Za-z_0-9.]+|\"[^\"]*\"?", resto)
        if palabra:
            return len(palabra.group(0))
        return 1

    def ir_a(self, linea, columna=None, largo=None, foco=False):
        if not linea:
            return
        t = self.texto
        inicio = f"{linea}.{(columna or 1) - 1}"
        t.mark_set("insert", inicio)
        t.see(inicio)
        self._cursor_movido()
        t.tag_remove("seleccion_destacada", "1.0", "end")
        if largo:
            t.tag_add("seleccion_destacada", inicio, f"{inicio}+{largo}c")
        if foco:
            t.focus_set()

    def destacar_rango(self, inicio, fin):
        t = self.texto
        t.mark_set("insert", f"1.0+{inicio}c")
        t.see(f"1.0+{inicio}c")
        self._cursor_movido()
        t.tag_add("seleccion_destacada", f"1.0+{inicio}c", f"1.0+{fin}c")


# ============================================================
# Ventana principal
# ============================================================

class AplicacionAnalizador(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Los Rústicos · Analizador de Rust (PLY)")
        self.geometry("1400x860")
        self.minsize(1000, 640)
        self.configure(background=C["app"])
        try:
            self.state("zoomed")
        except tk.TclError:
            pass
        self.escala = max(1.0, self.winfo_fpixels("1i") / 96)

        self.ruta_archivo = None
        self.sucio = False                 # cambios sin guardar
        self.desactualizado = False        # código cambió desde el último análisis
        self.errores_actuales = []
        self.fases_ejecutadas = set()
        self.filtro = tk.StringVar(value="TODOS")
        self.tipo_log = tk.StringVar(value="Todos")
        self.desarrollador = tk.StringVar(value="")
        self.textos_log = {}
        self._tokens = []
        self._errores_visibles = []

        self._crear_fuentes()
        self._crear_estilos()
        self._crear_cabecera()
        self._crear_barra_estado()
        self._crear_barra_ejecucion()
        self._crear_cuerpo()
        self._atajos()
        self._limpiar_resultados()
        self._actualizar_titulo_archivo()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)
        self.after(50, self._posicionar_divisores)

    # ---------------- construcción ----------------
    def _crear_fuentes(self):
        familias = set(tkfont.families())
        ui = "Segoe UI" if "Segoe UI" in familias else tkfont.nametofont("TkDefaultFont").cget("family")
        semi = "Segoe UI Semibold" if "Segoe UI Semibold" in familias else ui
        peso_semi = "normal" if semi != ui else "bold"
        for nombre in ("TkDefaultFont", "TkTextFont", "TkMenuFont"):
            tkfont.nametofont(nombre).configure(family=ui, size=10)
        self.fuente_ui = tkfont.Font(family=ui, size=10)
        self.fuente_pequena = tkfont.Font(family=ui, size=9)
        self.fuente_semi = tkfont.Font(family=semi, size=10, weight=peso_semi)
        self.fuente_semi_pequena = tkfont.Font(family=semi, size=9, weight=peso_semi)
        self.fuente_titulo = tkfont.Font(family=semi, size=12, weight=peso_semi)
        self.fuente_marca = tkfont.Font(family=semi, size=13, weight=peso_semi)
        self.fuente_codigo = tkfont.Font(family=fuente_monoespaciada(), size=11)
        self.fuente_tabla = tkfont.Font(family=ui, size=10)
        self.fuente_tabla_mono = tkfont.Font(family=fuente_monoespaciada(), size=10)
        self.option_add("*TCombobox*Listbox.font", self.fuente_ui)
        self.option_add("*TCombobox*Listbox.background", C["superficie"])
        self.option_add("*TCombobox*Listbox.selectBackground", C["acento_tinte"])
        self.option_add("*TCombobox*Listbox.selectForeground", C["acento_texto"])
        self.option_add("*TCombobox*Listbox.borderWidth", 0)

    def _crear_estilos(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        e = self.escala
        s.configure(".", background=C["app"], foreground=C["texto"], bordercolor=C["borde"],
                    font=self.fuente_ui, focuscolor=C["acento"])

        # Barras de desplazamiento delgadas, sin flechas
        for orientacion in ("Vertical", "Horizontal"):
            s.layout(f"{orientacion}.TScrollbar", [
                (f"{orientacion}.Scrollbar.trough", {"sticky": "nswe", "children": [
                    (f"{orientacion}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
        s.configure("TScrollbar", troughcolor=C["superficie"], background="#d9dce5",
                    bordercolor=C["superficie"], lightcolor="#d9dce5", darkcolor="#d9dce5",
                    arrowsize=int(9 * e), gripcount=0, relief="flat")
        s.map("TScrollbar", background=[("active", "#c3c8d4")],
              lightcolor=[("active", "#c3c8d4")], darkcolor=[("active", "#c3c8d4")])

        # Tablas
        s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        alto = self.fuente_tabla.metrics("linespace") + int(12 * e)
        s.configure("Treeview", background=C["superficie"], fieldbackground=C["superficie"],
                    foreground=C["texto"], rowheight=alto, font=self.fuente_tabla, borderwidth=0)
        s.map("Treeview", background=[("selected", C["seleccion"])], foreground=[("selected", C["texto"])])
        s.configure("Treeview.Heading", font=self.fuente_semi_pequena, background=C["superficie"],
                    foreground=C["suave"], relief="flat", borderwidth=0, padding=(int(8 * e), int(6 * e)),
                    bordercolor=C["superficie"], lightcolor=C["superficie"], darkcolor=C["superficie"])
        s.map("Treeview.Heading", background=[("active", C["hover"])])

        # Combobox
        s.configure("TCombobox", padding=(int(8 * e), int(5 * e)), fieldbackground=C["superficie"],
                    background=C["superficie"], bordercolor=C["borde"], lightcolor=C["superficie"],
                    darkcolor=C["superficie"], arrowcolor=C["suave"], arrowsize=int(11 * e),
                    foreground=C["texto"], selectbackground=C["superficie"], selectforeground=C["texto"])
        s.map("TCombobox", fieldbackground=[("readonly", C["superficie"])],
              bordercolor=[("focus", C["acento"]), ("hover", "#cfd4e0")],
              background=[("active", C["superficie"])])

        # Divisores entre tarjetas (el espacio entre ellas)
        s.configure("TPanedwindow", background=C["app"])
        s.configure("Sash", sashthickness=int(12 * e), gripcount=0, background=C["app"],
                    lightcolor=C["app"], bordercolor=C["app"])

    def _pildora(self, master, texto, fondo, paleta_colores, comando=None, fuente=None, **kw):
        return Pildora(master, texto, fondo, paleta_colores, fuente or self.fuente_semi,
                       comando=comando, escala=self.escala, **kw)

    def _crear_cabecera(self):
        cab = tk.Frame(self, background=C["superficie"])
        cab.pack(side="top", fill="x")
        tk.Frame(self, background=C["borde"], height=1).pack(side="top", fill="x")
        interior = tk.Frame(cab, background=C["superficie"])
        interior.pack(fill="x", padx=16, pady=10)
        interior.columnconfigure(1, weight=1)

        izquierda = tk.Frame(interior, background=C["superficie"])
        izquierda.grid(row=0, column=0, sticky="w")

        # Marca
        tam = int(32 * self.escala)
        logo = tk.Canvas(izquierda, width=tam, height=tam, background=C["superficie"], highlightthickness=0)
        rectangulo_redondeado(logo, 1, 1, tam - 1, tam - 1, int(9 * self.escala),
                              fill=C["acento_tinte"], outline=C["acento_tinte"])
        logo.create_text(tam / 2, tam / 2, text="{ }", fill=C["acento_texto"], font=self.fuente_semi)
        logo.pack(side="left")
        marca = tk.Frame(izquierda, background=C["superficie"])
        marca.pack(side="left", padx=(10, 18))
        tk.Label(marca, text="Los Rústicos", font=self.fuente_marca, background=C["superficie"],
                 foreground=C["texto"]).pack(anchor="w")
        tk.Label(marca, text="Analizador de Rust · PLY", font=self.fuente_pequena,
                 background=C["superficie"], foreground=C["suave"]).pack(anchor="w")
        tk.Frame(izquierda, background=C["borde"], width=1, height=int(30 * self.escala)).pack(
            side="left", padx=(0, 10))

        fantasma = paleta((None, C["texto"], None), hover=(C["hover"], C["texto"], None),
                          presionado=("#e6e9f1", C["texto"], None))
        acciones = [
            ("↥  Importar", self.abrir_archivo, "Cargar un archivo .rs en el editor (Ctrl+O)"),
            ("✓  Guardar", self.guardar, "Guardar el código (Ctrl+S) · Guardar como: Ctrl+Shift+S"),
            ("✕  Limpiar", self.limpiar, "Borrar el código y los resultados"),
            ("☰  Ejemplos", self._mostrar_ejemplos, "Abrir los algoritmos de prueba de algoritmos/"),
        ]
        for texto, comando, ayuda in acciones:
            b = self._pildora(izquierda, texto, C["superficie"], fantasma, comando,
                              fuente=self.fuente_ui, padx=12, pady=7, radio=8)
            b.pack(side="left", padx=2)
            Tooltip(b, ayuda)
            if texto.endswith("Ejemplos"):
                self._boton_ejemplos = b
        self.menu_ejemplos = tk.Menu(self, tearoff=0, background=C["superficie"], foreground=C["texto"],
                                     activebackground=C["acento_tinte"], activeforeground=C["acento_texto"],
                                     relief="flat", borderwidth=1, font=self.fuente_ui)

        # --- Exportación de logs (arriba a la derecha) ---
        logs = tk.Frame(interior, background=C["superficie"])
        logs.grid(row=0, column=2, sticky="e")
        tk.Label(logs, text="Exportar log", font=self.fuente_semi_pequena, background=C["superficie"],
                 foreground=C["suave"]).pack(side="left", padx=(0, 8))
        combo_tipo = ttk.Combobox(logs, textvariable=self.tipo_log, state="readonly", width=10,
                                  values=("Todos", "Léxico", "Sintáctico", "Semántico"))
        combo_tipo.pack(side="left", padx=(0, 6))
        Tooltip(combo_tipo, "Qué log(s) generar")
        combo_dev = ttk.Combobox(logs, textvariable=self.desarrollador, width=15, values=DESARROLLADORES)
        combo_dev.pack(side="left", padx=(0, 8))
        Tooltip(combo_dev, "Desarrollador (usuario de GitHub) para el nombre del log")
        self._marcador_dev(combo_dev)
        self.desarrollador.trace_add("write", lambda *a: self._actualizar_vista_log())
        contorno = paleta((C["acento_tinte"], C["acento_texto"], None),
                          hover=("#e2e6f8", C["acento_texto"], None), presionado=("#d6dbf4", C["acento_texto"], None))
        b = self._pildora(logs, "↓  Descargar", C["superficie"], contorno, self.descargar_logs, padx=16, pady=7)
        b.pack(side="left")
        Tooltip(b, "Genera el log con el mismo formato y nombre que main.py")

        self._logs_en_segunda_fila = False

        def reacomodar(_=None):
            necesario = izquierda.winfo_reqwidth() + logs.winfo_reqwidth() + 40
            segunda = interior.winfo_width() < necesario
            if segunda != self._logs_en_segunda_fila:
                self._logs_en_segunda_fila = segunda
                if segunda:
                    logs.grid(row=1, column=0, columnspan=3, sticky="e", pady=(8, 0))
                else:
                    logs.grid(row=0, column=2, columnspan=1, sticky="e", pady=0)
        interior.bind("<Configure>", reacomodar)

    def _marcador_dev(self, combo):
        """Texto guía dentro del combobox de desarrollador cuando está vacío."""
        guia = "Desarrollador…"

        def actualizar(*_):
            if not self.desarrollador.get() and self.focus_get() is not combo:
                combo.configure(foreground=C["tenue"])
                combo.set(guia)
            elif self.desarrollador.get() == guia and self.focus_get() is combo:
                combo.set("")
                combo.configure(foreground=C["texto"])
            elif self.desarrollador.get() != guia:
                combo.configure(foreground=C["texto"])
        combo.bind("<FocusIn>", actualizar, add="+")
        combo.bind("<FocusOut>", actualizar, add="+")
        combo.bind("<<ComboboxSelected>>", actualizar, add="+")
        self.desarrollador.trace_add("write", actualizar)
        self._guia_desarrollador = guia
        self.after(10, actualizar)

    def _crear_barra_ejecucion(self):
        barra = tk.Frame(self, background=C["app"])
        barra.pack(side="top", fill="x", padx=16, pady=(12, 0))
        tk.Label(barra, text="Analizar", font=self.fuente_semi, background=C["app"],
                 foreground=C["suave"]).pack(side="left", padx=(2, 10))
        for fase in (na.FASE_LEXICO, na.FASE_SINTACTICO, na.FASE_SEMANTICO):
            f = FASE[fase]
            p = paleta((f["tinte"], f["texto"], None), hover=(f["hover"], f["texto"], None))
            atajo = {"lex": "F6", "sin": "F7", "sem": "F8"}[f["clave"]]
            b = self._pildora(barra, f["nombre"], C["app"], p, lambda c=f["clave"]: self.ejecutar({c}),
                              punto=f["solido"], padx=16, pady=7)
            b.pack(side="left", padx=3)
            Tooltip(b, f"Ejecutar solo el análisis {f['nombre'].lower()} ({atajo})")
        tk.Frame(barra, background=C["borde"], width=1, height=int(24 * self.escala)).pack(side="left", padx=10)
        primario = paleta((C["acento"], "#ffffff", None), hover=(C["acento_hover"], "#ffffff", None))
        b = self._pildora(barra, "▸  Análisis completo", C["app"], primario,
                          lambda: self.ejecutar({"lex", "sin", "sem"}), padx=18, pady=7)
        b.pack(side="left", padx=3)
        Tooltip(b, "Ejecuta las tres fases (F5)")
        tk.Label(barra, text="F5 completo · F6 / F7 / F8 por fase", font=self.fuente_pequena,
                 background=C["app"], foreground=C["tenue"]).pack(side="right")

    def _crear_cuerpo(self):
        contenedor = tk.Frame(self, background=C["app"])
        contenedor.pack(side="top", fill="both", expand=True, padx=16, pady=(10, 0))
        self.divisor_vertical = ttk.PanedWindow(contenedor, orient="vertical")
        self.divisor_vertical.pack(fill="both", expand=True)
        self.divisor_horizontal = ttk.PanedWindow(self.divisor_vertical, orient="horizontal")
        self.divisor_vertical.add(self.divisor_horizontal, weight=3)

        # --- tarjeta del editor ---
        t_editor = tarjeta(self.divisor_horizontal)
        cab = tk.Frame(t_editor, background=C["superficie"])
        cab.pack(side="top", fill="x", padx=14, pady=(10, 8))
        self.icono_archivo = tk.Label(cab, text="◧", font=self.fuente_semi, background=C["superficie"],
                                      foreground=C["acento"])
        self.icono_archivo.pack(side="left", padx=(0, 6))
        self.etiqueta_archivo = tk.Label(cab, text="", font=self.fuente_semi, background=C["superficie"],
                                         foreground=C["texto"])
        self.etiqueta_archivo.pack(side="left")
        self.etiqueta_sin_guardar = tk.Label(cab, text="", font=self.fuente_pequena,
                                             background=C["superficie"], foreground=C["aviso"])
        self.etiqueta_sin_guardar.pack(side="left", padx=(8, 0))
        self.etiqueta_ruta = tk.Label(cab, text="", font=self.fuente_pequena, background=C["superficie"],
                                      foreground=C["suave"])
        self.etiqueta_ruta.pack(side="right")
        tk.Frame(t_editor, background=C["borde_suave"], height=1).pack(side="top", fill="x")
        self.editor = EditorCodigo(t_editor, self.fuente_codigo, self.escala,
                                   al_cambiar=self._codigo_cambiado, al_mover_cursor=self._cursor_movido)
        self.editor.pack(fill="both", expand=True)
        self.divisor_horizontal.add(t_editor, weight=1)

        # --- tarjeta de resultados ---
        t_result = tarjeta(self.divisor_horizontal)
        self.pestanas = PestanasPildora(t_result, C["superficie"], self.fuente_semi, self.escala)
        self.pestanas.pack(fill="both", expand=True)
        self.divisor_horizontal.add(t_result, weight=1)
        cuerpo = self.pestanas.cuerpo

        self.tabla_tokens = self._crear_tabla(
            cuerpo, [("#", 50, "e"), ("Línea", 60, "e"), ("Columna", 75, "e"),
                     ("Token", 170, "w"), ("Lexema", 260, "w")])
        self.pestanas.add(self.tabla_tokens.master, text="Tokens")
        self.tabla_tokens.bind("<<TreeviewSelect>>", self._token_seleccionado)

        marco_arbol = tk.Frame(cuerpo, background=C["superficie"])
        botones_arbol = tk.Frame(marco_arbol, background=C["superficie"])
        botones_arbol.pack(side="top", fill="x", padx=10, pady=(8, 4))
        mini = paleta((None, C["suave"], C["borde"]), hover=(C["hover"], C["texto"], C["borde"]))
        for texto, abrir in (("Expandir todo", True), ("Contraer todo", False)):
            self._pildora(botones_arbol, texto, C["superficie"], mini,
                          lambda a=abrir: self._expandir_arbol(a), fuente=self.fuente_pequena,
                          padx=10, pady=3).pack(side="left", padx=(0, 6))
        tk.Label(botones_arbol, text="Clic en un nodo para ubicarlo en el código", font=self.fuente_pequena,
                 background=C["superficie"], foreground=C["tenue"]).pack(side="right")
        self.arbol = self._crear_tabla(marco_arbol, [("Línea", 80, "e")], arbol=True)
        self.arbol.master.pack(fill="both", expand=True)
        self.arbol.bind("<<TreeviewSelect>>", self._nodo_seleccionado)
        self.arbol.tag_configure("sentencia", font=self.fuente_semi)
        self.arbol.tag_configure("aviso", foreground=C["error"])
        self.pestanas.add(marco_arbol, text="Árbol sintáctico")

        self.tabla_simbolos = self._crear_tabla(
            cuerpo, [("Nombre", 150, "w"), ("Categoría", 120, "w"), ("Tipo", 170, "w"),
                     ("Mutable", 75, "center"), ("Línea", 60, "e"), ("Ámbito", 200, "w")])
        self.pestanas.add(self.tabla_simbolos.master, text="Tabla de símbolos")
        self.tabla_simbolos.bind("<<TreeviewSelect>>", self._simbolo_seleccionado)
        for categoria, color in (("función", "#4a6fbf"), ("método", "#4a6fbf"), ("struct", "#2f8585"),
                                 ("constante", "#8763c4")):
            self.tabla_simbolos.tag_configure(categoria, foreground=color)

        marco_log = tk.Frame(cuerpo, background=C["superficie"])
        self.texto_log = tk.Text(marco_log, wrap="none", font=self.fuente_tabla_mono, state="disabled",
                                 background=C["superficie"], foreground=C["texto"], borderwidth=0,
                                 highlightthickness=0, padx=14, pady=10, spacing1=1, spacing3=1)
        vsb = ttk.Scrollbar(marco_log, orient="vertical", command=self.texto_log.yview)
        hsb = ttk.Scrollbar(marco_log, orient="horizontal", command=self.texto_log.xview)
        self.texto_log.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.texto_log.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        marco_log.rowconfigure(0, weight=1)
        marco_log.columnconfigure(0, weight=1)
        self.texto_log.tag_configure("titulo", font=self.fuente_semi, foreground=C["acento_texto"],
                                     background=C["acento_tinte"], spacing1=6, spacing3=6)
        self.texto_log.tag_configure("error", foreground=C["error"])
        self.texto_log.tag_configure("suave", foreground=C["suave"])
        self.pestanas.add(marco_log, text="Log")
        self.pestanas.select(0)

        # --- tarjeta de errores (ancho completo) ---
        t_err = tarjeta(self.divisor_vertical)
        cab = tk.Frame(t_err, background=C["superficie"])
        cab.pack(side="top", fill="x", padx=14, pady=(10, 8))
        tk.Label(cab, text="Errores", font=self.fuente_titulo, background=C["superficie"],
                 foreground=C["texto"]).pack(side="left")
        self.insignia_errores = self._pildora(cab, "—", C["superficie"],
                                              paleta((C["hover"], C["suave"], None)),
                                              fuente=self.fuente_semi_pequena, padx=10, pady=2)
        self.insignia_errores.pack(side="left", padx=10)

        filtros = tk.Frame(cab, background=C["superficie"])
        filtros.pack(side="right")
        tk.Label(filtros, text="Mostrar", font=self.fuente_pequena, background=C["superficie"],
                 foreground=C["suave"]).pack(side="left", padx=(0, 8))
        self.botones_filtro = {}
        chip_normal = (C["superficie"], C["texto"], C["borde"])
        chip_hover = (C["hover"], C["texto"], C["borde"])
        chip_desh = (C["superficie"], C["tenue"], C["borde_suave"])
        for valor in ("TODOS", na.FASE_LEXICO, na.FASE_SINTACTICO, na.FASE_SEMANTICO):
            if valor == "TODOS":
                texto, punto = "Todos", None
                sel = (C["acento_tinte"], C["acento_texto"], C["acento_tinte"])
            else:
                texto, punto = FASE[valor]["nombre"], FASE[valor]["solido"]
                sel = (FASE[valor]["tinte"], FASE[valor]["texto"], FASE[valor]["tinte"])
            b = self._pildora(filtros, texto, C["superficie"],
                              paleta(chip_normal, hover=chip_hover, seleccionado=sel, deshabilitado=chip_desh),
                              lambda v=valor: self._elegir_filtro(v), fuente=self.fuente_ui,
                              punto=punto, padx=12, pady=4)
            b.pack(side="left", padx=2)
            self.botones_filtro[valor] = (b, texto)

        # Aviso (solo visible cuando hay algo que decir)
        self.etiqueta_aviso = tk.Label(t_err, text="", font=self.fuente_ui, background=C["aviso_tinte"],
                                       foreground=C["aviso"], anchor="w", justify="left", padx=12, pady=6)
        self.etiqueta_aviso.bind("<Configure>", lambda e: self.etiqueta_aviso.configure(
            wraplength=max(200, e.width - 24)))
        self._cabecera_errores = cab
        self._separador_errores = tk.Frame(t_err, background=C["borde_suave"], height=1)
        self._separador_errores.pack(side="top", fill="x")

        self.tabla_errores = self._crear_tabla(
            t_err, [("Fase", 120, "w"), ("Línea", 60, "e"), ("Columna", 75, "e"), ("Mensaje", 900, "w")])
        self.tabla_errores.master.pack(side="top", fill="both", expand=True)
        for fase, f in FASE.items():
            self.tabla_errores.tag_configure(fase, background=f["fila"], foreground=C["texto"])
        self.tabla_errores.bind("<<TreeviewSelect>>", self._error_seleccionado)
        self.tabla_errores.bind("<Double-1>", lambda e: self._error_seleccionado(foco=True))
        self.tabla_errores.bind("<Control-c>", self._copiar_errores)
        menu = tk.Menu(self, tearoff=0, background=C["superficie"], foreground=C["texto"],
                       activebackground=C["acento_tinte"], activeforeground=C["acento_texto"],
                       relief="flat", font=self.fuente_ui)
        menu.add_command(label="Copiar mensaje(s)", command=self._copiar_errores)
        menu.add_command(label="Copiar todos los errores", command=lambda: self._copiar_errores(todos=True))
        self.tabla_errores.bind("<Button-3>", lambda e: (self.tabla_errores.selection_set(
            self.tabla_errores.identify_row(e.y)) if self.tabla_errores.identify_row(e.y) else None,
            menu.tk_popup(e.x_root, e.y_root)))
        self.divisor_vertical.add(t_err, weight=1)

    def _crear_tabla(self, padre, columnas, arbol=False):
        columnas = [(n, int(a * self.escala), al) for n, a, al in columnas]
        marco = tk.Frame(padre, background=C["superficie"])
        ids = [c[0] for c in columnas]
        tabla = ttk.Treeview(marco, columns=ids, show="tree headings" if arbol else "headings",
                             selectmode="extended" if not arbol else "browse")
        if arbol:
            tabla.heading("#0", text="NODO", anchor="w")
            tabla.column("#0", width=int(420 * self.escala), stretch=True)
        for nombre, ancho, alineacion in columnas:
            tabla.heading(nombre, text=nombre.upper(), anchor=alineacion)
            tabla.column(nombre, width=ancho, anchor=alineacion,
                         stretch=(nombre in ("Lexema", "Mensaje", "Ámbito", "Tipo")))
        tabla.tag_configure("par", background="#fafbfd")
        vsb = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        hsb = ttk.Scrollbar(marco, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tabla.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=(2, 0))
        vsb.grid(row=0, column=1, sticky="ns", padx=(0, 2))
        hsb.grid(row=1, column=0, sticky="ew", padx=(6, 0), pady=(0, 2))
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)
        return tabla

    def _crear_barra_estado(self):
        barra = tk.Frame(self, background=C["app"])
        barra.pack(side="bottom", fill="x", padx=16, pady=(8, 10))
        self.estado = {}
        for fase in (na.FASE_LEXICO, na.FASE_SINTACTICO, na.FASE_SEMANTICO):
            f = FASE[fase]
            p = paleta((f["tinte"], f["texto"], None))
            pil = self._pildora(barra, f["nombre"], C["app"], p, fuente=self.fuente_semi_pequena,
                                punto=f["solido"], padx=11, pady=4)
            pil.pack(side="left", padx=(0, 6))
            self.estado[f["clave"]] = pil
        self.estado_log = tk.Label(barra, font=self.fuente_pequena, background=C["app"], foreground=C["suave"])
        self.estado_log.pack(side="left", padx=(10, 16))
        self.estado_cursor = tk.Label(barra, font=self.fuente_pequena, background=C["app"],
                                      foreground=C["suave"])
        self.estado_cursor.pack(side="right", padx=(16, 0))
        self.estado_mensaje = tk.Label(barra, font=self.fuente_pequena, background=C["app"],
                                       foreground=C["error"], anchor="w")
        self.estado_mensaje.pack(side="left", fill="x", expand=True)

    def _poner_estado(self, clave, texto, ejecutado=True):
        pil = self.estado[clave]
        f = FASE[FASE_POR_CLAVE[clave]]
        pil.set_texto(texto)
        pil.set_estado("normal" if ejecutado else "disabled")
        pil.set_paleta(paleta((f["tinte"], f["texto"], None),
                              deshabilitado=(C["hover"], C["suave"], None)))

    def _atajos(self):
        self.bind_all("<Control-o>", lambda e: (self.abrir_archivo(), "break")[1])
        self.bind_all("<Control-s>", lambda e: (self.guardar(), "break")[1])
        self.bind_all("<Control-S>", lambda e: (self.guardar(como=True), "break")[1])
        self.bind_all("<F5>", lambda e: self.ejecutar({"lex", "sin", "sem"}))
        self.bind_all("<F6>", lambda e: self.ejecutar({"lex"}))
        self.bind_all("<F7>", lambda e: self.ejecutar({"sin"}))
        self.bind_all("<F8>", lambda e: self.ejecutar({"sem"}))
        self.bind_all("<Control-plus>", lambda e: self._zoom(1))
        self.bind_all("<Control-equal>", lambda e: self._zoom(1))
        self.bind_all("<Control-minus>", lambda e: self._zoom(-1))
        self.editor.texto.bind("<Control-MouseWheel>", lambda e: (self._zoom(1 if e.delta > 0 else -1), "break")[1])
        # El widget Text trae atajos propios (Ctrl+O inserta una línea): se reemplazan aquí.
        self.editor.texto.bind("<Control-o>", lambda e: (self.abrir_archivo(), "break")[1])
        self.editor.texto.bind("<Control-s>", lambda e: (self.guardar(), "break")[1])
        self.editor.texto.bind("<Control-S>", lambda e: (self.guardar(como=True), "break")[1])

    def _posicionar_divisores(self):
        self.update_idletasks()
        try:
            alto = self.divisor_vertical.winfo_height()
            ancho = self.divisor_horizontal.winfo_width()
            self.divisor_vertical.sashpos(0, int(alto * 0.66))
            self.divisor_horizontal.sashpos(0, int(ancho * 0.5))
        except tk.TclError:
            pass

    def _zoom(self, delta):
        tam = max(8, min(28, self.fuente_codigo.cget("size") + delta))
        self.editor.cambiar_tamano(tam)

    # ---------------- archivo ----------------
    def _actualizar_titulo_archivo(self):
        if self.ruta_archivo:
            nombre = os.path.basename(self.ruta_archivo)
            ruta = os.path.relpath(self.ruta_archivo, BASE) if self._dentro_proyecto(self.ruta_archivo) \
                else self.ruta_archivo
            self.etiqueta_ruta.configure(text=os.path.dirname(ruta).replace("\\", " / "))
        else:
            nombre = "Sin título"
            self.etiqueta_ruta.configure(text="código nuevo")
        self.etiqueta_archivo.configure(text=nombre)
        self.etiqueta_sin_guardar.configure(text="● sin guardar" if self.sucio else "")

    @staticmethod
    def _dentro_proyecto(ruta):
        try:
            return os.path.commonpath([os.path.abspath(ruta), BASE]) == BASE
        except ValueError:
            return False

    def _confirmar_descartar(self):
        if not self.sucio or not self.editor.obtener().strip():
            return True
        r = messagebox.askyesnocancel("Cambios sin guardar",
                                      "El código tiene cambios sin guardar.\n¿Desea guardarlos antes de continuar?")
        if r is None:
            return False
        if r:
            return self.guardar()
        return True

    def abrir_archivo(self, ruta=None):
        if not self._confirmar_descartar():
            return
        if ruta is None:
            ruta = filedialog.askopenfilename(
                title="Importar algoritmo Rust", initialdir=os.path.join(BASE, "algoritmos"),
                filetypes=[("Código Rust", "*.rs"), ("Todos los archivos", "*.*")])
            if not ruta:
                return
        try:
            with open(ruta, encoding="utf-8") as f:
                codigo = f.read()
        except UnicodeDecodeError:
            with open(ruta, encoding="latin-1") as f:
                codigo = f.read()
        except OSError as exc:
            messagebox.showerror("No se pudo abrir", str(exc))
            return
        self.editor.establecer(codigo)
        self.ruta_archivo = os.path.abspath(ruta)
        self.sucio = False
        self._limpiar_resultados()
        self._actualizar_titulo_archivo()
        m = re.search(r"_([A-Za-z0-9-]+)\.rs$", os.path.basename(ruta))
        if m and m.group(1) in DESARROLLADORES:
            self.desarrollador.set(m.group(1))

    def guardar(self, como=False):
        ruta = self.ruta_archivo
        if como or not ruta:
            ruta = filedialog.asksaveasfilename(
                title="Guardar algoritmo", defaultextension=".rs",
                initialdir=os.path.dirname(ruta) if ruta else os.path.join(BASE, "algoritmos"),
                initialfile=os.path.basename(ruta) if ruta else "algoritmo.rs",
                filetypes=[("Código Rust", "*.rs"), ("Todos los archivos", "*.*")])
            if not ruta:
                return False
        try:
            with open(ruta, "w", encoding="utf-8", newline="\n") as f:
                f.write(self.editor.obtener())
        except OSError as exc:
            messagebox.showerror("No se pudo guardar", str(exc))
            return False
        self.ruta_archivo = os.path.abspath(ruta)
        self.sucio = False
        self._actualizar_titulo_archivo()
        self.estado_mensaje.configure(text=f"Guardado: {os.path.basename(ruta)}", foreground=C["ok"])
        return True

    def limpiar(self):
        if self.editor.obtener().strip():
            if self.sucio:
                if not self._confirmar_descartar():
                    return
            elif not messagebox.askyesno("Limpiar", "¿Borrar todo el código y los resultados?"):
                return
        self.editor.establecer("")
        self.ruta_archivo = None
        self.sucio = False
        self._limpiar_resultados()
        self._actualizar_titulo_archivo()
        self.editor.texto.focus_set()

    def _mostrar_ejemplos(self):
        self._llenar_menu_ejemplos()
        b = self._boton_ejemplos
        self.menu_ejemplos.tk_popup(b.winfo_rootx(), b.winfo_rooty() + b.winfo_height() + 4)

    def _llenar_menu_ejemplos(self):
        m = self.menu_ejemplos
        m.delete(0, "end")
        carpeta = os.path.join(BASE, "algoritmos")
        if not os.path.isdir(carpeta):
            m.add_command(label="(no existe la carpeta algoritmos/)", state="disabled")
            return
        for sub in sorted(os.listdir(carpeta)):
            ruta_sub = os.path.join(carpeta, sub)
            if not os.path.isdir(ruta_sub):
                continue
            submenu = tk.Menu(m, tearoff=0, background=C["superficie"], foreground=C["texto"],
                              activebackground=C["acento_tinte"], activeforeground=C["acento_texto"],
                              relief="flat", font=self.fuente_ui)
            archivos = sorted(f for f in os.listdir(ruta_sub) if f.endswith(".rs"))
            for archivo in archivos:
                ruta = os.path.join(ruta_sub, archivo)
                submenu.add_command(label=archivo, command=lambda r=ruta: self.abrir_archivo(r))
            if not archivos:
                submenu.add_command(label="(vacío)", state="disabled")
            m.add_cascade(label=sub.capitalize(), menu=submenu)

    def _cerrar(self):
        if self._confirmar_descartar():
            self.destroy()

    # ---------------- eventos del editor ----------------
    def _codigo_cambiado(self):
        if not self.sucio:
            self.sucio = True
            self._actualizar_titulo_archivo()
        if self.fases_ejecutadas and not self.desactualizado:
            self.desactualizado = True
            self.estado_log.configure(text="⟳ Código modificado: vuelva a ejecutar el análisis",
                                      foreground=C["aviso"])

    def _cursor_movido(self, linea, columna):
        self.estado_cursor.configure(text=f"Ln {linea}  ·  Col {columna}")
        errores = [e for e in self._errores_filtrados() if e.linea == linea]
        if errores:
            e = errores[0]
            extra = f"  (+{len(errores) - 1} más)" if len(errores) > 1 else ""
            self.estado_mensaje.configure(text=f"{FASE[e.fase]['nombre']} · {e.mensaje}{extra}",
                                          foreground=FASE[e.fase]["texto"])
        elif self.estado_mensaje.cget("foreground") != C["ok"]:
            self.estado_mensaje.configure(text="")

    # ---------------- análisis ----------------
    def ejecutar(self, fases):
        codigo = self.editor.obtener()
        if not codigo.strip():
            messagebox.showinfo("Sin código", "Escriba o importe un algoritmo en Rust antes de analizar.")
            return
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            self._ejecutar(codigo, fases)
        finally:
            self.configure(cursor="")

    def _ejecutar(self, codigo, fases):
        self._limpiar_resultados()
        self.fases_ejecutadas = set(fases)
        self.desactualizado = False
        avisos = []
        errores = []

        lex = na.analisis_lexico(codigo) if "lex" in fases else None
        sin = na.analisis_sintactico(codigo) if fases & {"sin", "sem"} else None
        sem = na.analisis_semantico(codigo, sin) if "sem" in fases else None

        if lex:
            errores += lex.errores
            self._mostrar_tokens(lex)
            self._poner_estado("lex", f"Léxico · {len(lex.tokens)} tokens · {self._n(len(lex.errores))}")
        if sin:
            self._mostrar_arbol(sin, codigo)
        if "sin" in fases:
            errores += sin.errores
            self._poner_estado("sin", f"Sintáctico · {self._n(len(sin.errores))}")
            if "lex" not in fases and sin.errores_lexicos_previos:
                n = sin.errores_lexicos_previos
                avisos.append(f"⚠  El código también tiene {n} {'error léxico' if n == 1 else 'errores léxicos'}; "
                              "use «Análisis completo» para verlos.")
        if sem:
            errores += sem.errores
            self._mostrar_simbolos(sem)
            if not sem.ast_disponible:
                self._poner_estado("sem", "Semántico · no ejecutado (sin árbol)")
                avisos.append("✕  No se pudo construir el árbol sintáctico: el análisis semántico no se ejecutó. "
                              "Corrija primero los errores sintácticos.")
            else:
                self._poner_estado("sem", f"Semántico · {self._n(len(sem.errores))}")
                previos = sem.errores_sintacticos_previos + sem.errores_lexicos_previos
                if previos:
                    detalle = []
                    for n, singular, plural in ((sem.errores_lexicos_previos, "léxico", "léxicos"),
                                                (sem.errores_sintacticos_previos, "sintáctico", "sintácticos")):
                        if n:
                            detalle.append(f"{n} {singular if n == 1 else plural}")
                    avisos.append(f"⚠  El código tiene errores previos ({' y '.join(detalle)}): "
                                  "el análisis semántico puede estar incompleto.")

        errores.sort(key=lambda e: (e.linea if e.linea is not None else 10**9,
                                    ORDEN_FASE[e.fase], e.columna or 0))
        self.errores_actuales = errores
        for valor, (boton, texto) in self.botones_filtro.items():
            if valor == "TODOS":
                boton.set_texto(f"{texto}  {len(errores)}")
                boton.set_estado("normal")
                continue
            clave = FASE[valor]["clave"]
            n = sum(1 for e in errores if e.fase == valor)
            boton.set_texto(f"{texto}  {n}" if clave in fases else texto)
            boton.set_estado("normal" if clave in fases else "disabled")
        es_error = any(a.startswith("✕") for a in avisos)
        self._mostrar_aviso("     ".join(avisos), es_error)
        self._elegir_filtro("TODOS")

        # Vista previa de logs con los resultados recién obtenidos
        self.textos_log = {"lexico": lex, "sintactico": sin if "sin" in fases else None, "semantico": sem}
        self._actualizar_vista_log()
        self.estado_log.configure(text="Log listo para exportar", foreground=C["suave"])

        if fases == {"lex"}:
            self.pestanas.select(0)
        elif fases == {"sin"}:
            self.pestanas.select(1)
        elif fases == {"sem"}:
            self.pestanas.select(2)

    @staticmethod
    def _n(cantidad):
        return f"{cantidad} error" if cantidad == 1 else f"{cantidad} errores"

    def _limpiar_resultados(self):
        self.errores_actuales = []
        self.fases_ejecutadas = set()
        self.desactualizado = False
        self.textos_log = {}
        for tabla in (self.tabla_tokens, self.arbol, self.tabla_simbolos, self.tabla_errores):
            tabla.delete(*tabla.get_children())
        self.pestanas.tab(0, text="Tokens")
        self.pestanas.tab(2, text="Tabla de símbolos")
        self.editor.limpiar_errores()
        self._mostrar_aviso("", False)
        for valor, (boton, texto) in self.botones_filtro.items():
            boton.set_texto(texto)
            boton.set_estado("normal")
        self.filtro.set("TODOS")
        for valor, (boton, _) in self.botones_filtro.items():
            boton.set_seleccionado(valor == "TODOS")
        self._actualizar_insignia()
        for clave in ("lex", "sin", "sem"):
            self._poner_estado(clave, f"{FASE[FASE_POR_CLAVE[clave]]['nombre']} · —", ejecutado=False)
        self.estado_log.configure(text="Log sin generar", foreground=C["suave"])
        self.estado_mensaje.configure(text="")
        self._mostrar_texto_log([("\n  Ejecute un análisis para ver aquí la vista previa del log.\n", "suave")])

    def _mostrar_aviso(self, texto, es_error):
        if texto:
            self.etiqueta_aviso.configure(
                text=texto, foreground=C["error"] if es_error else C["aviso"],
                background=C["error_tinte"] if es_error else C["aviso_tinte"])
            self.etiqueta_aviso.pack(side="top", fill="x", padx=14, pady=(0, 8), after=self._cabecera_errores)
        else:
            self.etiqueta_aviso.configure(text="")
            self.etiqueta_aviso.pack_forget()

    # ---------------- presentación de resultados ----------------
    def _mostrar_tokens(self, lex):
        t = self.tabla_tokens
        self._tokens = lex.tokens
        for i, tok in enumerate(lex.tokens, start=1):
            lexema = tok.lexema.replace("\n", "⏎")
            t.insert("", "end", iid=str(i - 1), values=(i, tok.linea, tok.columna, tok.tipo, lexema),
                     tags=("par",) if i % 2 == 0 else ())
        self.pestanas.tab(0, text=f"Tokens  {len(lex.tokens)}")

    def _mostrar_simbolos(self, sem):
        t = self.tabla_simbolos
        if not sem.ast_disponible:
            t.insert("", "end", values=("—", "No disponible: no se pudo construir el árbol sintáctico",
                                        "", "", "", ""))
            return
        for i, s in enumerate(sem.simbolos):
            categoria = s.categoria.split(" ")[0]
            etiquetas = (categoria, "par") if i % 2 else (categoria,)
            t.insert("", "end", values=(s.nombre, s.categoria, s.tipo, s.mutable,
                                        s.linea if s.linea else "—", s.ambito), tags=etiquetas)
        self.pestanas.tab(2, text=f"Tabla de símbolos  {len(sem.simbolos)}")

    def _mostrar_arbol(self, sin, codigo):
        a = self.arbol
        if sin.ast is None:
            a.insert("", "end", text="No se pudo construir el árbol sintáctico (revise los errores)",
                     values=("",), tags=("aviso",))
            return
        raiz = a.insert("", "end", text="programa", values=("",), open=True, tags=("sentencia",))
        for sentencia in sin.ast[1] if isinstance(sin.ast, tuple) else []:
            self._insertar_nodo(raiz, None, sentencia, codigo, nivel=1)

    def _etiqueta_nodo(self, nodo):
        tag = nodo[0]
        nombre = na.NOMBRES_NODO.get(tag, tag)
        detalles = {
            "let": lambda: f"{'mut ' if nodo[1] else ''}{nodo[2]}",
            "const": lambda: nodo[1],
            "assign": lambda: f"'{nodo[2]}'",
            "binop": lambda: f"'{nodo[1]}'",
            "fn": lambda: nodo[1],
            "method": lambda: nodo[1],
            "call": lambda: f"{nodo[1]}()",
            "method_call": lambda: f".{nodo[2]}()",
            "assoc_call": lambda: f"{nodo[1]}::{nodo[2]}()",
            "print_macro": lambda: f"{nodo[1]}!",
            "struct": lambda: nodo[1],
            "impl": lambda: nodo[1],
            "for": lambda: nodo[1],
            "param": lambda: nodo[1],
            "field": lambda: nodo[1],
            "range": lambda: f"'{nodo[1]}'",
        }
        try:
            extra = detalles[tag]() if tag in detalles else ""
        except (IndexError, TypeError):
            extra = ""
        return f"{nombre} {extra}".strip()

    def _insertar_nodo(self, padre, campo, valor, codigo, nivel):
        a = self.arbol
        prefijo = f"{campo}: " if campo else ""
        hoja = na.resumen_hoja(valor)
        if hoja is not None:
            a.insert(padre, "end", text=prefijo + hoja, values=("",))
            return
        if isinstance(valor, list):
            if not valor:
                a.insert(padre, "end", text=f"{prefijo}(vacío)", values=("",))
                return
            nodo = a.insert(padre, "end", text=f"{campo or 'lista'} [{len(valor)}]", values=("",),
                            open=nivel <= 2)
            for elemento in valor:
                self._insertar_nodo(nodo, None, elemento, codigo, nivel + 1)
            return
        if isinstance(valor, tuple) and valor:
            # La línea se muestra en las sentencias (nodos sin campo); clic en un campo
            # sigue ubicando el código a través de su sentencia padre.
            linea = na.linea_de_nodo(valor, codigo) if campo is None else None
            es_sentencia = campo is None and nivel <= 1
            nodo = a.insert(padre, "end", text=prefijo + self._etiqueta_nodo(valor),
                            values=(f"línea {linea}" if linea else "",),
                            open=nivel <= 1, tags=("sentencia",) if es_sentencia else ())
            try:
                hijos = na.campos_de(valor)
            except Exception:
                hijos = [(None, v) for v in valor[1:]]
            for nombre_campo, hijo in hijos:
                self._insertar_nodo(nodo, nombre_campo, hijo, codigo, nivel + 1)
            return
        a.insert(padre, "end", text=prefijo + str(valor), values=("",))

    def _expandir_arbol(self, abrir):
        def recorrer(item):
            for hijo in self.arbol.get_children(item):
                self.arbol.item(hijo, open=abrir)
                recorrer(hijo)
        recorrer("")
        if not abrir:
            for raiz in self.arbol.get_children(""):
                self.arbol.item(raiz, open=True)

    def _errores_filtrados(self):
        f = self.filtro.get()
        return [e for e in self.errores_actuales if f == "TODOS" or e.fase == f]

    def _elegir_filtro(self, valor):
        self.filtro.set(valor)
        for v, (boton, _) in self.botones_filtro.items():
            boton.set_seleccionado(v == valor)
        self._aplicar_filtro()

    def _aplicar_filtro(self):
        t = self.tabla_errores
        t.delete(*t.get_children())
        visibles = self._errores_filtrados()
        for i, e in enumerate(visibles):
            t.insert("", "end", iid=str(i),
                     values=(f"●  {FASE[e.fase]['nombre']}", e.linea or "—", e.columna or "—", e.mensaje),
                     tags=(e.fase,))
        self._errores_visibles = visibles
        self.editor.marcar_errores(visibles)
        self._actualizar_insignia()

    def _actualizar_insignia(self):
        total = len(self.errores_actuales)
        visibles = len(self._errores_visibles) if self.fases_ejecutadas else 0
        if not self.fases_ejecutadas:
            texto, p = "sin analizar", paleta((C["hover"], C["suave"], None))
        elif total == 0:
            texto, p = "✓  sin errores", paleta((C["ok_tinte"], C["ok"], None))
        elif visibles == total:
            texto, p = str(total), paleta((C["error_tinte"], C["error"], None))
        else:
            texto, p = f"{visibles} de {total}", paleta((C["error_tinte"], C["error"], None))
        self.insignia_errores.set_paleta(p)
        self.insignia_errores.set_texto(texto)

    # ---------------- selección en tablas -> editor ----------------
    def _error_seleccionado(self, _=None, foco=False):
        sel = self.tabla_errores.selection()
        if not sel:
            return
        e = self._errores_visibles[int(sel[0])]
        if e.linea:
            self.editor.ir_a(e.linea, e.columna, foco=foco)
        self.estado_mensaje.configure(text=f"{FASE[e.fase]['nombre']} · {e.mensaje}",
                                      foreground=FASE[e.fase]["texto"])

    def _token_seleccionado(self, _=None):
        sel = self.tabla_tokens.selection()
        if sel:
            tok = self._tokens[int(sel[0])]
            self.editor.destacar_rango(tok.inicio, tok.fin)

    def _nodo_seleccionado(self, _=None):
        sel = self.arbol.selection()
        if not sel:
            return
        item = sel[0]
        valor = self.arbol.set(item, "Línea")
        while not valor and self.arbol.parent(item):   # hojas: usar la línea de la sentencia padre
            item = self.arbol.parent(item)
            valor = self.arbol.set(item, "Línea")
        m = re.search(r"\d+", str(valor))
        if m:
            linea = int(m.group(0))
            self.editor.ir_a(linea)
            self.editor.texto.tag_add("seleccion_destacada", f"{linea}.0", f"{linea}.0 lineend")

    def _simbolo_seleccionado(self, _=None):
        sel = self.tabla_simbolos.selection()
        if not sel:
            return
        nombre, _, _, _, linea, _ = self.tabla_simbolos.item(sel[0], "values")
        if str(linea).isdigit():
            linea = int(linea)
            texto_linea = self.editor.texto.get(f"{linea}.0", f"{linea}.0 lineend")
            m = re.search(r"\b" + re.escape(nombre) + r"\b", texto_linea)
            if m:
                self.editor.ir_a(linea, m.start() + 1, largo=len(nombre))
            else:
                self.editor.ir_a(linea)

    def _copiar_errores(self, _=None, todos=False):
        if todos:
            errores = self._errores_visibles
        else:
            errores = [self._errores_visibles[int(i)] for i in self.tabla_errores.selection()]
        if errores:
            self.clipboard_clear()
            self.clipboard_append("\n".join(e.original for e in errores))
        return "break"

    # ---------------- logs ----------------
    def _nombre_archivo_analizado(self):
        if self.ruta_archivo:
            if self._dentro_proyecto(self.ruta_archivo):
                return os.path.relpath(self.ruta_archivo, BASE).replace("\\", "/")
            return self.ruta_archivo
        return "(código ingresado en la interfaz)"

    def _usuario_log(self):
        usuario = self.desarrollador.get().strip()
        return "" if usuario == getattr(self, "_guia_desarrollador", None) else usuario

    def _actualizar_vista_log(self):
        if not self.textos_log:
            return
        codigo = self.editor.obtener()
        usuario = self._usuario_log() or "<desarrollador>"
        ahora = datetime.now()
        partes = []
        titulos = {"lexico": "Log léxico", "sintactico": "Log sintáctico", "semantico": "Log semántico"}
        for tipo in na.TIPOS_LOG:
            resultado = self.textos_log.get(tipo)
            if resultado is None:
                continue
            contenido = na.contenido_log(tipo, codigo, self._nombre_archivo_analizado(), usuario,
                                         ahora, resultado=resultado)
            partes.append((f"  {titulos[tipo]}  ·  {na.nombre_log(tipo, usuario, ahora)}  \n", "titulo"))
            partes.append(("\n", None))
            for linea in contenido.splitlines():
                partes.append((linea + "\n", "error" if linea.startswith("[ERROR") else None))
            partes.append(("\n", None))
        self._mostrar_texto_log(partes)

    def _mostrar_texto_log(self, partes):
        t = self.texto_log
        t.configure(state="normal")
        t.delete("1.0", "end")
        for texto, etiqueta in partes:
            t.insert("end", texto, (etiqueta,) if etiqueta else ())
        t.configure(state="disabled")

    def descargar_logs(self):
        codigo = self.editor.obtener()
        if not codigo.strip():
            messagebox.showinfo("Sin código", "No hay código para generar el log.")
            return
        usuario = self._usuario_log()
        if not usuario:
            messagebox.showwarning("Falta el desarrollador",
                                   "Seleccione o escriba el usuario de GitHub del desarrollador;\n"
                                   "se usa en el nombre del log (igual que en main.py).")
            return
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", usuario):
            messagebox.showwarning("Usuario no válido", "El usuario solo puede tener letras, números, '-', '_' o '.'.")
            return
        eleccion = {"Todos": na.TIPOS_LOG, "Léxico": ("lexico",), "Sintáctico": ("sintactico",),
                    "Semántico": ("semantico",)}[self.tipo_log.get()]
        archivo = self._nombre_archivo_analizado()
        ahora = datetime.now()
        carpeta_logs = os.path.join(BASE, "logs")

        if len(eleccion) == 1:
            tipo = eleccion[0]
            os.makedirs(os.path.join(carpeta_logs, tipo), exist_ok=True)
            ruta = filedialog.asksaveasfilename(
                title=f"Guardar log {tipo}", defaultextension=".txt",
                initialdir=os.path.join(carpeta_logs, tipo), initialfile=na.nombre_log(tipo, usuario, ahora),
                filetypes=[("Texto", "*.txt"), ("Todos los archivos", "*.*")])
            if not ruta:
                return
            destinos = [(tipo, ruta)]
        else:
            os.makedirs(carpeta_logs, exist_ok=True)
            carpeta = filedialog.askdirectory(
                title="Carpeta donde guardar los logs (se crean las subcarpetas lexico/, sintactico/ y semantico/)",
                initialdir=carpeta_logs, mustexist=False)
            if not carpeta:
                return
            destinos = [(t, os.path.join(carpeta, t, na.nombre_log(t, usuario, ahora))) for t in na.TIPOS_LOG]

        guardados = []
        try:
            for tipo, ruta in destinos:
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(na.contenido_log(tipo, codigo, archivo, usuario, ahora))
                guardados.append(ruta)
        except OSError as exc:
            messagebox.showerror("No se pudo guardar el log", str(exc))
            return
        mostrar = [os.path.relpath(r, BASE) if self._dentro_proyecto(r) else r for r in guardados]
        self.estado_log.configure(text=f"✓ {len(guardados)} log(s) exportado(s)", foreground=C["ok"])
        messagebox.showinfo("Logs generados", "Se guardaron los siguientes logs:\n\n" + "\n".join(mostrar))

    # ---------------- errores inesperados ----------------
    def report_callback_exception(self, exc, val, tb):
        detalle = "".join(traceback.format_exception(exc, val, tb))
        messagebox.showerror("Error inesperado", f"{val}\n\n{detalle[-1500:]}")


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    app = AplicacionAnalizador()
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        app.abrir_archivo(sys.argv[1])
    # Al abrir desde el .bat la ventana puede quedar detrás de otras: traerla al frente.
    app.lift()
    app.attributes("-topmost", True)
    app.after(400, lambda: app.attributes("-topmost", False))
    app.focus_force()
    app.mainloop()


if __name__ == "__main__":
    main()
