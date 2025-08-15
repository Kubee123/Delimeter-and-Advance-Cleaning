# Impor library yang diperlukan
import os
import webbrowser
from threading import Timer
from flask import Flask

# Impor "Blueprint" (cetak biru halaman) dari folder views
from views.detector_view import detector_bp
from views.delimiter_view import delimiter_bp

def create_app():
    """Membuat dan mengkonfigurasi instance aplikasi Flask."""
    app = Flask(__name__)

    # Konfigurasi
    UPLOAD_FOLDER = 'uploads'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
    app.config['SECRET_KEY'] = 'a_truly_new_and_secret_key_for_a_clean_session'

    # Pastikan folder upload ada
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Daftarkan blueprint ke aplikasi
    app.register_blueprint(detector_bp)
    app.register_blueprint(delimiter_bp)

    return app

# Buat aplikasi
app = create_app()

# --- FUNGSI RUN ---
def open_app():
    """Membuka tab browser untuk aplikasi lokal."""
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1, open_app).start()
    app.run(port=5000, debug=False)
