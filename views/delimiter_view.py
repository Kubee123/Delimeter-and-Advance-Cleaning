from flask import Blueprint, request, render_template

# Membuat Blueprint untuk halaman ini
delimiter_bp = Blueprint('delimiter', __name__)

@delimiter_bp.route('/delimiter-tool', methods=['GET', 'POST'])
def delimiter_tool():
    """Halaman untuk alat delimiter."""
    # Daftar simbol untuk ditampilkan di dropdown
    symbol_list = list("~!@#$%^&*()_+-={}[]:\";',./<>?\|")

    context = {
        'processed_query': '',
        'original_query': '',
        'selected_delimiter': '', # Untuk dropdown pertama
        'selected_symbol': '',    # Untuk dropdown kedua
        'active_page': 'delimiter',
        'symbol_list': symbol_list
    }

    if request.method == 'POST':
        action = request.form.get('action')
        context['original_query'] = request.form.get('query_input', '')
        
        # Ambil pilihan dari setiap dropdown secara terpisah
        delimiter_choice = request.form.get('delimiter_choice', '')
        symbol_choice = request.form.get('symbol_choice', '')
        
        # Simpan pilihan untuk ditampilkan kembali di halaman
        context['selected_delimiter'] = delimiter_choice
        context['selected_symbol'] = symbol_choice
        
        # Tentukan separator mana yang akan digunakan untuk proses
        # Pilihan delimiter utama lebih diprioritaskan
        separator = delimiter_choice or symbol_choice

        if action == 'process_delimiter' and context['original_query'] and separator:
            original_text = context['original_query']
            
            # Selalu pecah input menjadi kata-kata individual terlebih dahulu
            words = original_text.split()
            
            # Tentukan karakter join yang sebenarnya
            # Nilai dari HTML untuk newline adalah 'newline', kita perlu mengubahnya menjadi karakter newline '\n'
            join_char = '\n' if separator == 'newline' else separator
            
            # Gabungkan kembali kata-kata dengan separator yang dipilih
            context['processed_query'] = join_char.join(words)
            
    return render_template('delimiter_tool.html', **context)
