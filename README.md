
# PDF Structure Extractor - Adobe Hackathon Submission

This project is a submission for Round 1A of the Adobe India Hackathon "Connecting the Dots" Challenge. It is a fully containerized Python application designed to analyze PDF documents and automatically extract a structured outline, including the document's **Title** and hierarchical headings (**H1, H2, H3**).

The solution is built to be lightweight, fast, and robust, handling a wide variety of PDF layouts without relying on large, pre-trained models.

## Our Approach

The core of this solution is a multi-stage, heuristic-based pipeline that mimics how a human might identify structure, but applies it with machine precision. Instead of relying on a single attribute like font size, it analyzes a combination of stylistic and positional features.

The process is broken down into four main stages:

### 1. PDF Parsing & Block Grouping
- The process begins by using the `pdfplumber` library to parse each page of the PDF. Crucially, we extract not just the text but also rich metadata for each word, including its exact position (`bbox`), `fontname`, and `size`.
- Individual words are then grouped into logical text blocks. This is done by first merging words on the same vertical line into text lines, and then merging consecutive lines into blocks as long as they maintain consistent font properties (name and size) and have small vertical spacing between them. This reconstructs paragraphs and headings from raw word data.

### 2. Feature Engineering & Filtering
- We then filter out common non-content elements like **headers and footers** by ignoring text in the top and bottom 8% of each page.
- For every remaining text block, we engineer a set of features to help classify it:
    - **Stylistic Features:** `font_size`, `is_bold`, `is_all_caps`.
    - **Positional Features:** `is_centered` on the page.
    - **Content Features:** `word_count`, whether it `starts_with_number` (e.g., "2.1 Introduction"), or if it looks like a **Table of Contents** entry (e.g., "Topic...........5").

### 3. Title & Heading Identification
- **Title Extraction:** The title is identified by scoring potential candidates on the first page. Blocks get higher scores for larger font sizes, being bold, and being centered near the top of the page.
- **Heading Identification:** Any block that is not the title is considered a potential heading if it meets a set of rules (e.g., low word count, bold font, larger-than-normal text, etc.). This creates a clean list of candidate headings for the next stage.

### 4. Hierarchical Level Assignment (H1-H3)
- To avoid brittle `if/else` rules for font sizes, we use an unsupervised machine learning approach.
- The `font_size` of all candidate headings are collected and fed into a **KMeans clustering algorithm** from `scikit-learn`.
- We configure KMeans to find up to 3 clusters, representing H1, H2, and H3. The cluster with the largest average font size is labeled H1, the next largest is H2, and so on.
- This dynamic approach allows the solution to adapt to documents where, for example, the "H1" font size might be 24pt in one PDF and only 18pt in another.

## Libraries and Models Used

This solution is intentionally lightweight and does not use any large pre-trained language models. The intelligence comes from the algorithmic approach and a minimal ML clustering model.

-   **PDF Processing:**
    -   `pdfplumber`: The core library for extracting text, objects, and detailed metadata from PDF files.
    -   `pdf2image` & `Pillow`: Used by the `pdfplumber` ecosystem for operations that may require rendering page information.

-   **Data Analysis & Machine Learning:**
    -   `numpy`: Used for efficient numerical operations, primarily for preparing the font size data for clustering.
    -   `scikit-learn`: Used for its `KMeans` implementation to intelligently and dynamically cluster headings into H1, H2, and H3 levels based on font size.

## How to Build and Run

The entire solution is containerized with Docker, ensuring it runs identically on any machine.

### Prerequisites
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### Step 1: Clone the Repository
Clone this project to your local machine.```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### Step 2: Prepare Input Files
Place all the PDF files you want to process into the `input/` directory. The application is configured to read from this folder. The `output/` folder will be created automatically if it doesn't exist.

Your directory structure should look like this:
```
.
├── input/
│   ├── file01.pdf
│   └── file02.pdf
├── output/
├── Dockerfile
├── main.py
└── ... (other python files)
```

### Step 3: Build the Docker Image
Build the Docker image using the provided `Dockerfile`. This command packages all code and dependencies.
```bash
docker build -t pdf-outline-extractor .
```

### Step 4: Run the Solution
Run the container using the command below. This will mount your local `input` and `output` folders into the container, process the files, and save the results back to your local `output` folder.

```bash
docker run --rm -v "%cd%/input:/app/input" -v "%cd%/output:/app/output" pdf-outline-extractor
```
*(**Note for macOS/Linux users:** Replace `%cd%` with `$(pwd)`)*

After the script finishes, the `output/` directory will contain a `.json` file for each processed PDF, containing the extracted title and outline.