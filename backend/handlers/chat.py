import json
import urllib.parse
import urllib.request
import urllib.error
from ..database import get_db_connection
from ..config import GEMINI_API_KEY
from ..utils import send_json



def handle_chat(data, handler):
    user_message = data.get('message', '')
    user_id = data.get('userId')
    history = data.get('history', [])
    
    # 1. Build Context
    context_prompt = ""
    
    if not user_id:
        # --- SAFE MODE (Guest / No Login) ---
        context_prompt = "ACTÚA COMO: Enciclopedia de Alimentos (Nutrición Renal)."
        context_prompt += "\nTU OBJETIVO: Proporcionar DATOS NUTRICIONALES OBJETIVOS (Potasio, Fósforo, etc) sobre los alimentos que pregunte el usuario."
        context_prompt += "\nREGLA CRÍTICA DE SEGURIDAD: NO des consejos médicos personalizados ni recomendaciones sobre si 'puede comer' algo, ya que NO conoces su historial médico."
        context_prompt += "\nSI EL USUARIO PIDE CONSEJO (ej: '¿Puedo comer esto?'): Responde dando el dato nutricional y añade: 'Por favor, inicia sesión para que pueda verificar tu perfil médico y aconsejarte con seguridad.'."
    else:
        # --- MEDICAL MODE (Logged In User) ---
        context_prompt = "ACTÚA COMO: Asistente experto en nutrición renal (Nefrólogo/Nutricionista)."
        context_prompt += "\nTU OBJETIVO: Aconsejar al paciente basándote EXCLUSIVAMENTE en su perfil médico, que te proporciono abajo."
        context_prompt += "\nSi te pide algo elaborado, como una receta o menú, dásela pero con advertencia médica. IMPORTANTE: NO USES TABLAS MARKDOWN (|...|), el sistema no las soporta. Usa LISTAS con viñetas y NEGRILLAS para estructurar."
        context_prompt += "\nESTILO VISUAL: Usa MUCHOS emoticonos (🥘, 🥕, 👨‍⚕️, 📅) en tus respuestas para que sea visual y amigable. Tienes prohibido el 'texto plano' aburrido para cuando te piden menus o recetas."
        context_prompt += "\n\n📒 **CALCULADORA NUTRICIONAL ACTIVADA**"
        context_prompt += "\nSi el usuario pide un **MENÚ**, USA LISTAS (Bullets), **NO USES TABLAS**."
        context_prompt += "\n\nFORMATO OBLIGATORIO POR COMIDA:"
        context_prompt += "\n   *   **Nombre del Plato** (descripción breve)."
        context_prompt += "\n       - *Nutrientes: Calorías: X kcal, Proteínas: Xg, Carbohidratos: Xg, Fósforo: Xmg, Potasio: Xmg, Sodio: Xmg.*"
        context_prompt += "\n\nREGLAS DE ESTILO:"
        context_prompt += "\n   1. **NO USES ICONOS** para los nutrientes. Usa las palabras completas (Proteína, Potasio, etc). Muestra todos los nutrientes que se muestran en la web"
        context_prompt += "\n   2. Pon los datos justo DEBAJO del plato, indentado si es posible."
        context_prompt += "\n   3. Si es un menú semanal, separa los días claramente (LUNES, MARTES...)."
        context_prompt += "\n   (Es vital que des estos valores estimados para la seguridad del paciente)."


        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute('SELECT has_insufficiency, kidney_stage, treatment_type, name FROM users WHERE id = ?', (user_id,))
            row = c.fetchone()
            
            if row:
                has_insufficiency, stage, treatment, u_name = row['has_insufficiency'], row['kidney_stage'], row['treatment_type'], row['name']
                context_prompt += f"\n\nPERFIL DEL PACIENTE (ESTE ES EL USUARIO CON EL QUE HABLAS):"
                context_prompt += f"\n- Nombre: {u_name}"
                if has_insufficiency == '1' or has_insufficiency == 1:
                    if treatment == 'dialysis':
                        context_prompt += "\n- Condición: DIÁLISIS (Requiere: Alta proteína, Control estricto de Potasio/Fósforo/Sodio/Líquidos)."
                    elif treatment == 'transplant':
                        context_prompt += f"\n- Condición: TRASPLANTE RENAL (Estadio {stage}). (Requiere: Dieta equilibrada, evitar pomelo/seguridad alimentaria, control de sal)."
                    else:
                        context_prompt += f"\n- Condición: ENFERMEDAD RENAL CRÓNICA (ERC) ESTADIO {stage} (Pre-diálisis). (Requiere: Bajo sodio, proteína moderada/baja, control de potasio/fósforo según analíticas)."
                else:
                    context_prompt += "\n- Condición: Riñones sanos (Sin insuficiencia)."
                
                context_prompt += "\nINSTRUCCIÓN CLAVE: El usuario YA te ha dado estos datos en su perfil. NO digas 'no tengo acceso a tus datos'. TÚ TIENES ESTOS DATOS. Úsalos para personalizar cada respuesta."

            # Simple Food Search for Context (Only relevant for detailed medical advice or specific questions)
            try:
                c.execute("SELECT food_id, name FROM food_translations WHERE lang='es'")
                all_foods = c.fetchall()
                
                # Normalize function
                def normalize(text):
                    import unicodedata
                    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')

                user_msg_norm = normalize(user_message)
                found_foods = []
                for food in all_foods:
                    f_name = food['name']
                    if len(f_name) > 2 and normalize(f_name) in user_msg_norm:
                        found_foods.append(food['food_id'])

                if found_foods:
                    context_prompt += "\n\nDATOS NUTRICIONALES DETECTADOS (Base de Datos):"
                    for f_id in found_foods[:3]:
                         c.execute("""
                            SELECT n.key, fn.value, n.unit 
                            FROM food_nutrients fn 
                            JOIN nutrients n ON fn.nutrient_id = n.id 
                            WHERE fn.food_id = ?
                        """, (f_id,))
                         nutrients = c.fetchall()
                         # We need the name again
                         c.execute("SELECT name FROM food_translations WHERE food_id = ? AND lang='es'", (f_id,))
                         name_row = c.fetchone()
                         name = name_row['name'] if name_row else f"Food {f_id}"
                         
                         nut_str = ", ".join([f"{n['key']}: {n['value']}{n['unit']}" for n in nutrients if n['key'] in ['potassium','phosphorus','protein','carbs','sodium']])
                         context_prompt += f"\n- {name}: {nut_str}"

            except Exception as e:
                print(f"Chat DB Lookups Error: {e}")

            conn.close()
        except Exception as e:
            print(f"Chat DB Error: {e}")

    context_prompt += "\n\nIMPORTANTE: Detecta el idioma del usuario y responde SIEMPRE en ese mismo idioma (Español, Inglés, Alemán, etc)."
    context_prompt += "\nResponde de forma breve y empática."

    # 2. Call Gemini
    if not GEMINI_API_KEY:
        send_json(handler, 500, {"error": "Missing API Key"})
        return

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    contents = []
    
    # Sanitize History to ensure alternating roles (User -> Model -> User -> Model)
    last_role = None
    
    for note in history:
        text = note.get('text', '').strip()
        role = note.get('role', 'user')
        
        if not text:
            continue
            
        if role == last_role:
            if contents:
                contents[-1]['parts'][0]['text'] += f"\n\n{text}"
        else:
            contents.append({"role": role, "parts": [{"text": text}]})
            last_role = role
            
    full_prompt = f"{context_prompt}\n\nPregunta: {user_message}"
    
    if last_role == 'user':
        if contents:
             contents[-1]['parts'][0]['text'] += f"\n\n{full_prompt}"
        else:
             contents.append({"role": "user", "parts": [{"text": full_prompt}]})
    else:
        contents.append({"role": "user", "parts": [{"text": full_prompt}]})
    
    payload = {"contents": contents}
    
    try:
        req = urllib.request.Request(api_url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            try:
                ai_text = result['candidates'][0]['content']['parts'][0]['text']
                send_json(handler, 200, {"response": ai_text})
            except Exception as e:
                print(f"Gemini Parse Error: {e}, Raw: {result}")
                send_json(handler, 500, {"error": "Bad API Response", "raw": result})
    except urllib.error.HTTPError as e:
        err_content = e.read().decode()
        print(f"Gemini HTTP Error {e.code}: {err_content}")
        send_json(handler, 500, {"error": f"API Error {e.code}", "details": err_content})
    except Exception as e:
        print(f"Gemini General Error: {e}")
        send_json(handler, 500, {"error": str(e)})
