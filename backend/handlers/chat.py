import json
import urllib.parse
import urllib.request
import urllib.error
from ..database import get_db_connection
from ..config import GEMINI_API_KEY

def send_json(handler, status, data):
    handler.send_response(status)
    handler.send_header('Content-type', 'application/json')
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode())

def handle_chat(data, handler):
    user_message = data.get('message', '')
    user_id = data.get('userId')
    history = data.get('history', [])
    
    # 1. Build Context
    context_prompt = "ACTÚA COMO: Asistente experto en nutrición renal (Nefrólogo/Nutricionista)."
    context_prompt += "\nTU OBJETIVO: Aconsejar al paciente basándote EXCLUSIVAMENTE en su perfil médico (que te proporciono abajo) y en la base de datos de alimentos."
    
    if user_id:
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

            # Simple Food Search for Context
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
                    context_prompt += "\n\nDATOS NUTRICIONALES DETECTADOS:"
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
                         
                         nut_str = ", ".join([f"{n['key']}: {n['value']}{n['unit']}" for n in nutrients if n['key'] in ['potassium','phosphorus','protein','sodium']])
                         context_prompt += f"\n- {name}: {nut_str}"

            except Exception as e:
                print(f"Chat DB Lookups Error: {e}")

            conn.close()
        except Exception as e:
            print(f"Chat DB Error: {e}")

    context_prompt += "\nIMPORTANTE: Detecta el idioma del usuario y responde SIEMPRE en ese mismo idioma (Español, Inglés, Alemán, etc)."
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
