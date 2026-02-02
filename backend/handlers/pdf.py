import json
from fpdf import FPDF
from ..utils import send_json
from ..database import get_db_connection

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        # Title
        self.cell(0, 10, 'Alimentación Renal Inteligente', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def handle_generate_pdf(data, handler):
    user_id = data.get('userId')
    text = data.get('text', '')
    
    if not user_id:
        send_json(handler, 401, {"error": "Unauthorized"})
        return

    # Verify user exists
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT name FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()

    if not user:
        send_json(handler, 401, {"error": "User not found"})
        return

    try:
        pdf = PDF()
        pdf.add_page()
        
        # Add User Name
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Menú generado para: {user['name']}", 0, 1, 'L')
        pdf.ln(5)
        
        # Load Fonts
        import os
        
        # Paths
        font_dir = r'C:\Windows\Fonts'
        arial_path = os.path.join(font_dir, 'arial.ttf')
        emoji_path = os.path.join(font_dir, 'seguiemj.ttf')
        
        has_arial = False
        has_emoji = False

        # 1. Load Main Font (Arial)
        if os.path.exists(arial_path):
            try:
                pdf.add_font('ArialUnicode', fname=arial_path)
                has_arial = True
            except Exception as e:
                print(f"Error loading Arial: {e}")

        # 2. Load Fallback (Emoji)
        if os.path.exists(emoji_path):
            try:
                pdf.add_font('Emoji', fname=emoji_path)
                has_emoji = True
            except Exception as e:
                print(f"Error loading Emoji: {e}")

        if has_emoji:
            try:
                pdf.set_fallback_fonts(['Emoji'])
            except Exception as e:
                print(f"Error setting fallback: {e}")

        # Helper to set font
        def set_font_style(style='', size=10):
            # Prefer our loaded TTF Arial because it supports Unicode (and fallbacks)
            if has_arial:
                pdf.set_font('ArialUnicode', style, size)
            else:
                # Fallback to core font (no emoji, no unicode outside latin-1)
                pdf.set_font('Arial', style, size)

        # Header logic would be here, but we are in the handler. 
        
        set_font_style(size=10)

        # 1. Clean Markdown artifacts
        lines = text.split('\n')
        
        start_table = False
        table_lines = []
        
        normal_buffer = []

        def flush_normal_buffer():
            if normal_buffer:
                content = "\n".join(normal_buffer)
                content = content.replace("**", "").replace("### ", "").replace("`", "")
                
                # No encoding needed! FPDF2 handles Unicode with TTF fonts.
                pdf.multi_cell(0, 6, content)
                pdf.ln(2)
                normal_buffer.clear()

        def render_table(t_lines):
            data_rows = []
            for row_idx, line in enumerate(t_lines):
                if "---" in line and "|" in line: continue
                cells = [c.strip() for c in line.split('|')]
                if len(cells) > 0 and cells[0] == '': cells.pop(0)
                if len(cells) > 0 and cells[-1] == '': cells.pop()
                
                clean_cells = []
                for cell in cells:
                    cell = cell.replace("**", "")
                    clean_cells.append(cell)
                
                if clean_cells:
                    data_rows.append(clean_cells)

            if data_rows:
                pdf.ln(2)
                try:
                    with pdf.table() as table:
                        for i, row_data in enumerate(data_rows):
                            row = table.row()
                            for datum in row_data:
                                if i == 0:
                                    # Use bold if possible, but simplistic here
                                    # FPDF2 fallback support for bold might vary
                                    pdf.set_fill_color(240, 240, 240)
                                    # Try to set bold style if ArialUnicode supports it, 
                                    # otherwise keep normal
                                    set_font_style('', 10) 
                                else:
                                    set_font_style('', 10)
                                    pdf.set_fill_color(255, 255, 255)
                                row.cell(datum)
                    pdf.ln(5)
                except Exception as table_err:
                     print(f"Table Render Error: {table_err}")
                     # Fallback
                     flush_text = "\n".join(t_lines)
                     pdf.multi_cell(0, 6, flush_text)
            
            set_font_style(size=10)

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('|') and stripped.count('|') >= 1:
                if not start_table:
                    flush_normal_buffer()
                    start_table = True
                table_lines.append(stripped)
            else:
                if start_table:
                   render_table(table_lines)
                   table_lines = []
                   start_table = False
                normal_buffer.append(line)
        
        if start_table:
            render_table(table_lines)
        flush_normal_buffer()
        
        # Output
        # fpdf2 .output() returns a bytearray if no arguments provided
        pdf_bytes = pdf.output()
        
        handler.send_response(200)
        handler.send_header('Content-Type', 'application/pdf')
        handler.send_header('Content-Disposition', 'attachment; filename="menu_renal.pdf"')
        handler.end_headers()
        
        # Ensure it is bytes
        if isinstance(pdf_bytes, bytearray):
            handler.wfile.write(bytes(pdf_bytes))
        else:
            handler.wfile.write(pdf_bytes)
        
    except Exception as e:
        print(f"PDF Generation Error: {str(e)}") # Use str(e) to avoid encoding crash
        import traceback
        traceback.print_exc()
        # Return the error to the client for debugging
        send_json(handler, 500, {"error": f"PDF Error: {str(e)}"})
