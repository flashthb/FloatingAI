# Launcher IA (Windows) - versión inicial

Aplicación de escritorio en Python que actúa como un launcher tipo Raycast/Spotlight y consulta a una IA (OpenAI). Esta primera versión está pensada para Windows.

Características principales
- Ejecuta en segundo plano y escucha atajo global Ctrl+Space.
- Abre una ventana pequeña, frameless y siempre encima.
- Input para preguntar y área para respuesta breve (máx ~3–5 líneas).
- Usa OpenAI si se configura OPENAI_API_KEY; si no, usa un simulador local sencillo.
- No guarda nada en disco.

Instalación (Windows)

1. Crear y activar entorno virtual

   python -m venv venv
   venv\Scripts\activate

2. Instalar dependencias

   pip install -r requirements.txt

3. Configurar OpenAI (opcional)

   Si tienes clave de OpenAI, exporta la variable de entorno OPENAI_API_KEY. En Windows (PowerShell):

   setx OPENAI_API_KEY "sk-..."

   Cierra y abre la terminal para que la variable esté disponible.

Ejecución

   python main.py

Uso

- Pulsa Ctrl+Space para abrir/ocultar la ventana.
- Escribe la pregunta y pulsa Enter para enviar.
- Pulsa Esc o haz click fuera para ocultar la ventana.

Notas

- En esta versión la aplicación se cierra con Ctrl+C en la consola (no hay icono en bandeja todavía).
- Si no hay OPENAI_API_KEY la app seguirá funcionando con un simulador que devuelve respuestas muy cortas.
