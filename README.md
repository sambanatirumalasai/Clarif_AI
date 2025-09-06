Clarif_AI


  The AI Book Companion "Clarif_AI" is a web application that transforms any plain text book into a personal, interactive e-reader with AI-powered explanations, designed to enhance comprehension and create a beautiful, offline reading experience.


Features:


Seamless Workflow: A simple, guided process from welcome page to final download.

Intelligent Annotation: Uses Google's gemini-1.5-pro model to provide detailed, context-aware explanations for every paragraph.

Asynchronous Processing: Employs a background task queue to handle long books without timing out, providing a smooth user experience with a live progress indicator.

Professional E-Reader Output: Generates a downloadable .zip file containing a standalone, offline HTML e-reader.

High-Quality Design: The final e-reader features a polished dark mode, professional typography (Merriweather & Lato), and a clean, user-friendly layout with a clickable Table of Contents.

Rich Content Support: Parses and displays both text paragraphs and embedded images from the source .txt file.



Tech Stack


Backend : Flask (Python)

AI : Google Generative AI (Gemini 1.5 Pro)Frontend: HTML, CSS, JavaScript (for status polling)

Session Management : Flask-Session (Filesystem-based)Concurrency: Python's threading for background tasks.

How It Works

The application uses a "factory" model. The user provides a formatted .txt file and their Gemini API key. The Flask backend then starts a background thread to:

Parse the text into a structured format of chapters and content blocks.

Initiate a conversational chat session with the Gemini API for each chapter to maintain context.

Send each paragraph to the API to get a detailed explanation.

While this happens, the user sees a processing page that polls the server for status updates.

Once complete, the user can review the annotated book online and download the final .zip archive, which contains a fully interactive, offline HTML e-reader.



Local Setup & Run


Clone the repository:

git clone [https://github.com/](https://github.com/)\[your-username]/clarif\_ai.git


cd clarif_ai


Install dependencies:


pip install -r requirements.txt


Run the application:


flask run


Open your web browser and navigate to http://127.0.0.1:5000.This is a final project for Harvard's CS50x course.
