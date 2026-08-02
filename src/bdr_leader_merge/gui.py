"""Interfaz grafica minima (Tkinter) para consolidar archivos LEADER."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .api import consolidate

NOMBRE_POR_DEFECTO = "leader_consolidado.xlsx"
EXTENSION = ".xlsx"
TIPOS_EXCEL = [("Archivos Excel", "*.xlsx *.XLSX"), ("Todos los archivos", "*.*")]


class ValidationError(Exception):
    """Entrada invalida del formulario, con mensaje listo para mostrar."""


def _validar_excel(ruta_texto: str, etiqueta: str) -> Path:
    if not ruta_texto.strip():
        raise ValidationError(f"Selecciona el archivo {etiqueta}.")
    ruta = Path(ruta_texto.strip())
    if ruta.suffix.lower() != EXTENSION:
        raise ValidationError(
            f"El archivo {etiqueta} debe ser .xlsx.\n\nSeleccionado: {ruta.name}"
        )
    if not ruta.is_file():
        raise ValidationError(f"No se encuentra el archivo {etiqueta}:\n\n{ruta}")
    return ruta


def _normalizar_nombre(nombre: str) -> str:
    nombre = nombre.strip() or NOMBRE_POR_DEFECTO
    if Path(nombre).name != nombre:
        raise ValidationError(
            "El nombre de salida no puede incluir carpetas.\n\n"
            f"Usa solo un nombre de archivo, por ejemplo: {NOMBRE_POR_DEFECTO}"
        )
    if not nombre.lower().endswith(EXTENSION):
        nombre += EXTENSION
    return nombre


def validar_entradas(
    ruta_n: str, ruta_n1: str, carpeta: str, nombre: str
) -> tuple[Path, Path, Path]:
    """Valida el formulario y devuelve (n, n+1, archivo de salida)."""
    archivo_n = _validar_excel(ruta_n, "Leader n")
    archivo_n1 = _validar_excel(ruta_n1, "Leader n+1")

    if archivo_n.resolve() == archivo_n1.resolve():
        raise ValidationError(
            "Los archivos Leader n y Leader n+1 deben ser distintos.\n\n"
            f"Ambos apuntan a: {archivo_n.name}"
        )

    if not carpeta.strip():
        raise ValidationError("Selecciona la carpeta de salida.")
    destino = Path(carpeta.strip())
    if not destino.is_dir():
        raise ValidationError(f"La carpeta de salida no existe:\n\n{destino}")

    salida = destino / _normalizar_nombre(nombre)
    if salida.resolve() in {archivo_n.resolve(), archivo_n1.resolve()}:
        raise ValidationError(
            "El archivo de salida no puede sobrescribir un archivo de entrada.\n\n"
            f"{salida}"
        )
    return archivo_n, archivo_n1, salida


class LeaderMergeApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=16)
        self.grid(row=0, column=0, sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.var_n = tk.StringVar()
        self.var_n1 = tk.StringVar()
        self.var_carpeta = tk.StringVar()
        self.var_nombre = tk.StringVar(value=NOMBRE_POR_DEFECTO)
        self.var_estado = tk.StringVar(value="Selecciona los archivos y presiona Procesar.")

        self._cola: queue.Queue = queue.Queue()
        self._construir()

    def _construir(self) -> None:
        fila = 0
        ttk.Label(self, text="Consolidacion LEADER", font=("Segoe UI", 13, "bold")).grid(
            row=fila, column=0, columnspan=3, sticky="w", pady=(0, 2)
        )
        fila += 1
        ttk.Label(
            self,
            text="Suma al estimado de la campana n el 5 % del estimado de la campana n+1.",
            foreground="#555555",
        ).grid(row=fila, column=0, columnspan=3, sticky="w", pady=(0, 12))

        fila += 1
        self._fila_archivo(fila, "Archivo Leader n (base):", self.var_n, self._elegir_n)
        fila += 1
        self._fila_archivo(fila, "Archivo Leader n+1:", self.var_n1, self._elegir_n1)
        fila += 1
        self._fila_archivo(fila, "Carpeta de salida:", self.var_carpeta, self._elegir_carpeta)

        fila += 1
        ttk.Label(self, text="Nombre de salida (opcional):").grid(
            row=fila, column=0, sticky="w", pady=4
        )
        ttk.Entry(self, textvariable=self.var_nombre).grid(
            row=fila, column=1, sticky="ew", padx=(8, 8), pady=4
        )

        fila += 1
        ttk.Separator(self, orient="horizontal").grid(
            row=fila, column=0, columnspan=3, sticky="ew", pady=(14, 10)
        )

        fila += 1
        self.barra = ttk.Progressbar(self, mode="indeterminate")
        self.barra.grid(row=fila, column=0, columnspan=2, sticky="ew", padx=(0, 8))
        self.boton = ttk.Button(self, text="Procesar", command=self._procesar)
        self.boton.grid(row=fila, column=2, sticky="e")

        fila += 1
        ttk.Label(self, textvariable=self.var_estado, foreground="#555555", wraplength=560).grid(
            row=fila, column=0, columnspan=3, sticky="w", pady=(12, 0)
        )

    def _fila_archivo(self, fila: int, etiqueta: str, var: tk.StringVar, comando) -> None:
        ttk.Label(self, text=etiqueta).grid(row=fila, column=0, sticky="w", pady=4)
        ttk.Entry(self, textvariable=var).grid(row=fila, column=1, sticky="ew", padx=(8, 8), pady=4)
        ttk.Button(self, text="Examinar...", command=comando).grid(row=fila, column=2, sticky="e")

    # --- selectores ---

    def _elegir_n(self) -> None:
        ruta = filedialog.askopenfilename(
            title="Selecciona el archivo Leader n", filetypes=TIPOS_EXCEL
        )
        if ruta:
            self.var_n.set(ruta)
            if not self.var_carpeta.get():
                self.var_carpeta.set(str(Path(ruta).parent))

    def _elegir_n1(self) -> None:
        ruta = filedialog.askopenfilename(
            title="Selecciona el archivo Leader n+1", filetypes=TIPOS_EXCEL
        )
        if ruta:
            self.var_n1.set(ruta)

    def _elegir_carpeta(self) -> None:
        ruta = filedialog.askdirectory(title="Selecciona la carpeta de salida")
        if ruta:
            self.var_carpeta.set(ruta)

    # --- proceso ---

    def _procesar(self) -> None:
        try:
            archivo_n, archivo_n1, salida = validar_entradas(
                self.var_n.get(), self.var_n1.get(), self.var_carpeta.get(), self.var_nombre.get()
            )
        except ValidationError as exc:
            messagebox.showwarning("Revisa los datos", str(exc), parent=self)
            return

        self.boton.state(["disabled"])
        self.barra.start(12)
        self.var_estado.set("Procesando...")

        hilo = threading.Thread(
            target=self._trabajo, args=(archivo_n, archivo_n1, salida), daemon=True
        )
        hilo.start()
        self.after(100, self._revisar_cola)

    def _trabajo(self, archivo_n: Path, archivo_n1: Path, salida: Path) -> None:
        try:
            self._cola.put(("ok", consolidate(archivo_n, archivo_n1, salida)))
        except Exception as exc:  # se reporta al usuario en el hilo principal
            self._cola.put(("error", exc))

    def _revisar_cola(self) -> None:
        try:
            estado, carga = self._cola.get_nowait()
        except queue.Empty:
            self.after(100, self._revisar_cola)
            return

        self.barra.stop()
        self.boton.state(["!disabled"])

        if estado == "error":
            self.var_estado.set("El proceso fallo.")
            messagebox.showerror(
                "Error al procesar",
                f"No se pudo generar el archivo.\n\n{type(carga).__name__}: {carga}",
                parent=self,
            )
            return

        rep = carga.result.report
        self.var_estado.set(f"Listo: {carga.path}")
        messagebox.showinfo(
            "Consolidacion completada",
            "Archivo generado correctamente.\n\n"
            f"{carga.path}\n\n"
            f"Filas resultado: {rep.filas_resultado}\n"
            f"Cruces material+tipo: {rep.cruces_exactos}\n"
            f"Cruces solo material: {rep.cruces_por_material}\n"
            f"Filas nuevas desde n+1: {rep.filas_nuevas}",
            parent=self,
        )


def main() -> int:
    root = tk.Tk()
    root.title("Consolidacion LEADER")
    root.minsize(620, 300)
    try:
        root.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass
    LeaderMergeApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
