import os
import re
import uuid
import pandas as pd
from flask import Blueprint, request, session, render_template, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from utils import allowed_file, read_dataframe, save_dataframe

# Membuat Blueprint untuk halaman ini
detector_bp = Blueprint('detector', __name__)

def format_issue_log(issue_name, locations, limit=5):
    """Memformat daftar lokasi masalah untuk ditampilkan di log."""
    if not locations:
        return ""
    
    total = len(locations)
    log_str = f"<b>{issue_name} ({total} ditemukan):</b><ul>"
    
    for i, (row, col) in enumerate(locations):
        if i < limit:
            log_str += f"<li>- Baris {row + 1}, Kolom '{col}'</li>"
    
    if total > limit:
        log_str += f"<li>- ... dan {total - limit} lainnya.</li>"
        
    log_str += "</ul>"
    return log_str

@detector_bp.route('/')
@detector_bp.route('/advanced-cleaner', methods=['GET', 'POST'])
def advanced_cleaner():
    """Halaman utama untuk deteksi masalah data."""
    context = {
        'headers': [], 'data': [], 'log_message': '', 'upload_error': '',
        'issues': {'missing': [], 'duplicates': [], 'symbols': [], 'contaminated_alpha': [], 'contaminated_numeric': []},
        'data_uploaded': False, 'sheet_names': None, 'active_page': 'advanced', 
        'col_types': {}, 'rows': 0, 'cols': 0, 'issues_found': False
    }
    
    if request.method == 'GET':
        filepath = session.pop('filepath', None)
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return render_template('advanced_cleaner.html', **context)

    df = None
    action = request.form.get('action')
    
    if action not in ['upload', 'load_sheet'] and 'filepath' in session and os.path.exists(session['filepath']):
        try:
            df = read_dataframe(session['filepath'])
            context['data_uploaded'] = True
        except Exception as e:
            context['log_message'] = f"Error: Tidak dapat membaca file dari session: {e}"
            session.pop('filepath', None)
            context['data_uploaded'] = False

    if action == 'upload':
        filepath = session.pop('filepath', None)
        if filepath and os.path.exists(filepath):
            os.remove(filepath)

        file = request.files.get('file')
        if file and file.filename != '' and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                temp_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4()}_{filename}")
                file.save(temp_filepath)

                if filename.lower().endswith(('.xls', '.xlsx')):
                    xls = pd.ExcelFile(temp_filepath)
                    sheet_names = xls.sheet_names
                    if len(sheet_names) > 1:
                        session['temp_filepath'] = temp_filepath
                        context['sheet_names'] = sheet_names
                        context['log_message'] = "File Excel terdeteksi. Silakan pilih sheet yang akan dianalisis."
                    else:
                        df = pd.read_excel(temp_filepath)
                        os.remove(temp_filepath)
                else:
                    df = pd.read_csv(temp_filepath, low_memory=False)
                    os.remove(temp_filepath)

                if df is not None:
                    unique_id = str(uuid.uuid4())
                    internal_filename = f"{unique_id}_{filename.rsplit('.', 1)[0]}.csv"
                    internal_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], internal_filename)
                    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
                    save_dataframe(df, internal_filepath)
                    session['filepath'] = internal_filepath
                    context['data_uploaded'] = True
                    context['log_message'] = "File berhasil di-upload. Tentukan tipe kolom dan lakukan aksi."
            except Exception as e:
                context['upload_error'] = f"Error: Gagal memproses file: {e}"
                context['data_uploaded'] = False
        else:
            context['upload_error'] = "Error: File tidak valid atau tidak ada file yang dipilih."
            context['data_uploaded'] = False

    elif action == 'load_sheet':
        temp_filepath = session.get('temp_filepath')
        selected_sheet = request.form.get('sheet_name')

        if temp_filepath and selected_sheet and os.path.exists(temp_filepath):
            df = pd.read_excel(temp_filepath, sheet_name=selected_sheet)
            os.remove(temp_filepath)

            unique_id = str(uuid.uuid4())
            internal_filename = f"{unique_id}_{selected_sheet}.csv"
            internal_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], internal_filename)
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            save_dataframe(df, internal_filepath)

            session.pop('temp_filepath', None)
            session['filepath'] = internal_filepath
            context['data_uploaded'] = True
            context['log_message'] = f"Sheet '{selected_sheet}' berhasil dimuat."
        else:
            context['upload_error'] = "Gagal memuat sheet. Silakan upload ulang file."
            context['data_uploaded'] = False
    
    elif action == 'find_issues' and df is not None:
        context['issues_found'] = True
        col_types = {str(i): request.form.get(f'col_type_{i}') for i, col in enumerate(df.columns)}
        context['col_types'] = col_types
        
        symbol_pattern = re.compile(r'[!@#$%^&*()_+<>?:"/\\~`{}\[\]|;\'\.]')
        missing_markers = ['-', 'null', '0', 'kosong', 'na', 'nan', 'none', '']
        
        missing_locations = []
        symbol_locations = []
        contaminated_alpha_locations = []
        contaminated_numeric_locations = []

        context['issues']['duplicates'] = df[df.duplicated(keep=False)].index.tolist()

        for i, col in enumerate(df.columns):
            col_type = col_types.get(str(i))
            for j, val in enumerate(df[col]):
                s_val = str(val).strip()
                if pd.isna(val) or s_val.lower() in missing_markers:
                    context['issues']['missing'].append(f"{j}-{i}")
                    missing_locations.append((j, col))
                    continue
                
                if col_type == 'numeric':
                    if any(char.isalpha() for char in s_val):
                        context['issues']['contaminated_alpha'].append(f"{j}-{i}")
                        contaminated_alpha_locations.append((j, col))
                elif col_type == 'alpha':
                    if any(char.isdigit() for char in s_val):
                        context['issues']['contaminated_numeric'].append(f"{j}-{i}")
                        contaminated_numeric_locations.append((j, col))

                # PERBAIKAN: Jangan cek simbol jika tipe kolom adalah Date
                if col_type != 'date' and isinstance(val, str) and symbol_pattern.search(val):
                    context['issues']['symbols'].append(f"{j}-{i}")
                    symbol_locations.append((j, col))

        log_parts = []
        if context['issues']['duplicates']:
            log_parts.append(f"<b>Data Duplikat:</b> {len(context['issues']['duplicates'])} baris ditemukan.")
        
        log_parts.append(format_issue_log("Data Hilang", missing_locations))
        log_parts.append(format_issue_log("Terkontaminasi Huruf", contaminated_alpha_locations))
        log_parts.append(format_issue_log("Terkontaminasi Angka", contaminated_numeric_locations))
        log_parts.append(format_issue_log("Terkontaminasi Simbol", symbol_locations))

        context['log_message'] = "<br>".join(filter(None, log_parts))
        if not context['log_message']:
            context['log_message'] = "<b>Tidak ada masalah yang ditemukan.</b>"


    if df is not None:
        rows, cols = df.shape
        context['rows'] = rows
        context['cols'] = cols
        context['headers'] = df.columns.tolist()
        data_list = df.fillna('').values.tolist()
        context['data'] = [(row_idx, list(enumerate(row_values))) for row_idx, row_values in enumerate(data_list)]

    return render_template('advanced_cleaner.html', **context)
