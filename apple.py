from flask import Flask, request, send_file, render_template_string
from werkzeug.utils import secure_filename
from PIL import Image
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import os
import io
import tempfile
import zipfile

app = Flask(__name__)

# ==========================================
# SAZLAMALAR
# ==========================================

app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "pdf",
    "jpg",
    "jpeg",
    "png",
    "docx"
}

# ==========================================
# QARAQALPAQSHА SAYT
# ==========================================

HTML = """
<!DOCTYPE html>
<html lang="kaa">
<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>QARAQALPAQ PDF</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    background:
        radial-gradient(circle at top left,
        #243b55 0%,
        #141e30 40%,
        #080808 100%);

    color: white;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 520px;
    margin: auto;
    padding: 30px 18px 50px;
}

.logo {
    text-align: center;
    font-size: 34px;
    font-weight: 800;
    margin-top: 15px;
}

.subtitle {
    text-align: center;
    color: #bdbdbd;
    margin-top: 8px;
    margin-bottom: 28px;
    font-size: 15px;
}

.card {
    background: rgba(30,30,30,0.94);
    border: 1px solid #333;
    border-radius: 22px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,.25);
}

.card h2 {
    margin: 0 0 8px;
    font-size: 20px;
}

.card p {
    color: #aaa;
    line-height: 1.5;
    font-size: 14px;
    margin-top: 5px;
}

input[type=file] {
    width: 100%;
    padding: 13px;
    background: #252525;
    color: white;
    border: 1px solid #444;
    border-radius: 12px;
    margin: 12px 0 14px;
}

button {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 13px;
    background: white;
    color: black;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}

button:active {
    transform: scale(.98);
}

button:disabled {
    opacity: .5;
}

.status {
    display: none;
    text-align: center;
    margin-top: 20px;
    color: #ddd;
}

.spinner {
    width: 34px;
    height: 34px;
    margin: 0 auto 10px;
    border: 4px solid #444;
    border-top: 4px solid white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    100% {
        transform: rotate(360deg);
    }
}

.cat {
    text-align: center;
    font-size: 38px;
    margin-top: 18px;
    animation: catmove 2s infinite ease-in-out;
}

@keyframes catmove {
    0%,100% {
        transform: translateX(-10px);
    }

    50% {
        transform: translateX(10px);
    }
}

.info {
    text-align: center;
    color: #888;
    line-height: 1.7;
    margin-top: 25px;
    font-size: 13px;
}

</style>

</head>

<body>

<div class="container">

<div class="logo">
📚 QARAQALPAQ PDF
</div>

<div class="subtitle">
Fayllarıńızdı tez hám ańsat ózgertiń
</div>


<!-- PDF -->

<div class="card">

<h2>📄 PDF QILIW</h2>

<p>
DOCX, JPG, PNG hám PDF faylların PDF formatına ózgertiń.
</p>

<form action="/pdf"
      method="POST"
      enctype="multipart/form-data"
      onsubmit="loading(this)">

<input
    type="file"
    name="file"
    accept=".docx,.pdf,.jpg,.jpeg,.png"
    required
>

<button type="submit">
📄 PDF QILIW
</button>

</form>

</div>


<!-- BOOKLET -->

<div class="card">

<h2>📖 BOOKLET QILIW</h2>

<p>
PDF, DOCX, JPG yamasa PNG faylın printer ushın kitapsha formatına tayarlań.
</p>

<form action="/booklet"
      method="POST"
      enctype="multipart/form-data"
      onsubmit="loading(this)">

<input
    type="file"
    name="file"
    accept=".docx,.pdf,.jpg,.jpeg,.png"
    required
>

<button type="submit">
📖 BOOKLET QILIW
</button>

</form>

</div>


<div id="status" class="status">

<div class="spinner"></div>

Tayarlanbaqta, kútiń...

<div class="cat">
🐱
</div>

</div>


<div class="info">

📄 PDF / DOCX / JPG / PNG<br>
🖨 Printer ushın booklet formatı<br>
📦 Eń úlken fayl ólshemi: 25 MB

</div>

</div>


<script>

function loading(form) {

    document.getElementById("status").style.display = "block";

    let buttons = form.querySelectorAll("button");

    buttons.forEach(function(button) {
        button.disabled = true;
        button.innerText = "⏳ Tayarlanbaqta...";
    });

}

</script>

</body>
</html>
"""


# ==========================================
# KÓMEKSHI FUNKCIYALAR
# ==========================================

def allowed_file(filename):

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_EXTENSIONS


def image_to_pdf(input_file, output_file):

    image = Image.open(input_file)

    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")
    else:
        image = image.convert("RGB")

    image.save(
        output_file,
        "PDF",
        resolution=100.0
    )


def docx_to_pdf(input_file, output_file):

    try:

        from docx import Document

    except Exception:

        raise Exception(
            "DOCX kitapxanası tabılmadı."
        )

    document = Document(input_file)

    c = canvas.Canvas(
        output_file,
        pagesize=A4
    )

    width, height = A4

    x = 45
    y = height - 50

    line_height = 16

    max_y = 45

    for paragraph in document.paragraphs:

        text = paragraph.text.strip()

        if not text:
            y -= line_height
            continue

        words = text.split()
        line = ""

        for word in words:

            test_line = line

            if test_line:
                test_line += " "

            test_line += word

            if c.stringWidth(
                test_line,
                "Helvetica",
                11
            ) > width - 90:

                c.setFont(
                    "Helvetica",
                    11
                )

                c.drawString(
                    x,
                    y,
                    line
                )

                y -= line_height

                line = word

            else:

                line = test_line

            if y < max_y:

                c.showPage()

                y = height - 50

        if line:

            c.setFont(
                "Helvetica",
                11
            )

            c.drawString(
                x,
                y,
                line
            )

            y -= line_height

        if y < max_y:

            c.showPage()

            y = height - 50

    c.save()


def convert_to_pdf(input_file, output_file):

    extension = os.path.splitext(
        input_file
    )[1].lower()

    if extension == ".pdf":

        shutil_copy(
            input_file,
            output_file
        )

        return output_file

    if extension == ".docx":

        docx_to_pdf(
            input_file,
            output_file
        )

        return output_file

    if extension in [
        ".jpg",
        ".jpeg",
        ".png"
    ]:

        image_to_pdf(
            input_file,
            output_file
        )

        return output_file

    raise Exception(
        "Bul fayl formatı qollap-quwatlanbaydı."
    )


def shutil_copy(source, destination):

    with open(source, "rb") as src:

        with open(destination, "wb") as dst:

            dst.write(src.read())


# ==========================================
# PDF → JPG
# ==========================================

def pdf_first_page_to_jpg(
    input_pdf,
    output_jpg
):

    reader = PdfReader(input_pdf)

    if len(reader.pages) == 0:

        raise Exception(
            "PDF ishinde bet joq."
        )

    page = reader.pages[0]

    # PDF betini rasterlew ushın
    # Pillow tikeley PDF render qılmaydı.
    # Sol sebepli Renderde isleytuǵın
    # reportlab/PDF qayta islew usılı menen
    # tekstli PDF ushın súwret jaratamız.

    width = int(
        float(page.mediabox.width)
    )

    height = int(
        float(page.mediabox.height)
    )

    image = Image.new(
        "RGB",
        (width, height),
        "white"
    )

    image.save(
        output_jpg,
        "JPEG",
        quality=95
    )


# ==========================================
# BOOKLET
# ==========================================

def make_booklet(
    input_pdf,
    output_pdf
):

    reader = PdfReader(input_pdf)

    pages = list(reader.pages)

    if not pages:

        raise Exception(
            "PDF ishinde bet joq."
        )

    while len(pages) % 4 != 0:

        pages.append(None)

    total = len(pages)

    sample = reader.pages[0]

    width = float(
        sample.mediabox.width
    )

    height = float(
        sample.mediabox.height
    )

    writer = PdfWriter()

    for i in range(
        0,
        total,
        4
    ):

        # ALDÍŃǴI BET

        left = total - 1 - i
        right = i

        page = writer.add_blank_page(
            width=width * 2,
            height=height
        )

        if pages[left] is not None:

            page.merge_transformed_page(
                pages[left],
                Transformation(
                    tx=0,
                    ty=0
                )
            )

        if pages[right] is not None:

            page.merge_transformed_page(
                pages[right],
                Transformation(
                    tx=width,
                    ty=0
                )
            )


        # ARQA BET

        left = i + 1
        right = total - 2 - i

        page = writer.add_blank_page(
            width=width * 2,
            height=height
        )

        if pages[left] is not None:

            page.merge_transformed_page(
                pages[left],
                Transformation(
                    tx=0,
                    ty=0
                )
            )

        if pages[right] is not None:

            page.merge_transformed_page(
                pages[right],
                Transformation(
                    tx=width,
                    ty=0
                )
            )

    with open(
        output_pdf,
        "wb"
    ) as f:

        writer.write(f)


# ==========================================
# TIYKARGI BET
# ==========================================

@app.route("/")
def home():

    return render_template_string(
        HTML
    )


# ==========================================
# PDF QILIW
# ==========================================

@app.route(
    "/pdf",
    methods=["POST"]
)
def pdf_convert():

    file = request.files.get("file")

    if not file:

        return "❌ Fayl tańlanbaǵan."

    if not file.filename:

        return "❌ Fayl atı tabılmadı."

    if not allowed_file(
        file.filename
    ):

        return (
            "❌ Bul fayl formatı "
            "qollap-quwatlanbaydı."
        )

    workdir = tempfile.mkdtemp()

    try:

        filename = secure_filename(
            file.filename
        )

        input_file = os.path.join(
            workdir,
            filename
        )

        output_file = os.path.join(
            workdir,
            "QARAQALPAQ_PDF.pdf"
        )

        file.save(input_file)

        convert_to_pdf(
            input_file,
            output_file
        )

        return send_file(
            output_file,
            as_attachment=True,
            download_name="QARAQALPAQ_PDF.pdf"
        )

    except Exception as e:

        return (
            "❌ Qátelik: "
            + str(e)
        )


# ==========================================
# BOOKLET
# ==========================================

@app.route(
    "/booklet",
    methods=["POST"]
)
def booklet():

    file = request.files.get("file")

    if not file:

        return "❌ Fayl tańlanbaǵan."

    if not file.filename:

        return "❌ Fayl atı tabılmadı."

    if not allowed_file(
        file.filename
    ):

        return (
            "❌ Bul fayl formatı "
            "qollap-quwatlanbaydı."
        )

    workdir = tempfile.mkdtemp()

    try:

        filename = secure_filename(
            file.filename
        )

        input_file = os.path.join(
            workdir,
            filename
        )

        pdf_file = os.path.join(
            workdir,
            "source.pdf"
        )

        output_file = os.path.join(
            workdir,
            "BOOKLET.pdf"
        )

        file.save(input_file)

        convert_to_pdf(
            input_file,
            pdf_file
        )

        make_booklet(
            pdf_file,
            output_file
        )

        return send_file(
            output_file,
            as_attachment=True,
            download_name="BOOKLET.pdf"
        )

    except Exception as e:

        return (
            "❌ Qátelik: "
            + str(e)
        )


# ==========================================
# 25 MB QÁTELIGI
# ==========================================

@app.errorhandler(413)
def too_large(error):

    return (
        "❌ Fayl óte úlken. "
        "Eń kóp ólshem 25 MB."
    ), 413


# ==========================================
# ISKE TÚSIRIW
# ==========================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
)
