## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/vinayakravi/web-markdown-converter.git
    ```
2. Navigate to the project directory:
    ```sh
    cd web-markdown-converter
    ```
3. Sync and install dependencies:
    ```sh
    # Install Python Dependencies using uv (install uv first if not already installed)
    uv sync

    # Install Playwright
    uv run python -m playwright install --with-deps chromium

    # Create Output directory
    mkdir output
    
    ```

## Usage

1. Update main mthod in sitemap_fetcher to specify sitemap xml

2. Run the sitemap fetcher script:
    ```sh
    # Either specify the URL of a single page to convert, a sitemap.xml link or a txt file with list of links to convert as an argument
    uv run python sitemap_fetcher.py
    ```
