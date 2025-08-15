import pandas as pd

ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_dataframe(filepath):
    """Membaca file CSV internal yang disimpan di server."""
    return pd.read_csv(filepath, low_memory=False)

def save_dataframe(df, filepath):
    """Menyimpan DataFrame ke file CSV internal di server."""
    df.to_csv(filepath, index=False)
