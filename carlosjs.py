import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class SistemaGestion:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión Integrado - TK/SQL")
        self.root.geometry("1000x600")
        
        self.conexion = sqlite3.connect("gestion.db")
        self.cursor = self.conexion.cursor()
        self.crear_tablas()
        
        self.login_ui()

    def crear_tablas(self):
        # Relación: El inventario depende de un Área (FOREIGN KEY)
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT, clave TEXT);
            CREATE TABLE IF NOT EXISTS areas (id INTEGER PRIMARY KEY, nombre TEXT);
            CREATE TABLE IF NOT EXISTS inventario (
                id INTEGER PRIMARY KEY, 
                producto TEXT, 
                cantidad INTEGER, 
                area_id INTEGER,
                FOREIGN KEY(area_id) REFERENCES areas(id) ON DELETE CASCADE
            );
        ''')
        # Usuario inicial
        self.cursor.execute("INSERT OR IGNORE INTO usuarios VALUES (1, 'admin', '1234')")
        self.conexion.commit()

    # --- INTERFAZ DE LOGIN ---
    def login_ui(self):
        self.limpiar_pantalla()
        frame = ttk.Frame(self.root, padding="20")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(frame, text="INICIO DE SESIÓN", font=('Arial', 18, 'bold')).grid(row=0, column=0, columnspan=2, pady=20)
        ttk.Label(frame, text="Usuario:").grid(row=1, column=0, sticky="w")
        self.ent_user = ttk.Entry(frame)
        self.ent_user.grid(row=1, column=1, pady=5)
        
        ttk.Label(frame, text="Clave:").grid(row=2, column=0, sticky="w")
        self.ent_pass = ttk.Entry(frame, show="*")
        self.ent_pass.grid(row=2, column=1, pady=5)
        
        ttk.Button(frame, text="Entrar", command=self.validar_login).grid(row=3, column=0, columnspan=2, pady=20)

    def validar_login(self):
        u, p = self.ent_user.get(), self.ent_pass.get()
        self.cursor.execute("SELECT * FROM usuarios WHERE nombre=? AND clave=?", (u, p))
        if self.cursor.fetchone():
            self.dashboard_ui()
        else:
            messagebox.showerror("Error", "Acceso denegado")

    # --- PANEL PRINCIPAL (DASHBOARD) ---
    def dashboard_ui(self):
        self.limpiar_pantalla()
        
        # Menú Superior
        menu_bar = tk.Frame(self.root, bg="#2c3e50", height=50)
        menu_bar.pack(side="top", fill="x")
        
        btns = [("Inventario", self.crud_inventario), ("Áreas", self.crud_areas), ("Usuarios", self.crud_usuarios), ("Salir", self.root.quit)]
        for texto, comando in btns:
            tk.Button(menu_bar, text=texto, command=comando, bg="#34495e", fg="white", bd=0, padx=20, pady=10).pack(side="left")

        self.cont_principal = ttk.Frame(self.root, padding="20")
        self.cont_principal.pack(expand=True, fill="both")
        self.crud_inventario() # Carga inicial

    # --- CRUD GENÉRICO (Lógica de Áreas como ejemplo de relación) ---
    def crud_areas(self):
        self.limpiar_contenedor()
        ttk.Label(self.cont_principal, text="GESTIÓN DE ÁREAS", font=("Arial", 14, "bold")).pack()
        
        f_inputs = ttk.Frame(self.cont_principal)
        f_inputs.pack(pady=10)
        
        ttk.Label(f_inputs, text="Nombre Área:").grid(row=0, column=0)
        ent_nombre = ttk.Entry(f_inputs)
        ent_nombre.grid(row=0, column=1, padx=5)

        # Tabla
        tv = ttk.Treeview(self.cont_principal, columns=("ID", "Nombre"), show="headings")
        tv.heading("ID", text="ID"); tv.heading("Nombre", text="Nombre")
        tv.pack(fill="both", expand=True)

        def refrescar():
            tv.delete(*tv.get_children())
            for r in self.cursor.execute("SELECT * FROM areas"): tv.insert("", "end", values=r)

        def guardar():
            if ent_nombre.get():
                self.cursor.execute("INSERT INTO areas (nombre) VALUES (?)", (ent_nombre.get(),))
                self.conexion.commit()
                refrescar()
            
        def eliminar():
            sel = tv.selection()
            if sel:
                id_sel = tv.item(sel)['values'][0]
                self.cursor.execute("DELETE FROM areas WHERE id=?", (id_sel,))
                self.conexion.commit()
                refrescar()

        ttk.Button(f_inputs, text="Añadir", command=guardar).grid(row=0, column=2, padx=5)
        ttk.Button(self.cont_principal, text="Eliminar Seleccionado", command=eliminar).pack(pady=5)
        refrescar()

    # --- CRUD INVENTARIO (CON RELACIÓN A ÁREAS) ---
    def crud_inventario(self):
        self.limpiar_contenedor()
        ttk.Label(self.cont_principal, text="CONTROL DE INVENTARIO", font=("Arial", 14, "bold")).pack()
        
        f_inputs = ttk.Frame(self.cont_principal)
        f_inputs.pack(pady=10)
        
        ttk.Label(f_inputs, text="Producto:").grid(row=0, column=0)
        ent_prod = ttk.Entry(f_inputs); ent_prod.grid(row=0, column=1)
        
        ttk.Label(f_inputs, text="Cant:").grid(row=0, column=2)
        ent_cant = ttk.Entry(f_inputs, width=10); ent_cant.grid(row=0, column=3)

        ttk.Label(f_inputs, text="Área:").grid(row=0, column=4)
        # Cargamos áreas para el menú desplegable
        self.cursor.execute("SELECT id, nombre FROM areas")
        areas_dict = {nom: idx for idx, nom in self.cursor.fetchall()}
        cb_area = ttk.Combobox(f_inputs, values=list(areas_dict.keys()), state="readonly")
        cb_area.grid(row=0, column=5, padx=5)

        tv = ttk.Treeview(self.cont_principal, columns=("ID", "Prod", "Cant", "Area"), show="headings")
        for c in ("ID", "Prod", "Cant", "Area"): tv.heading(c, text=c)
        tv.pack(fill="both", expand=True)

        def refrescar():
            tv.delete(*tv.get_children())
            # Join para ver el nombre del área y no solo el ID
            query = "SELECT i.id, i.producto, i.cantidad, a.nombre FROM inventario i LEFT JOIN areas a ON i.area_id = a.id"
            for r in self.cursor.execute(query): tv.insert("", "end", values=r)

        def guardar():
            if ent_prod.get() and cb_area.get():
                self.cursor.execute("INSERT INTO inventario (producto, cantidad, area_id) VALUES (?,?,?)",
                                    (ent_prod.get(), ent_cant.get(), areas_dict[cb_area.get()]))
                self.conexion.commit()
                refrescar()

        ttk.Button(f_inputs, text="Guardar", command=guardar).grid(row=0, column=6)
        refrescar()

    # --- CRUD USUARIOS ---
    def crud_usuarios(self):
        self.limpiar_contenedor()
        ttk.Label(self.cont_principal, text="GESTIÓN DE USUARIOS", font=("Arial", 14, "bold")).pack()
        # Estructura similar a Áreas para Crear/Leer/Borrar...
        ttk.Label(self.cont_principal, text="(Lógica CRUD idéntica a Áreas aplicada a la tabla 'usuarios')").pack(pady=20)

    # --- UTILIDADES ---
    def limpiar_pantalla(self):
        for w in self.root.winfo_children(): w.destroy()

    def limpiar_contenedor(self):
        for w in self.cont_principal.winfo_children(): w.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaGestion(root)
    root.mainloop()
