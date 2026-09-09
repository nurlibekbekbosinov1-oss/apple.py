from flask import Flask, request, send_file, render_template_string
import os
import tempfile
import subprocess
import shutil
from pypdf import PdfReader, PdfWriter

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Kitapsha</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #101010;
    color: white;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 520px;
    margin: auto;
    padding: 35px 20px;
}

h1 {
    text-align: center;
    font-size: 32px;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    color: #aaa;
    margin-bottom: 30px;
}

.card {
    background: #1c1c1c;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 20px;
}

.card h2 {
    margin-top: 0;
    font-size: 20px;
}

input[type=file] {
    width: 100%;
    padding: 12px;
    background: #292929;
    color: white;
    border-radius: 10px;
    border: 1px solid #444;
    margin: 12px 0 16px;
}

button {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 12px;
    background: white;
    color: black;
    font-size: 17px;
    font-weight: bold;
}

button:active {
    transform: scale(0.98);
}

.info {
    text-align: center;
    color: #888;
    line-height: 1.6;
    margin-top: 25px;
}

</style>
</head>

<body>

<div class="container">

<h1>📚 KITAPSHA</h1>

<div class="subtitle">
Faylıńızdı kerekli formatqa ózgertiń
</div>


<div class="card">

<h2>🖼 1. JPG qa ózgertiw</h2>

<form action="/jpg" method="POST" enctype="multipart/form-data">

<input
    type="file"
    name="file"
    accept=".doc,.docx,.pdf,.jpg,.jpeg,.png"
    required
>

<button type="submit">
🖼 JPG qa ózgertiw
</button>

</form>

</div>


<div class="card">

<h2>📖 2. Kitapsha qılıw</h2>

<form action="/booklet" method="POST" enctype="multipart/form-data">

<input
    type="file"
    name="file"
    accept=".doc,.docx,.pdf,.jpg,.jpeg,.png"
    required
>

<button type="submit">
📖 Kitapsha qılıw
</button>

</form>

</div>


<div class="info">

📄 DOC / DOCX / PDF / JPG / PNG<br>
🖨 Printer ushın kitapsha formatı<br>
⚙️ Betler avtomatik túrde esaplanadı

</div>

</div>

</body>
</html>
"""


# ==========================================
# TIYKARGI BET
# ==========================================

@app.route("/")
def home():

    return render_template_string(HTML)


# ==========================================
# OFFICE -> PDF
# ==========================================

def convert_to_pdf(input_file, workdir):

    extension = os.path.splitext(input_file)[1].lower()

    if extension == ".pdf":
        return input_file

    output = subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            workdir,
            input_file
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    pdf_file = os.path.join(
        workdir,
        os.path.splitext(
            os.path.basename(input_file)
        )[0] + ".pdf"
    )

    if not os.path.exists(pdf_file):

        raise Exception(
            "DOC/DOCX faylın PDFqa ózgertiw múmkin bolmadı."
        )

    return pdf_file


# ==========================================
# IMAGE -> PDF
# ==========================================

def image_to_pdf(input_file, output_file):

    try:

        subprocess.run(
            [
                "convert",
                input_file,
                output_file
            ],
            check=True
        )

    except Exception:

        raise Exception(
            "Súwretti PDFqa ózgertiw ushın "
            "ImageMagick kerek."
        )


# ==========================================
# PDF -> BOOKLET
# ==========================================

def make_booklet(input_pdf, output_pdf):

    reader = PdfReader(input_pdf)

    pages = list(reader.pages)

    original_pages = len(pages)

    if original_pages == 0:
        raise Exception("PDF ishinde bet joq.")

    # 4 ke eselik etemiz
    while len(pages) % 4 != 0:
        pages.append(None)

    total = len(pages)

    sample = reader.pages[0]

    width = float(sample.mediabox.width)
    height = float(sample.mediabox.height)

    writer = PdfWriter()

    # ======================================
    # BOOKLET TÁRTIBI
    # ======================================

    for i in range(0, total, 4):

        # -------------------------------
        # ALDÍŃǴI BETI
        # -------------------------------

        left = total - 1 - i
        right = i

        page = writer.add_blank_page(
            width=width * 2,
            height=height
        )

        if pages[left] is not None:

            page.merge_translated_page(
                pages[left],
                0,
                0
            )

        if pages[right] is not None:

            page.merge_translated_page(
                pages[right],
                width,
                0
            )

        # -------------------------------
        # ARQA BETI
        # -------------------------------

        left = i + 1
        right = total - 2 - i

        page = writer.add_blank_page(
            width=width * 2,
            height=height
        )

        if pages[left] is not None:

            page.merge_translated_page(
                pages[left],
                0,
                0
            )

        if pages[right] is not None:

            page.merge_translated_page(
                pages[right],
                width,
                0
            )

    with open(output_pdf, "wb") as f:

        writer.write(f)


# ==========================================
# JPG TÚYMESI
# ==========================================

@app.route("/jpg", methods=["POST"])
def jpg_convert():

    file = request.files.get("file")

    if not file:

        return "Fayl tańlanbaǵan."

    filename = file.filename

    if not filename:

        return "Fayl atı tabılmadı."

    workdir = tempfile.mkdtemp()

    try:

        input_file = os.path.join(
            workdir,
            filename
        )

        file.save(input_file)

        extension = os.path.splitext(
            filename
        )[1].lower()

        # JPG bolsa
        if extension in [".jpg", ".jpeg"]:

            return send_file(
                input_file,
                as_attachment=True,
                download_name="result.jpg"
            )

        # PNG
        if extension == ".png":

            output = os.path.join(
                workdir,
                "result.jpg"
            )

            subprocess.run(
                [
                    "convert",
                    input_file,
                    output
                ],
                check=True
            )

            return send_file(
                output,
                as_attachment=True,
                download_name="result.jpg"
            )

        # DOC/DOCX/PDF
        pdf_file = convert_to_pdf(
            input_file,
            workdir
        )

        # PDF -> JPG
        prefix = os.path.join(
            workdir,
            "page"
        )

        subprocess.run(
            [
                "pdftoppm",
                "-jpeg",
                "-f",
                "1",
                "-singlefile",
                pdf_file,
                prefix
            ],
            check=True
        )

        output = prefix + ".jpg"

        if not os.path.exists(output):

            raise Exception(
                "JPG jaratılmadı."
            )

        return send_file(
            output,
            as_attachment=True,
            download_name="result.jpg"
        )

    except Exception as e:

        return "❌ Qátelik: " + str(e)

    finally:

        # Flask juwaptı jibergennen keyin
        # waqıtsha fayllardı óshiriwdi
        # sistema basqaradı.
        pass


# ==========================================
# KITAPSHA TÚYMESI
# ==========================================

@app.route("/booklet", methods=["POST"])
def booklet():

    file = request.files.get("file")

    if not file:

        return "Fayl tańlanbaǵan."

    filename = file.filename

    if not filename:

        return "Fayl atı tabılmadı."

    workdir = tempfile.mkdtemp()

    try:

        input_file = os.path.join(
            workdir,
            filename
        )

        file.save(input_file)

        extension = os.path.splitext(
            filename
        )[1].lower()

        # -------------------------------
        # PDF
        # -------------------------------

        if extension == ".pdf":

            pdf_file = input_file

        # -------------------------------
        # DOC / DOCX
        # -------------------------------

        elif extension in [".doc", ".docx"]:

            pdf_file = convert_to_pdf(
                input_file,
                workdir
            )

        # -------------------------------
        # JPG / PNG
        # -------------------------------

        elif extension in [
            ".jpg",
            ".jpeg",
            ".png"
        ]:

            pdf_file = os.path.join(
                workdir,
                "image.pdf"
            )

            image_to_pdf(
                input_file,
                pdf_file
            )

        else:

            return (
                "❌ Bul fayl formatı "
                "qollap-quwatlanbaydı."
            )

        # -------------------------------
        # BOOKLET
        # -------------------------------

        output_file = os.path.join(
            workdir,
            "KITAPSHA.pdf"
        )

        make_booklet(
            pdf_file,
            output_file
        )

        return send_file(
            output_file,
            as_attachment=True,
            download_name="KITAPSHA.pdf"
        )

    except Exception as e:

        return "❌ Qátelik: " + str(e)

    finally:

        pass


# ==========================================
# ISKE TÚSIRIW
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
  )
