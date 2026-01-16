# Declaration of Conformity Generator

A desktop application for generating Declarations of Conformity for multilayer films.

## Requirements

### Software
- Python 3.8+
- wkhtmltopdf (for PDF generation)

### Installing wkhtmltopdf

**Windows:**
1. Download the installer: https://wkhtmltopdf.org/downloads.html  
2. Install it (default path: `C:\Program Files\wkhtmltopdf`)  
3. Add it to PATH or the application will automatically find the installation

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install wkhtmltopdf
```

## Project Installation

1. **Clone / Download the project**

2. **Create a virtual environment:**
```bash
python -m venv venv
```

3. **Activate the environment:**
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## Server Configuration

### 1. Folder structure on the server
On the server `\\192.168.14.14\` create the following structure:
```text
declarations/
├── config/
│   ├── texts_pl.json
│   ├── texts_en.json
│   ├── substances_table.json
│   ├── dual_use_table.json
│   └── laminate_structures.json
├── templates/
│   ├── declaration_tech_pl.html
│   ├── declaration_tech_en.html
│   ├── declaration_bok_pl.html (future)
│   └── declaration_bok_en.html (future)
└── images/
    └── signature.png (optional)
```

### 2. Copy example files
Use the generated sample JSON files and HTML templates:
- `config/*.json` → server  
- `templates/*.html` → server  

### 3. Modify the path (if needed)
If the server path is different, edit `src/config/constants.py`:
```python
SERVER_BASE = Path(r"\\YOUR_PATH\declarations")
```

## Running the application

```bash
python main.py
```

## Project structure

```text
declaration_generator/
├── main.py                          # Entry point
├── requirements.txt
├── README.md
├── src/
│   ├── config/
│   │   └── constants.py            # All constants and paths (REFERENCES)
│   ├── models/
│   │   └── declaration.py          # Data model
│   ├── services/
│   │   ├── data_loader.py          # JSON loader (Singleton)
│   │   └── pdf_generator.py        # PDF/HTML generation
│   └── gui/
│       ├── main_window.py          # Main window
│       ├── tech_declaration_view.py # Generation view
│       └── data_editor_view.py     # Data editor
└── output/                         # Generated files (local)
```

## Usage

### Generating a technical declaration
1. Start the application  
2. Select language (Polish / English)  
3. Enter product name  
4. Select structure materials (e.g. OPA + PE)  
5. Click **“Generate PDF”**

### Editing input data
1. Click **“Input Data Editor”**  
2. Select a file to edit:
   - Substances table (section 6)  
   - Dual use table (section 8)  
   - Laminate structures  
3. Edit the data in the table  
4. Click **“Save”**

**WARNING:** Changes are saved on the server and affect all users!

### Refreshing data
Click **“🔄 Refresh data from server”** to reload data from the server without restarting the application.

## Key implementation principles

### Reference pattern
- **All paths** in `src/config/constants.py`  
- **All texts** in JSON files (`texts_pl.json`, `texts_en.json`)  
- **No hardcoded strings** in the code  

### DataLoader Singleton
- Automatic data caching  
- Centralized load/save management  
- `clear_cache()` method to force reload  

### Laminate structure mapping
The structure is a key in `laminate_structures.json`:
```json
"OPA/PE": {
  "substances": [...],
  "dual_use": [...]
}
```

## Future extensions

### Customer Service version (with customer data)
- Connection to production database (SQLAlchemy)  
- Fetching customer and product data  
- Automatic filling of production batches  

### Additional features
- Export to DOCX  
- History of generated documents  
- Digital signatures  
- Multi-threading for large volumes  

## Troubleshooting

### Error: “Cannot connect to server”
- Check network connection  
- Verify the path in `constants.py`  
- Check permissions for the network folder  

### Error: “wkhtmltopdf not found”
- Install wkhtmltopdf  
- Windows: add it to PATH or check if it exists in `C:\Program Files\wkhtmltopdf\bin`

### PDF is not generated
- Check if HTML is generated (`👁️ HTML Preview`)  
- If HTML works, the problem is with wkhtmltopdf  
- Check error logs  

## 📞 Contact
- GitHub: @Serafin06

