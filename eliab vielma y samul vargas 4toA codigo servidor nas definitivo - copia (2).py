import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class SistemaFeYAlegria:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión - Fe y Alegría")
        self.root.geometry("1100x700")
        self.root.configure(bg="#F5F5F5")

        self.NARANJA = "#FF6600"
        self.GRIS_OSCURO = "#2C3E50"
        self.BLANCO = "#FFFFFF"

        self.conexion = sqlite3.connect("gestion_feya.db")
        self.cursor = self.conexion.cursor()
        self.crear_tablas()
        
        self.id_sel = None 
        self.configurar_estilos()
        self.login_ui()

    def crear_tablas(self):
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS areas (id INTEGER PRIMARY KEY, nombre TEXT);
            CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT, clave TEXT);
            CREATE TABLE IF NOT EXISTS inventario (
                id INTEGER PRIMARY KEY, producto TEXT, cantidad INTEGER, area_id INTEGER,
                FOREIGN KEY(area_id) REFERENCES areas(id) ON DELETE CASCADE
            );
        ''')
        self.cursor.execute("INSERT OR IGNORE INTO usuarios VALUES (1, 'admin', '1234')")
        self.conexion.commit()

    def configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=30, font=("Arial", 10))
        style.configure("Treeview.Heading", background=self.GRIS_OSCURO, foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', self.NARANJA)])

    def login_ui(self):
        self.limpiar_pantalla()
        self.root.configure(bg=self.GRIS_OSCURO)
        frame = tk.Frame(self.root, bg=self.BLANCO, padx=40, pady=40, highlightbackground=self.NARANJA, highlightthickness=2)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(frame, text="FE Y ALEGRÍA", font=("Arial", 22, "bold"), fg=self.NARANJA, bg=self.BLANCO).pack()
        self.ent_u = ttk.Entry(frame, width=30); self.ent_u.pack(pady=5); self.ent_u.insert(0, "admin")
        self.ent_p = ttk.Entry(frame, show="*", width=30); self.ent_p.pack(pady=5); self.ent_p.insert(0, "1234")
        tk.Button(frame, text="ENTRAR", bg=self.NARANJA, fg="white", font=("Arial", 10, "bold"), 
                  bd=0, width=25, pady=10, command=self.validar).pack(pady=20)

    def validar(self):
        user = self.ent_u.get()
        pas = self.ent_p.get()
        self.cursor.execute("SELECT * FROM usuarios WHERE nombre=? AND clave=?", (user, pas))
        if self.cursor.fetchone():
            self.main_ui()
        else:
            messagebox.showerror("Error", "Usuario o clave incorrectos")

    def main_ui(self):
        self.limpiar_pantalla()
        header = tk.Frame(self.root, bg=self.NARANJA, height=60)
        header.pack(side="top", fill="x")
        tk.Label(header, text="FE Y ALEGRÍA - PANEL PRINCIPAL", font=("Arial", 12, "bold"), fg="white", bg=self.NARANJA, padx=20).pack(side="left")
        
        nav = tk.Frame(self.root, bg=self.GRIS_OSCURO)
        nav.pack(side="top", fill="x")
        menu = [("INVENTARIO", self.ventana_inventario), ("ÁREAS", self.ventana_areas), ("USUARIOS", self.ventana_usuarios), ("SALIR", self.root.quit)]
        for t, c in menu:
            tk.Button(nav, text=t, command=c, bg=self.GRIS_OSCURO, fg="white", bd=0, padx=20, pady=12, activebackground=self.NARANJA).pack(side="left")

        self.body = tk.Frame(self.root, bg="#F5F5F5", padx=30, pady=20)
        self.body.pack(expand=True, fill="both")
        self.ventana_inventario()

    # --- CRUD USUARIOS CORREGIDO ---
    def ventana_usuarios(self):
        self.preparar_body("Gestión de Usuarios")
        f = tk.Frame(self.body, bg="#F5F5F5")
        f.pack(fill="x", pady=10)

        tk.Label(f, text="Usuario:", bg="#F5F5F5").grid(row=0, column=0)
        ent_u = ttk.Entry(f); ent_u.grid(row=0, column=1, padx=5)
        tk.Label(f, text="Clave:", bg="#F5F5F5").grid(row=0, column=2)
        ent_p = ttk.Entry(f); ent_p.grid(row=0, column=3, padx=5)

        tv = self.crear_tv(("ID", "Usuario", "Clave"))

        def refresh():
            tv.delete(*tv.get_children())
            for r in self.cursor.execute("SELECT * FROM usuarios"):
                tv.insert("", "end", values=r)
            ent_u.delete(0, tk.END); ent_p.delete(0, tk.END)
            self.id_sel = None

        def guardar():
            u, p = ent_u.get(), ent_p.get()
            if not u or not p: 
                messagebox.showwarning("Atención", "Llene todos los campos")
                return
            if self.id_sel:
                self.cursor.execute("UPDATE usuarios SET nombre=?, clave=? WHERE id=?", (u, p, self.id_sel))
            else:
                self.cursor.execute("INSERT INTO usuarios (nombre, clave) VALUES (?,?)", (u, p))
            self.conexion.commit()
            refresh()

        def al_clic(e):
            item_id = tv.focus()
            if item_id:
                valores = tv.item(item_id)['values']
                self.id_sel = valores[0]
                ent_u.delete(0, tk.END); ent_u.insert(0, valores[1])
                ent_p.delete(0, tk.END); ent_p.insert(0, valores[2])

        tv.bind("<<TreeviewSelect>>", al_clic)
        self.crear_botones(f, guardar, lambda: self.borrar("usuarios", refresh, True), refresh)

    # --- VENTANA INVENTARIO ---
    def ventana_inventario(self):
        self.preparar_body("Gestión de Inventario")
        f = tk.Frame(self.body, bg="#F5F5F5")
        f.pack(fill="x", pady=10)

        ent_prod = ttk.Entry(f); ent_prod.grid(row=0, column=1, padx=5)
        ent_cant = ttk.Entry(f, width=10); ent_cant.grid(row=0, column=3, padx=5)
        
        self.cursor.execute("SELECT id, nombre FROM areas")
        areas_dict = {nom: idx for idx, nom in self.cursor.fetchall()}
        cb_area = ttk.Combobox(f, values=list(areas_dict.keys()), state="readonly")
        cb_area.grid(row=0, column=5, padx=5)

        tk.Label(f, text="Producto:", bg="#F5F5F5").grid(row=0, column=0)
        tk.Label(f, text="Cant:", bg="#F5F5F5").grid(row=0, column=2)
        tk.Label(f, text="Área:", bg="#F5F5F5").grid(row=0, column=4)

        tv = self.crear_tv(("ID", "Producto", "Cantidad", "Área"))

        def refresh():
            tv.delete(*tv.get_children())
            query = "SELECT i.id, i.producto, i.cantidad, a.nombre FROM inventario i LEFT JOIN areas a ON i.area_id = a.id"
            for r in self.cursor.execute(query): tv.insert("", "end", values=r)
            ent_prod.delete(0, tk.END); ent_cant.delete(0, tk.END); self.id_sel = None

        def guardar():
            p, c, a = ent_prod.get(), ent_cant.get(), cb_area.get()
            if not p or not a: return
            id_area = areas_dict[a]
            if self.id_sel:
                self.cursor.execute("UPDATE inventario SET producto=?, cantidad=?, area_id=? WHERE id=?", (p, c, id_area, self.id_sel))
            else:
                self.cursor.execute("INSERT INTO inventario (producto, cantidad, area_id) VALUES (?,?,?)", (p, c, id_area))
            self.conexion.commit(); refresh()

        def al_clic(e):
            item_id = tv.focus()
            if item_id:
                v = tv.item(item_id)['values']
                self.id_sel = v[0]
                ent_prod.delete(0, tk.END); ent_prod.insert(0, v[1])
                ent_cant.delete(0, tk.END); ent_cant.insert(0, v[2])
                cb_area.set(v[3])

        tv.bind("<<TreeviewSelect>>", al_clic)
        self.crear_botones(f, guardar, lambda: self.borrar("inventario", refresh), refresh)

    # --- VENTANA ÁREAS ---
    def ventana_areas(self):
        self.preparar_body("Gestión de Áreas")
        f = tk.Frame(self.body, bg="#F5F5F5")
        f.pack(fill="x", pady=10)
        ent_nom = ttk.Entry(f, width=40); ent_nom.grid(row=0, column=1, padx=10)
        tk.Label(f, text="Nombre del Área:", bg="#F5F5F5").grid(row=0, column=0)
        tv = self.crear_tv(("ID", "Nombre"))

        def refresh():
            tv.delete(*tv.get_children())
            for r in self.cursor.execute("SELECT * FROM areas"): tv.insert("", "end", values=r)
            ent_nom.delete(0, tk.END); self.id_sel = None

        def guardar():
            n = ent_nom.get()
            if not n: return
            if self.id_sel:
                self.cursor.execute("UPDATE areas SET nombre=? WHERE id=?", (n, self.id_sel))
            else:
                self.cursor.execute("INSERT INTO areas (nombre) VALUES (?)", (n,))
            self.conexion.commit(); refresh()

        tv.bind("<<TreeviewSelect>>", lambda e: [self.set_id(tv), ent_nom.delete(0,tk.END), ent_nom.insert(0, tv.item(tv.focus())['values'][1])])
        self.crear_botones(f, guardar, lambda: self.borrar("areas", refresh), refresh)

    # --- UTILIDADES ---
    def set_id(self, tv):
        if tv.focus(): self.id_sel = tv.item(tv.focus())['values'][0]

    def preparar_body(self, t):
        for w in self.body.winfo_children(): w.destroy()
        self.id_sel = None
        tk.Label(self.body, text=t, font=("Arial", 16, "bold"), bg="#F5F5F5", fg=self.GRIS_OSCURO).pack(anchor="w")

    def crear_tv(self, cols):
        tv = ttk.Treeview(self.body, columns=cols, show="headings")
        for c in cols: tv.heading(c, text=c)
        tv.pack(expand=True, fill="both", pady=10)
        return tv

    def crear_botones(self, f, fg, fe, fr):
        tk.Button(f, text="GUARDAR", bg=self.NARANJA, fg="white", bd=0, padx=15, pady=5, command=fg).grid(row=0, column=6, padx=5)
        tk.Button(f, text="ELIMINAR", bg="#E74C3C", fg="white", bd=0, padx=15, pady=5, command=fe).grid(row=0, column=7, padx=5)
        fr()

    def borrar(self, tabla, cb, es_u=False):
        if not self.id_sel: return
        if es_u and self.id_sel == 1: 
            messagebox.showwarning("Prohibido", "No puedes eliminar al administrador base")
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar registro?"):
            self.cursor.execute(f"DELETE FROM {tabla} WHERE id=?", (self.id_sel,))
            self.conexion.commit(); cb()

    def limpiar_pantalla(self):
        for w in self.root.winfo_children(): w.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaFeYAlegria(root)
    root.mainloop()
