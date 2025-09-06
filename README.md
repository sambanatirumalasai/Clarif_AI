# &nbsp; &nbsp; &nbsp;  &nbsp;     &nbsp; &nbsp; &nbsp;  &nbsp;     &nbsp;  &nbsp; &nbsp;  &nbsp;     &nbsp;                           ClarifAI - The AI Book Companion

"ClarifAI" is a web application that transforms any plain text book into a personal, interactive e-reader with AI-powered explanations, designed to enhance comprehension and create a beautiful, offline reading experience.

## Project Philosophy

ClarifAI is more than just a document reader; it's a personal e-book **factory**. Unlike typical web tools that require a constant online connection, ClarifAI's goal is to produce a final, polished, and permanent product for the user to own and keep. The entire process is designed to be private and self-contained, using the user's own API key to create a standalone, offline e-reader that ensures a focused and secure reading environment.

## Features

* **Seamless Workflow:** A simple, guided process from welcome page to final download.
* **Intelligent Annotation:** Uses Google's `gemini-1.5-pro` model to provide detailed, context-aware explanations for every paragraph.
* **Asynchronous Processing:** Employs a background task queue to handle long books without timing out, providing a smooth user experience with a live progress indicator.
* **Professional E-Reader Output:** Generates a downloadable `.zip` file containing a standalone, offline HTML e-reader.
* **High-Quality Design:** The final e-reader features a polished dark mode, professional typography (`Merriweather` & `Lato`), and a clean, user-friendly layout with a clickable Table of Contents.
* **Rich Content Support:** Parses and displays both text paragraphs and embedded images from the source `.txt` file.

## 🌙 Superior Reading Experience

- **Dark Mode Ready:** The exported book can be viewed in dark mode, reducing eye strain and making long reading sessions more comfortable.
- **Neat and Modern Formatting:** Clean organization of sections and paragraphs ensures clarity and easy navigation—far better than cluttered or static PDFs.
- **AI-Powered Insights:** Explanations and annotations are seamlessly integrated for deeper understanding, making study and review effortless.
- **Flexible Formats:** Output files (HTML, Markdown, etc.) can be opened on any device and customized to suit your reading preferences.

> **Tip:** The downloadable zip file contains all enhanced content—just extract and open in your favorite viewer for the best experience!

## Tech Stack

* **Backend:** Flask (Python)
* **AI:** Google Generative AI (Gemini 1.5 Pro)
* **Frontend:** HTML, CSS, JavaScript (for status polling)
* **Session Management:** Flask-Session (Filesystem-based)
* **Concurrency:** Python's `threading` for background tasks.

## How It Works

The application uses a "factory" model. The user provides a formatted `.txt` file and their Gemini API key. The Flask backend then starts a background thread to:

1.  Parse the text into a structured format of chapters and content blocks.
2.  Initiate a conversational chat session with the Gemini API for each chapter to maintain context.
3.  Send each paragraph to the API to get a detailed explanation.
4.  While this happens, the user sees a processing page that polls the server for status updates.
5.  Once complete, the user can review the annotated book online and download the final `.zip` archive, which contains a fully interactive, offline HTML e-reader.

## Prerequisites

Before running the application, you will need two things:

* **Your Name:** This is used to personalize the AI's explanations, making them feel like a direct conversation (e.g., "As you can see, David...").
* **Google AI (Gemini) API Key:** The application uses your own API key to communicate with the Gemini model. This ensures your usage is private and under your control.

    * You can get a free API key from the **[Google AI Studio](https://aistudio.google.com/)**.
    * **Note:** Google generously provides a free tier that is more than sufficient for processing several books.

## Local Setup & Run

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/sambanatirumalasai/Clarif_AI.git
    cd Clarif_AI
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    flask run
    ```

4.  Open your web browser and navigate to `http://127.0.0.1:5000`.


