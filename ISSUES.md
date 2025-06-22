# Problemas conocidos y soluciones

## Formato de bloques de código

**Problema:**
Los bloques de código en las conversaciones convertidas a Markdown no se mostraban correctamente:
- No mantenían la indentación
- No detectaban el lenguaje de programación
- Los delimitadores (```) no eran consistentes

**Solución implementada:**
Se modificó la función `html_to_markdown_basic()` en `main.py` para:
1. Detectar automáticamente el lenguaje de programación (cuando está especificado en clases CSS)
2. Preservar la indentación y espacios en blanco
3. Manejar consistentemente bloques con/sin etiqueta `<code>`
4. Escapar caracteres especiales en código inline

**Ejemplo antes:**
```
    def example():
    print('Hello World')
```

**Ejemplo después:**
```python
def example():
    print('Hello World')
```
