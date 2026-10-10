# hackathonProject
project for hackathon




# roles:
Split your team into four owners: capture, AI analysis, storage/search, and interface/integration. Each person can build their part independently, provided you agree on the inputs and outputs first.

For today, aim for this complete loop:

text
Take screenshot
      ↓
Save original safely
      ↓
AI generates category, title and tags
      ↓
App creates/reuses the category folder
      ↓
Screenshot appears in your searchable gallery

1. Person A — screenshot capture

Owns: the snipping-tool behaviour.

Tasks:

    Add a “Take screenshot” button.

    Let the user select a rectangular area.

    Save the captured image to a temporary/pending folder.

    Pass its file path to the processing pipeline.

    Handle cancelling a capture cleanly.

Deliverable:

python
capture_screenshot() -> image_path

If using Python, MSS supports capturing screen regions; the selection overlay is a separate interface task you would still need to implement. Test capture on the actual demo laptop immediately rather than assuming it works everywhere.

Fallback: if region selection takes too long, start with full-screen capture or importing an image. This lets the other three people keep working.
2. Person B — AI image analysis

Owns: turning an image into useful metadata.

Tasks:

    Connect to an image-capable AI API.

    Send the screenshot with instructions to identify its content.

    Return a title, category, tags and short description.

    Validate the response.

    Handle API failures without losing the screenshot.

Deliverable:

python
analyse_screenshot(image_path) -> metadata

Agree on this response format:

json
{
  "title": "Binary search tree insertion",
  "category": "Diagrams",
  "tags": [
    "computer science",
    "binary search tree",
    "data structures",
    "insertion"
  ],
  "description": "A lecture diagram showing insertion into a binary search tree."
}

Use structured output if your chosen API supports it. OpenAI’s structured-output feature can constrain responses to a supplied JSON schema, including permitted category values; that ensures the format, not the correctness of the classification.

For the prototype, choose from a fixed category list:

text
Diagrams
Code
Questions
Lecture Notes
Receipts
Other

This still creates folders automatically when first needed, but avoids inconsistent categories such as Diagram, Diagrams and Lecture diagrams.
3. Person C — folder organisation and search

Owns: saving the image and making its metadata searchable.

Tasks:

    Create the category folder if it does not exist.

    Move the screenshot into that folder.

    Use safe filenames and prevent overwriting existing screenshots.

    Store its path, title, category, tags, description and capture time.

    Implement keyword search and category filtering.

Deliverables:

python
save_screenshot(image_path, metadata) -> saved_record

search_screenshots(query="", category=None) -> list_of_records

Example result:

text
Screenshots/
├── Diagrams/
│   └── binary-search-tree-insertion_104805.png
├── Code/
└── screenshots.db

How the tags work

The tags do not need to be embedded inside the PNG. Store them in a database record linked to the image’s path.

When someone searches “tree,” your app searches the stored title, tags and description, then displays the matching screenshots.

SQLite is a suitable local option because it does not require a separate database server, and Python provides a sqlite3 interface.

Keep category folder names restricted to your agreed list; do not use arbitrary AI text as a filesystem path.
4. Person D — gallery, integration and demo

Owns: the usable application and connecting everyone’s work.

Tasks:

    Build the main window with:

        Screenshot button.

        Screenshot thumbnails.

        Search box.

        Category filter.

        Details showing title and tags.

    Connect capture → AI → storage → gallery refresh.

    Show processing, success and failure states.

    Ensure AI processing does not freeze the interface.

    Coordinate integration tests, README and demo recording.

Deliverable: a working app where a screenshot automatically appears in the correct category and can be found through search.

Start the gallery using fake records so you do not have to wait for the AI or storage components.
