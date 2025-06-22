import os
from bs4 import BeautifulSoup, NavigableString, Tag
import re
from markdown_enhancer import EnhancedMarkdownConverter
from datetime import datetime
import subprocess
import argparse

def html_to_markdown_basic(element):
    if isinstance(element, NavigableString):
        return str(element)

    if isinstance(element, list): # Handle list of elements (e.g., element.contents)
        return ''.join([html_to_markdown_basic(child) for child in element])

    if element.name == 'p':
        return html_to_markdown_basic(element.contents) + '\n\n'
    elif element.name in ['strong', 'b']:
        return '**' + html_to_markdown_basic(element.contents) + '**'
    elif element.name in ['em', 'i']:
        return '*' + html_to_markdown_basic(element.contents) + '*'
    elif element.name.startswith('h') and len(element.name) == 2 and element.name[1].isdigit():
        level = int(element.name[1])
        return '#' * level + ' ' + html_to_markdown_basic(element.contents) + '\n\n'
    elif element.name == 'blockquote':
        content = html_to_markdown_basic(element.contents)
        # Add '>' prefix to each line of the blockquote content
        return '> ' + content.replace('\n', '\n> ') + '\n\n'
    elif element.name == 'ul':
        list_items = []
        for li in element.find_all('li', recursive=False):
            list_items.append(html_to_markdown_basic(li))
        return '\n'.join(['* ' + item for item in list_items]) + '\n\n'
    elif element.name == 'ol':
        list_items = []
        for i, li in enumerate(element.find_all('li', recursive=False)):
            list_items.append(html_to_markdown_basic(li))
        return '\n'.join([f'{i+1}. ' + item for i, item in enumerate(list_items)]) + '\n\n'
    elif element.name == 'li':
        return html_to_markdown_basic(element.contents)
    elif element.name == 'a':
        href = element.get('href', '')
        text = html_to_markdown_basic(element.contents)
        return f'[{text}]({href})'
    elif element.name == 'pre':
        code_tag = element.find('code')
        if code_tag:
            # Obtener el lenguaje del código si está especificado
            language = ''
            for cls in code_tag.get('class', []):
                if cls.startswith('language-'):
                    language = cls[len('language-'):]
                    break
            
            code_content = code_tag.get_text(strip=False)
            # Normalizar espacios y mantener indentación
            code_content = '\n'.join(line.rstrip() for line in code_content.splitlines())
            return f'```{language}\n{code_content}\n```\n\n'
        else:
            # Si es un pre sin code, tratarlo como bloque de código sin lenguaje especificado
            code_content = element.get_text(strip=False)
            code_content = '\n'.join(line.rstrip() for line in code_content.splitlines())
            return f'```\n{code_content}\n```\n\n'
    elif element.name == 'code':
        if element.find_parent('pre'):  # Ya manejado por el caso 'pre'
            return element.get_text(strip=False)
        else:  # Código inline
            code_text = element.get_text(strip=True)
            # Escapar caracteres especiales
            code_text = code_text.replace('`', '\`')
            return f'`{code_text}`'
    elif element.name == 'br':
        return '\n'
    elif element.contents:
        return ''.join([html_to_markdown_basic(child) for child in element.contents])
    else:
        return ''


def convert_to_gemini_markdown(html_file):
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        conversation = extract_gemini_conversation_singlepage(html_file)
        print(f"📊 Extraídos {len(conversation)} mensajes de {html_file}")
        
        # Extraer metadatos
        title = soup.title.string if soup.title else os.path.basename(html_file).replace('.html', '')
        date_match = re.search(r'(\d{1,2}[_/]\d{1,2}[_/]\d{2,4})', html_file)
        date_str = date_match.group(1).replace('_', '/') if date_match else datetime.now().strftime("%Y-%m-%d")
        
        # Generar Markdown
        markdown = f"""# 💬 {title}
**📅 Fecha de conversación:** {date_str}  
**🔄 Exportado:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  

<style>
.chat-container {{
    max-width: 800px;
    margin: 0 auto;
    font-family: 'Google Sans', Arial, sans-serif;
}}
.user-message {{
    background: #4285F4;
    color: white;
    border-radius: 18px 18px 0 18px;
    padding: 12px 16px;
    margin: 8px 0 8px auto;
    max-width: 85%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}}
.bot-message {{
    background: #f1f3f4;
    border-radius: 18px 18px 18px 0;
    padding: 12px 16px;
    margin: 8px auto 8px 0;
    max-width: 85%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}}
</style>

<div class="chat-container">
"""
        for msg in conversation:
            bubble_class = "user-message" if msg['speaker'] == "Tú" else "bot-message"
            markdown += f"""<div class="{bubble_class}">
<strong>{msg['speaker']}:</strong><br>
{msg['content']}
</div>

"""
            
        markdown += "\n</div>"
        return markdown
        
    except Exception as e:
        print(f"⚠️ Error procesando {html_file}: {str(e)}")
        return None

def extract_conversation_with_pandoc(html_file):
    # Check if pandoc is installed
    try:
        subprocess.run(['pandoc', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ pandoc no está instalado. Por favor, instálalo con 'sudo apt install pandoc'")
        return []
    
    # Convert HTML to Markdown
    markdown_file = html_file.replace('.html', '.md')
    subprocess.run(['pandoc', html_file, '-o', markdown_file], check=True)
    
    # Read the Markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Split into messages by looking for patterns
    # Example: **Tú:** or **Gemini:**
    pattern = r'\*\*(Tú|Gemini):\*\*'
    messages = re.split(pattern, markdown_content)
    
    # The first part is before the first speaker, so we skip it
    conversation = []
    for i in range(1, len(messages), 2):
        speaker = messages[i].strip()
        content = messages[i+1].strip()
        conversation.append({
            'speaker': speaker,
            'content': content
        })
    
    return conversation

def extract_conversation_with_html2text(html_file):
    try:
        import html2text
    except ImportError:
        print("⚠️ html2text no está instalado. Por favor, instálalo con 'pip install html2text'")
        return []
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Convert HTML to Markdown
    text_maker = html2text.HTML2Text()
    text_maker.ignore_links = False
    markdown_content = text_maker.handle(html_content)
    
    # Split into messages by looking for patterns
    # Example: **Tú:** or **Gemini:**
    pattern = r'\*\*(Tú|Gemini):\*\*'
    messages = re.split(pattern, markdown_content)
    
    # The first part is before the first speaker, so we skip it
    conversation = []
    for i in range(1, len(messages), 2):
        speaker = messages[i].strip()
        content = messages[i+1].strip()
        conversation.append({
            'speaker': speaker,
            'content': content
        })
    
    return conversation

def extract_gemini_conversation_singlepage(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    message_elements_with_speaker = []

    # 1. Extract Gemini responses
    # Find all potential message containers in document order
    # This includes the main div for Gemini responses and the p tags for user queries
    all_potential_message_elements = soup.find_all(lambda tag:
        (tag.name == 'div' and tag.has_attr('id') and tag['id'].startswith('model-response-message-contentr_')) or
        (tag.name == 'p' and 'query-text-line' in tag.get('class', []))
    )

    print(f"DEBUG: Found {len(all_potential_message_elements)} total potential message elements.")

    for element in all_potential_message_elements:
        speaker = None
        content = ""

        if element.name == 'div' and element.has_attr('id') and element['id'].startswith('model-response-message-contentr_'):
            speaker = 'Gemini'
            # Pass the entire container to the new converter
            converter = EnhancedMarkdownConverter()
            # We need to pass the HTML string of the element
            content = converter.convert(element.prettify())
        elif element.name == 'p' and 'query-text-line' in element.get('class', []):
            speaker = 'Tú'
            converter = EnhancedMarkdownConverter()
            content = converter.convert(element.prettify())

        if speaker and content and content.strip():
            message_elements_with_speaker.append({
                'speaker': speaker,
                'content': content,
                'original_element': element # Keep original element for debugging if needed, but not for sorting
            })

    # Sort all collected messages by their original position in the document
    all_elements_in_order = list(soup.find_all(True))
    element_to_index = {el: i for i, el in enumerate(all_elements_in_order)}

    message_elements_with_speaker.sort(key=lambda x: element_to_index.get(x['original_element'], float('inf')))
    
    # Clean duplicates and format final output
    cleaned_conversation = []
    seen_contents = set()
    for msg in message_elements_with_speaker:
        # A simple way to check for duplicates, might need refinement if messages are very similar
        if msg['content'] not in seen_contents:
            cleaned_conversation.append({'speaker': msg['speaker'], 'content': msg['content']})
            seen_contents.add(msg['content'])
            
    return cleaned_conversation

def extract_conversation_combined(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    conversation = []
    
    # Enfoque 1: Búsqueda por contenedores principales
    main_containers = soup.find_all(class_=re.compile('conversation-container|chat-container'))
    for container in main_containers:
        # Extraer contenido textual significativo
        content = container.get_text('\n', strip=True)
        if len(content) < 30:
            continue
            
        # Determinar speaker por contexto
        classes = ' '.join(container.get('class', []))
        if 'user' in classes.lower():
            speaker = 'Tú'
        elif 'bot' in classes.lower() or 'gemini' in classes.lower():
            speaker = 'Gemini'
        else:
            # Enfoque 2: Detección por patrones lingüísticos
            if 'tú:' in content.lower() or 'you:' in content.lower():
                speaker = 'Tú'
            elif 'gemini:' in content.lower() or 'model:' in content.lower():
                speaker = 'Gemini'
            else:
                continue
                
        conversation.append({
            'speaker': speaker,
            'content': content
        })
    
    return conversation

def extract_conversation_from_text(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Ajustar regex para capturar más bloques de texto
    message_blocks = re.findall(r'(\w[\w\s.,;:!?()-]{20,})', html_content)
    print(f"🔍 Encontrados {len(message_blocks)} bloques de texto en {html_file}")
    
    conversation = []
    user_keywords = [
        'tú:', 'you:', 'user:', 'enviaste', 'escribiste', 'pregunta:', 
        'dijiste:', 'comentaste:', 'preguntaste:', 'indicaste:'
    ]
    bot_keywords = [
        'gemini:', 'model:', 'respuesta:', 'asistente:', 'ia:', 'ai:', 
        'yo:', 'como ia', 'como modelo', 'puedo ayudarte', 'puedo ayudarle'
    ]
    
    for i, block in enumerate(message_blocks):
        # Saltar bloques demasiado cortos
        if len(block) < 30:
            print(f"🚫 Bloque {i+1}: demasiado corto ({len(block)} caracteres)")
            continue
            
        # Verificar palabras clave de usuario
        if any(keyword in block.lower() for keyword in user_keywords):
            speaker = 'Tú'
            print(f"👤 Bloque {i+1}: identificado como usuario")
        # Verificar palabras clave de bot
        elif any(keyword in block.lower() for keyword in bot_keywords):
            speaker = 'Gemini'
            print(f"🤖 Bloque {i+1}: identificado como Gemini")
        else:
            # Si no tiene palabras clave, pero estamos en medio de una conversación, intentar inferir
            if conversation:
                # Si el último mensaje fue del usuario, este debe ser de Gemini y viceversa
                last_speaker = conversation[-1]['speaker']
                if last_speaker == 'Tú':
                    speaker = 'Gemini'
                    print(f"🔁 Bloque {i+1}: inferido como Gemini (turno alternado)")
                else:
                    speaker = 'Tú'
                    print(f"🔁 Bloque {i+1}: inferido como usuario (turno alternado)")
            else:
                print(f"❓ Bloque {i+1}: no se pudo determinar el hablante")
                continue
            
        conversation.append({
            'speaker': speaker,
            'content': block
        })
    
    print(f"📋 {len(conversation)} mensajes válidos extraídos")
    return conversation

def extract_conversation_hybrid(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    conversation = []
    
    # Try to find the main conversation container
    container = soup.find(class_=re.compile('chat-history|conversation-container'))
    if not container:
        container = soup
    
    # Find all elements that might be messages
    candidates = container.find_all(['div', 'section', 'article', 'p'])
    
    # We'll assume the conversation starts with the user
    next_speaker = 'Tú'
    
    for candidate in candidates:
        content = candidate.get_text('\n', strip=True)
        if len(content) < 20:
            continue
            
        # Check if the content matches a message pattern
        if 'tú:' in content.lower() or 'you:' in content.lower():
            speaker = 'Tú'
            next_speaker = 'Gemini'
        elif 'gemini:' in content.lower() or 'model:' in content.lower():
            speaker = 'Gemini'
            next_speaker = 'Tú'
        else:
            # If no indicators, use the expected next speaker
            speaker = next_speaker
            # Flip the speaker for the next message
            next_speaker = 'Gemini' if next_speaker == 'Tú' else 'Tú'
            
        conversation.append({
            'speaker': speaker,
            'content': content
        })
    
    return conversation

def extract_conversation_targeted(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    conversation = []
    
    # Try to find the main conversation container
    container = soup.find(class_=re.compile('chat-history|conversation-container'))
    if not container:
        container = soup
    
    # Find all elements that might be messages
    candidates = container.find_all(['div', 'section', 'article', 'p'])
    
    # We'll assume the conversation starts with the user
    next_speaker = 'Tú'
    
    for candidate in candidates:
        content = candidate.get_text('\n', strip=True)
        if len(content) < 20:
            continue
            
        # Check if the content matches a message pattern
        if 'tú:' in content.lower() or 'you:' in content.lower():
            speaker = 'Tú'
            next_speaker = 'Gemini'
        elif 'gemini:' in content.lower() or 'model:' in content.lower():
            speaker = 'Gemini'
            next_speaker = 'Tú'
        else:
            # If no indicators, use the expected next speaker
            speaker = next_speaker
            # Flip the speaker for the next message
            next_speaker = 'Gemini' if next_speaker == 'Tú' else 'Tú'
            
        conversation.append({
            'speaker': speaker,
            'content': content
        })
    
    return conversation

def debug_html_structure(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Mostrar estructura básica
    print("\nEstructura del documento:")
    print(f"Título: {soup.title.string if soup.title else 'No encontrado'}")
    
    # Buscar contenedores de chat
    chat_containers = soup.find_all(class_=re.compile('chat|message|conversation'))
    print(f"\nSe encontraron {len(chat_containers)} contenedores de chat")
    
    # Mostrar primeros 3 mensajes con su estructura
    print("\nEjemplo de mensajes (primeros 3):")
    messages = soup.find_all(class_=re.compile('message|bubble'))
    for i, msg in enumerate(messages[:3]):
        print(f"\nMensaje {i+1}:")
        print(f"Clases: {msg.get('class', [])}")
        print(f"Contenido: {msg.get_text(strip=True)[:100]}...")
        print(f"Atributos: {dict(list(msg.attrs.items())[:3])}")

def process_conversations_folder(input_dir):
    try:
        html_files = [f for f in os.listdir(input_dir) if f.endswith('.html')]
        if not html_files:
            print("⚠️ No se encontraron archivos .html en el directorio de entrada")
            print("   Coloca tus archivos SingleFile HTML en:", os.path.abspath(input_dir))
            return
            
        success_count = 0
        for html_file in html_files:
            input_path = os.path.join(input_dir, html_file)
            markdown = convert_to_gemini_markdown(input_path)
            
            if markdown:
                output_path = os.path.join(input_dir, f"{os.path.splitext(html_file)[0]}.md")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                print(f"✅ Guardado en: {output_path}")
                success_count += 1
        
        print(f"\n🎉 Proceso completado: {success_count}/{len(html_files)} archivos convertidos")
    
    except Exception as e:
        print(f"⚠️ Error procesando directorio: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Convert Gemini HTML conversations to Markdown')
    parser.add_argument('input_path', help='Path to HTML file or directory containing HTML files')
    args = parser.parse_args()

    if os.path.isfile(args.input_path):
        # Es un archivo, procesarlo directamente
        extract_conversation_targeted(args.input_path)
    elif os.path.isdir(args.input_path):
        # Es un directorio, procesar todos los archivos
        process_conversations_folder(args.input_path)
    else:
        print(f"Error: Path '{args.input_path}' does not exist or is not a file/directory")
        return 1

if __name__ == "__main__":
    main()