import os
import sys
import psutil
import requests
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

__location__ = os.path.dirname(os.path.abspath(__file__))
__output__ = os.path.join(__location__, "output")

async def crawl_parallel(urls: List[str], max_concurrent: int = 3):
    """Crawl multiple URLs in parallel with memory tracking"""
    print("\n=== Parallel Crawling with Browser Reuse + Memory Check ===")
    
    # Memory tracking
    peak_memory = 0
    process = psutil.Process(os.getpid())

    def log_memory(prefix: str = ""):
        nonlocal peak_memory
        current_mem = process.memory_info().rss  # in bytes
        if current_mem > peak_memory:
            peak_memory = current_mem
        print(f"{prefix} Current Memory: {current_mem // (1024 * 1024)} MB, Peak: {peak_memory // (1024 * 1024)} MB")

    # Browser configuration
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        #extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    # Create crawler instance
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        success_count = 0
        fail_count = 0
        
        # Process URLs in batches
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = []

            # Create tasks for each URL in batch
            for j, url in enumerate(batch):
                session_id = f"parallel_session_{i + j}"
                output_path = os.path.join(__output__, f"link_{i + j + 1}.md")
                
                async def process_url(url: str, output_path: str):
                    try:
                        result = await crawler.arun(url=url, config=crawl_config, session_id=session_id)
                        if result.success:
                            with open(output_path, 'w') as f:
                                f.write(result.markdown)
                            return True
                        return False
                    except Exception as e:
                        print(f"Error processing {url}: {e}")
                        return False

                tasks.append(process_url(url, output_path))

            # Check memory before batch
            log_memory(prefix=f"Before batch {i//max_concurrent + 1}: ")

            # Execute batch
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check memory after batch
            log_memory(prefix=f"After batch {i//max_concurrent + 1}: ")

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    fail_count += 1
                elif result:
                    success_count += 1
                else:
                    fail_count += 1

        print(f"\nSummary:")
        print(f"  - Successfully crawled: {success_count}")
        print(f"  - Failed: {fail_count}")

    finally:
        print("\nClosing crawler...")
        await crawler.close()
        # Final memory log
        log_memory(prefix="Final: ")
        print(f"\nPeak memory usage (MB): {peak_memory // (1024 * 1024)}")

def fetch_sitemap_links(sitemap_url: str) -> List[str]:
    """Fetch all links from a sitemap.xml file"""
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')
        links = []
        
        # Find all <loc> tags which contain the URLs
        for loc in soup.find_all('loc'):
            url = loc.text.strip()
            if is_valid_url(url):
                links.append(url)
                
        return links
        
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

async def main():
    if len(sys.argv) < 2:
        print("Usage: python sitemap_fetcher.py [sitemap_url|file_path|single_url]")
        return
        
    input_arg = sys.argv[1]
    
    links = []
    
    if urlparse(input_arg).scheme in ('http', 'https'):
        # Single URL or Sitemap URL
        if "sitemap" in input_arg:
            sitemap_url = input_arg
            links = fetch_sitemap_links(sitemap_url)
        else:
            links.append(input_arg)
        
    elif input_arg.endswith('.txt'):
        with open(input_arg, 'r') as file:
            urls = file.readlines()
            links.extend([url.strip() for url in urls if url.strip()])
    
    else:
        print("Invalid argument. Provide a sitemap URL, a text file path, or a single URL.")
        return

    if not links:
        print("No valid links found")
        return
    
    print(f"Found {len(links)} links")
    await crawl_parallel(links, max_concurrent=3)

if __name__ == "__main__":
    asyncio.run(main())
