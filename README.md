# **PDF Structure Extractor - Adobe Hackathon Submission**

This project is a submission for **Round 1A of the Adobe India Hackathon "Connecting the Dots" Challenge**. It is a fully containerized Python application designed to analyze PDF documents and automatically extract a structured outline, including the document's **Title** and hierarchical headings (**H1, H2, H3**). The solution is lightweight, fast, and robust, handling a wide variety of PDF layouts without relying on large, pre-trained models.

## **Our Approach**

The core of this solution is a multi-stage, heuristic-based pipeline that mimics human intuition for identifying document structure but applies it with machine precision. Instead of relying solely on a single attribute like font size, our algorithm analyzes a combination of stylistic, positional, and content-based features to ensure high accuracy.

The process is broken down into four main stages:

### **1. PDF Parsing & Block Grouping**
The process begins by using the `pdfplumber` library to parse each page, extracting not just text but also rich metadata for each word, including its exact position (`bbox`), `fontname`, and `size`. These individual words are then grouped into logical text blocks (lines and paragraphs) by analyzing their vertical alignment, font consistency, and spacing. This stage reconstructs a clean, structured representation of the PDF's content from raw word data.

### **2. Feature Engineering & Filtering**
To isolate meaningful content, we first filter out common non-content elements like **headers and footers** by ignoring text in the top and bottom 8% of each page. For every remaining text block, we engineer a set of features for classification:
-   **Stylistic Features**: `font_size`, `is_bold` (by checking font name), `is_all_caps`.
-   **Positional Features**: `is_centered` on the page.
-   **Content Features**: `word_count`, and whether the block `starts_with_number` (e.g., "2.1 Introduction") or looks like a **Table of Contents** entry (e.g., "Topic...........5").

### **3. Title & Heading Identification**
-   **Title Extraction**: The title is identified by scoring candidate blocks on the first page. Blocks receive higher scores for larger font sizes, bold styling, and centered alignment near the top of the page.
-   **Heading Identification**: Any non-title block is considered a potential heading if it meets a set of rules (e.g., low word count, bold font, larger-than-normal text). This creates a clean list of candidates for the final stage.

### **4. Hierarchical Level Assignment (H1-H3)**
To avoid brittle `if/else` rules for font sizes, we use an unsupervised machine learning approach. The `font_size` of all candidate headings is fed into a **KMeans clustering algorithm** from `scikit-learn`. We configure KMeans to find up to 3 clusters, representing H1, H2, and H3. The cluster with the largest average font size is labeled H1, the next largest is H2, and so on. This dynamic approach allows the solution to adapt to documents where, for instance, an H1 heading might be 24pt in one PDF and only 18pt in another.

---

## **Libraries and Models Used**

This solution is intentionally lightweight and does not use any large pre-trained language models. The intelligence comes from our algorithmic approach and a minimal ML clustering model.

-   **PDF Processing**:
    -   `pdfplumber`: The core library for extracting text and detailed metadata from PDF files.
    -   `Pillow`: A dependency of `pdfplumber` for image processing operations.

-   **Data Analysis & Machine Learning**:
    -   `numpy`: Used for efficient numerical operations, primarily for preparing font size data for clustering.
    -   `scikit-learn`: Used for its `KMeans` implementation to intelligently cluster headings into H1, H2, and H3 levels based on font size.

---

## **How to Build and Run (for Hackathon Evaluation)**

The entire solution is containerized with Docker to ensure it runs identically on any machine. The following instructions are aligned with the "Expected Execution" section of the challenge brief.

### **Prerequisites**
-   Docker must be installed and running.

### **Step 1: Place Input Files**
Place all PDF files to be processed into an `input/` directory in the project's root folder. The application is configured to read from this folder. An `output/` folder will be created automatically.

### **Step 2: Build the Docker Image**
Build the Docker image using the provided `Dockerfile`. This command packages all code and dependencies.
```bash
docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
```

### **Step 3: Run the Solution**
Run the container using the command below. This will mount your local `input` and `output` folders into the container, process the files, and save the results back to your local `output` folder. The container will automatically process all PDFs from `/app/input` and generate a corresponding `.json` file in `/app/output`.

```bash
docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none mysolutionname:somerandomidentifier
```
*(**Note:** The use of `$(pwd)` is standard for macOS/Linux. For Windows, `%cd%` may be used in Command Prompt or `$(pwd)` in PowerShell.)*

After the script finishes, the `output/` directory will contain a `.json` file for each processed PDF, containing the extracted title and outline as per the required format.