"""
===========================================================
 ClarifAI - AI-Powered Interactive Book Explainer
===========================================================

Description:
    ClarifAI takes a plain text book/document and transforms it
    into an interactive, AI-annotated reading experience.

    Features:
    - Upload a .txt file and parse it into structured chapters.
    - Automatically generate AI-powered explanations for each paragraph.
    - Interactive web reader with chapter navigation and explanation popups.
    - Download the entire annotated book as a styled HTML bundle (.zip).
    - Dark theme UI with support for embedded images.

Tech Stack:
    - Flask (Python web framework)
    - Flask-Session (server-side session handling)
    - Google Generative AI (Gemini models for explanations)
    - HTML/CSS (dark theme UI for output)

Author:
    Sambana Tirumalasai

Course:
    Harvard CS50x – Final Project

Repository:
    https://github.com/[your-username]/clarif_ai

Version:
    1.0.0
"""

# === Standard library imports ===
import os
import re
import io
import zipfile
import time
import threading
import html
import uuid

# === Third-party imports ===
from flask import Flask, render_template, request, session, redirect, flash, Response, jsonify
from flask_session import Session
from werkzeug.utils import secure_filename
import google.generativeai as genai

# === Flask App Configuration ===
app = Flask(__name__)

# Security & session config
app.config["SECRET_KEY"] = os.urandom(24)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Uploads folder (ensure it exists)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# === Task Management (Background Processing) ===
tasks = {}                      # In-memory mapping: task_id -> status/progress/data
tasks_lock = threading.Lock()   # Lock to synchronize access to `tasks`


# === Helper functions ===
def slugify(text):
    """
    Convert a string into a URL/ID-friendly slug.
    Example: "Chapter 1: The Beginning?" -> "chapter_1_the_beginning"
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)      # remove non-alphanumeric
    text = re.sub(r"[\s-]+", "_", text).strip("_")  # replace spaces/hyphens with underscore
    return text


def convert_txt_to_dict(filepath):
    """
    Parse a plain-text file into a structured dict:
    { "Chapter Title": [ {'type':'text','content':...}, {'type':'image','url':...}, ... ], ... }

    Rules:
    - Paragraphs separated by blank lines.
    - Chapter markers: { - Chapter Title - }  (e.g. "{-Chapter 1-}")
    - Image markers: [IMAGE: https://example.com/image.jpg]
    """
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            content = fh.read().replace("\r\n", "\n").strip()

        if not content:
            return {}

        # Split into blocks by blank lines, preserve trimmed blocks
        blocks = [p.strip() for p in content.split("\n\n") if p.strip()]

        chapters = {"Introduction": []}
        current_chapter_title = "Introduction"

        image_regex = r"\[IMAGE:\s*(https?://[^\s\]]+)\s*\]"
        chapter_regex = r"\{-(.+?)-\}"

        for block in blocks:
            # Use search so leading/trailing whitespace doesn't prevent detection
            chapter_match = re.search(chapter_regex, block)
            image_match = re.search(image_regex, block, re.IGNORECASE)

            if chapter_match:
                # start a new chapter
                current_chapter_title = chapter_match.group(1).strip()
                if current_chapter_title not in chapters:
                    chapters[current_chapter_title] = []
            elif image_match:
                # append image entry
                chapters[current_chapter_title].append({
                    "type": "image",
                    "url": image_match.group(1)
                })
            else:
                # normal text paragraph
                chapters[current_chapter_title].append({
                    "type": "text",
                    "content": block
                })

        return chapters

    except Exception as e:
        # Log and return None on unexpected error
        print(f"Error parsing file: {e}")
        return None


def get_explanation(chat_session, paragraph, user_name):
    """
    Send a single message to Gemini (via the given chat_session) to request
    an explanation of the paragraph tailored to `user_name`.

    Returns the explanation string; on failure returns a safe fallback.
    """
    try:
        # Prompting strategy is minimal here; consider improving for better results
        response = chat_session.send_message(f'Explain this to {user_name}: "{paragraph}"')
        explanation = response.text.strip()
        # small buffer to avoid accidental rate spikes; adjust or remove in production
        time.sleep(1.5)
        return explanation
    except Exception as e:
        print(f"API Error: {e}")
        return "[Could not get an explanation.]"


def create_book_zip(book_data, base_filename):
    """
    Build a zip archive (bytes) that contains:
    - <base_filename>.html : The main annotated book with dark styling + TOC toggle
    - book_requirements/exp_<n>.html : Individual explanation pages for each paragraph

    `book_data` format:
    { "Chapter Title": [ {type:'text', 'original':..., 'explanation':...}, {type:'image','url':...}, ... ], ... }
    """
    if isinstance(base_filename, tuple):
        base_filename = base_filename[0]

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        main_html_content = ""
        para_id = 0
        explanation_folder = "book_requirements"

        # Build TOC HTML
        toc_html = "<h3>Table of Contents</h3><ul>"
        for chapter_title in book_data.keys():
            chapter_id = slugify(chapter_title)
            toc_html += f'<li><a href="#{chapter_id}">{html.escape(chapter_title)}</a></li>'
        toc_html += "</ul>"

        # Build main content and per-paragraph explanation files
        for chapter_title, content_items in book_data.items():
            chapter_id = slugify(chapter_title)
            main_html_content += f"<h2 class='chapter-title' id='{chapter_id}'>{html.escape(chapter_title)}</h2>\n"

            for item in content_items:
                if item.get("type") == "text":
                    explanation_path = f"{explanation_folder}/exp_{para_id}.html"
                    # Main page paragraph with link to explanation
                    main_html_content += f"""
                        <div class="paragraph-container">
                            <p>{html.escape(item.get('original',''))}</p>
                            <a href="{explanation_path}" target="_blank" class="explain-button" aria-label="Explain paragraph">?</a>
                        </div>
                    """
                    # Individual explanation HTML
                    explanation_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Explanation</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Lato:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
  <style>
    html {{ color-scheme: dark; }}
    body {{ background:#1a1a1d; color:#c5c6c7; font-family:'Lato',sans-serif; padding:2rem; display:flex; justify-content:center; align-items:center; min-height:100vh; }}
    .card {{ background:#25282d; border-left:5px solid #c9b037; border-radius:8px; padding:2rem; max-width:800px; box-shadow:0 10px 25px rgba(0,0,0,0.2); }}
    .card p {{ text-indent:2em; margin:0 0 1em 0; }}
  </style>
</head>
<body>
  <div class="card">
    <p>{html.escape(item.get('explanation','')).replace(chr(10), '</p><p>')}</p>
  </div>
</body>
</html>
"""
                    # Write to zip
                    zip_file.writestr(explanation_path, explanation_html)
                    para_id += 1

                elif item.get("type") == "image":
                    # Insert the remote image (URL) into the main page
                    main_html_content += f'<div class="image-container"><img src="{html.escape(item.get("url",""))}" alt="Embedded image"></div>\n'

        # Main book HTML with TOC toggle button and styling
        book_html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(base_filename.replace('_',' ').title())}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
  <style>
    html {{ color-scheme: dark; }}
    body {{ background:#121212; color:#e0e0e0; font-family:'Merriweather',Georgia,serif; font-size:20px; line-height:1.7; padding:3rem 2rem; max-width:800px; margin:auto; }}
    .main-title {{ font-family:'Algerian',sans-serif; font-size:3.5rem; color:#d4af37; text-align:center; margin-bottom:4rem; text-shadow:2px 2px 4px #000; }}
    .chapter-title {{ font-family:'Algerian',sans-serif; font-size:2.5rem; color:#d4af37; text-align:center; margin-top:3rem; margin-bottom:2rem; text-shadow:1px 1px 3px #000; scroll-margin-top:2rem; }}
    .paragraph-container {{ display:flex; align-items:flex-start; gap:1rem; margin-bottom:1rem; }}
    .paragraph-container p {{ text-indent:2em; margin:0; flex-grow:1; }}
    .explain-button {{ flex-shrink:0; margin-left:auto; background:transparent; color:#555; border:1px solid #444; border-radius:50%; width:28px; height:28px; display:flex; align-items:center; justify-content:center; font-family:'Lato',sans-serif; font-size:1rem; font-weight:700; text-decoration:none; cursor:pointer; transition:all .2s ease-in-out; margin-top:4px; }}
    .explain-button:hover {{ background:#c9b037; color:#121212; border-color:#f6e27a; }}
    .image-container {{ margin:2.5em 0; }}
    img {{ max-width:100%; height:auto; border-radius:8px; display:block; margin:auto; }}

    /* TOC styles */
    #toc-toggle-btn {{ position:fixed; top:20px; right:20px; z-index:1001; padding:10px 15px; font-family:'Lato',sans-serif; font-weight:bold; background:#d4af37; color:#121212; border:none; border-radius:8px; cursor:pointer; box-shadow:0 4px 10px rgba(0,0,0,0.5); }}
    #toc-sidebar {{ display:none; position:fixed; top:80px; right:20px; width:220px; background:#1e1e1e; padding:1.5rem; border-radius:8px; border:1px solid #444; box-shadow:0 4px 15px rgba(0,0,0,0.4); font-family:'Lato',sans-serif; z-index:1000; }}
    #toc-sidebar h3 {{ margin-top:0; font-size:1.2rem; color:#d4af37; border-bottom:1px solid #555; padding-bottom:0.5rem; }}
    #toc-sidebar ul {{ list-style:none; padding-left:0; margin-bottom:0; max-height:60vh; overflow-y:auto; }}
    #toc-sidebar li {{ margin-bottom:0.75em; }}
    #toc-sidebar a {{ color:#c5c6c7; text-decoration:none; font-size:0.9rem; transition:color .2s; }}
    #toc-sidebar a:hover {{ color:#f6e27a; }}
    @media (max-width:1200px) {{ #toc-sidebar, #toc-toggle-btn {{ display:none; }} }}
  </style>
</head>
<body>
  <button id="toc-toggle-btn" aria-expanded="false">Contents</button>
  <div id="toc-sidebar">{toc_html}</div>

  <h1 class="main-title">{html.escape(base_filename.replace('_',' ').title())}</h1>

  {main_html_content}

  <script>
    // Toggle the Table of Contents sidebar
    document.getElementById('toc-toggle-btn').addEventListener('click', () => {{
      const toc = document.getElementById('toc-sidebar');
      const btn = document.getElementById('toc-toggle-btn');
      const isVisible = toc.style.display === 'block';
      toc.style.display = isVisible ? 'none' : 'block';
      btn.setAttribute('aria-expanded', !isVisible);
    }});

    // Smooth scroll behaviour for TOC links
    document.querySelectorAll('#toc-sidebar a').forEach(anchor => {{
      anchor.addEventListener('click', function (e) {{
        e.preventDefault();
        const targetElement = document.querySelector(this.getAttribute('href'));
        if (targetElement) {{
          targetElement.scrollIntoView({{ behavior: 'smooth' }});
        }}
      }});
    }});
  </script>
</body>
</html>
"""
        zip_file.writestr(f"{base_filename}.html", book_html_template)

    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def background_explanation_task(task_id, session_data):
    """
    Background worker to:
    - parse uploaded file,
    - call the generative AI for each paragraph,
    - update task progress in the global tasks dict.
    """
    filepath = session_data.get("filepath")
    user_name = session_data.get("user_name")
    api_key = session_data.get("api_key")

    def update_status(status, progress=None, message=None, data=None):
        with tasks_lock:
            tasks[task_id].update({
                "status": status,
                "progress": progress,
                "message": message,
                "data": data
            })

    # Convert file to structured book dict
    initial_book_data = convert_txt_to_dict(filepath)
    if not initial_book_data:
        update_status("failed", message="Failed to parse book file.")
        return

    # Count paragraphs to compute progress
    total_paragraphs = sum(
        1 for items in initial_book_data.values() for item in items if item.get("type") == "text"
    )
    if total_paragraphs == 0:
        update_status("complete", progress=100, data=initial_book_data)
        return

    # Configure GenAI client and model
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("models/gemini-1.5-pro")
    except Exception as e:
        update_status("failed", message=f"API Configuration Error: {e}")
        return

    enriched_book_data = {}
    paragraphs_processed = 0

    for chapter_title, content_items in initial_book_data.items():
        enriched_book_data[chapter_title] = []
        chat = model.start_chat()
        for item in content_items:
            if item.get("type") == "text":
                explanation = get_explanation(chat, item.get("content", ""), user_name)
                enriched_book_data[chapter_title].append({
                    "type": "text",
                    "original": item.get("content", ""),
                    "explanation": explanation
                })
                paragraphs_processed += 1
                # Update progress (integer percentage)
                update_status("processing", progress=int((paragraphs_processed / total_paragraphs) * 100))
            else:
                # for images and other items, preserve as-is
                enriched_book_data[chapter_title].append(item)

    # Finalize
    update_status("complete", progress=100, data=enriched_book_data)


# === Routes ===
@app.route("/")
def index():
    """Landing page — clears any session state and shows home."""
    session.clear()
    return render_template("index.html")


@app.route("/instructions")
def instructions():
    """Render instructions page describing usage."""
    return render_template("instructions.html")


@app.route("/upload_page")
def upload_page():
    """Render upload form where users submit name, API key, and .txt file."""
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload():
    """
    Handle upload POST:
    - validate presence of user_name, api_key and file
    - do a minimal API-key check
    - save the uploaded file securely
    - store required info in session for background processing
    """
    user_name = request.form.get("user_name")
    api_key = request.form.get("api_key")
    file = request.files.get("book_file")

    if not all([user_name, api_key, file, getattr(file, "filename", "")]):
        flash("All fields are required.")
        return redirect("/upload_page")

    # Minimal validation of the API key (small API call). Keep this light to avoid costs.
    try:
        genai.configure(api_key=api_key)
        # A tiny request to validate credentials — adjust if you have a dedicated endpoint for validation
        genai.GenerativeModel("models/gemini-1.5-flash").generate_content("Hello", generation_config={"max_output_tokens": 1})
    except Exception as e:
        flash(f"API Key Error: {e}")
        return redirect("/upload_page")

    # Save file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Store session state needed for background job
    session["filename"] = os.path.splitext(filename)[0]
    session["filepath"] = filepath
    session["user_name"] = user_name
    session["api_key"] = api_key

    return redirect("/process")


@app.route("/process")
def process():
    """Show a processing page (frontend should poll /task-status)."""
    if not session.get("filepath"):
        return redirect("/")
    return render_template("processing.html")


@app.route("/start-task", methods=["POST"])
def start_task():
    """Start the background worker thread and return immediately (202)."""
    task_id = str(uuid.uuid4())
    session["task_id"] = task_id
    with tasks_lock:
        tasks[task_id] = {"status": "pending", "progress": 0}

    # Use a copy of session data so thread sees needed values
    thread = threading.Thread(target=background_explanation_task, args=(task_id, session.copy()))
    thread.daemon = True
    thread.start()
    return jsonify({"message": "Task started."}), 202


@app.route("/task-status")
def task_status():
    """Return JSON describing the current task's status and progress."""
    task_id = session.get("task_id")
    if not task_id:
        return jsonify({"status": "not_found"})
    with tasks_lock:
        task = tasks.get(task_id, {})
    return jsonify({
        "status": task.get("status"),
        "progress": task.get("progress"),
        "message": task.get("message")
    })


@app.route("/read")
def read():
    """
    Display the completed annotated book.
    If processing isn't complete, redirect back to process page with a message.
    """
    task_id = session.get("task_id")
    if not task_id:
        return redirect("/")

    with tasks_lock:
        task = tasks.get(task_id, {})

    if task.get("status") != "complete":
        flash("Processing is not complete or an error occurred.")
        return redirect("/")

    # store the book_data in session for download route, and render read template
    book_data = task.get("data", {})
    session["book_data"] = book_data

    # Build chapter list with slug IDs for client-side TOC
    chapters_with_ids = [{"title": title, "id": slugify(title)} for title in book_data.keys()]

    return render_template("read.html", book=book_data, chapters=chapters_with_ids)


@app.route("/download")
def download():
    """
    Create the annotated book zip and send it as a file download.
    Also clean up the uploaded file and clear the session.
    """
    book_data = session.get("book_data")
    if not book_data:
        flash("Could not find book data for download. Please try the process again.")
        return redirect("/")

    zip_data = create_book_zip(book_data, session.get("filename", "annotated_book"))
    download_filename = f"{session.get('filename', 'annotated_book')}_annotated.zip"

    # Remove the uploaded file (cleanup)
    if session.get("filepath") and os.path.exists(session.get("filepath")):
        try:
            os.remove(session.get("filepath"))
        except Exception:
            pass

    # Clear session after preparing download
    session.clear()

    return Response(zip_data, mimetype="application/zip", headers={"Content-disposition": f"attachment; filename={download_filename}"})


# === Run the app ===
if __name__ == "__main__":
    # Debug mode for development; set debug=False for production
    app.run(debug=True, threaded=True)
