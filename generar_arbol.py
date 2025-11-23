import os

def generar_arbol(ruta_inicio, archivo_salida, ignorar=None):
    if ignorar is None:
        ignorar = {'.git', '__pycache__', '.vscode', 'venv', 'env', '.idea'}

    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write(f"📂 ESTRUCTURA DE: {os.path.abspath(ruta_inicio)}\n")
        f.write("=" * 50 + "\n")
        
        for root, dirs, files in os.walk(ruta_inicio):
            # Filtrar carpetas ignoradas para no entrar en ellas
            dirs[:] = [d for d in dirs if d not in ignorar]
            
            level = root.replace(ruta_inicio, '').count(os.sep)
            indent = ' ' * 4 * (level)
            
            # Nombre de la carpeta actual
            carpeta_actual = os.path.basename(root)
            if level == 0:
                f.write(f".\n")
            else:
                f.write(f"{indent}📁 {carpeta_actual}/\n")
            
            subindent = ' ' * 4 * (level + 1)
            
            # Listar archivos
            for file in sorted(files):
                if file not in ignorar and not file.endswith('.pyc'):
                    f.write(f"{subindent}📄 {file}\n")

if __name__ == "__main__":
    nombre_archivo = "mi_arbol_actual.txt"
    generar_arbol(".", nombre_archivo)
    print(f"✅ ¡Listo! Se ha generado el archivo '{nombre_archivo}'.")
