import asyncio
from crawl4ai import *
from flask import Flask, request, render_template_string
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

app = Flask(__name__)

# Global variable to store extracted data
data = {
    "text": "", 
    "html": "", 
    "images": [], 
    "videos": [], 
    "css": [], 
    "js": [], 
    "links": []  # Added to store page links
}

async def scrape_data(url):
    global data
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            extract=["text", "html", "links", "media"]
        )
        if result:
            data["text"] = result.markdown if result.markdown else "Failed to extract text."
            data["html"] = result.html if result.html else "Failed to extract HTML."
            
            # Extract and join media URLs
            data["images"] = [urljoin(url, media) if not media.startswith(('http', 'https')) else media
                             for media in result.media if media.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
            data["videos"] = [urljoin(url, media) if not media.startswith(('http', 'https')) else media
                             for media in result.media if media.endswith(('.mp4', '.webm', '.ogg'))]
            
            # Extract CSS & JS files
            data["css"] = [urljoin(url, link) for link in result.links if link.endswith(".css")]
            data["js"] = [urljoin(url, link) for link in result.links if link.endswith(".js")]
            
            # Extract page links
            data["links"] = [urljoin(url, link) if not link.startswith(('http', 'https')) else link
                             for link in result.links if link]  # Filter out empty links
            
            # Debugging: Print extracted data
            print("Extracted Images (Crawl4.ai):", data["images"])
            print("Extracted Links (Crawl4.ai):", data["links"])
        else:
            data = {"text": "Failed to extract data.", "html": "", "images": [], "videos": [], "css": [], "js": [], "links": []}

def scrape_with_selenium(url):
    """Fallback to Selenium for dynamic content."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    page_source = driver.page_source
    driver.quit()

    soup = BeautifulSoup(page_source, "html.parser")
    images = [img["src"] for img in soup.find_all("img", src=True)]
    videos = [video["src"] for video in soup.find_all("video", src=True)]
    links = [a["href"] for a in soup.find_all("a", href=True)]
    
    # Resolve relative URLs
    images = [urljoin(url, img) if not img.startswith(('http', 'https')) else img for img in images]
    videos = [urljoin(url, video) if not video.startswith(('http', 'https')) else video for video in videos]
    links = [urljoin(url, link) if not link.startswith(('http', 'https')) else link for link in links]
    
    return images, videos, links

@app.route('/', methods=['GET', 'POST'])
def home():
    url = request.form.get("url", "")

    if request.method == "POST" and url:
        asyncio.run(scrape_data(url))
        
        # If no images were extracted, use Selenium as a fallback
        if not data["images"]:
            print("Falling back to Selenium for image extraction...")
            images, videos, links = scrape_with_selenium(url)
            data["images"] = images
            data["videos"] = videos
            data["links"] = links  # Update links with Selenium-extracted links
            print("Extracted Images (Selenium):", data["images"])
            print("Extracted Links (Selenium):", data["links"])

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Crawl4ai</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {
                background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
                font-family: 'Georgia', serif;
            }
            .navbar {
                background: rgba(255, 255, 255, 0.8);
                backdrop-filter: blur(10px);
            }
            .card {
                background: rgba(255, 255, 255, 0.9);
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
            }
            .btn-primary {
                background: linear-gradient(135deg, #4f46e5, #6366f1);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                transition: background 0.3s ease;
            }
            .btn-primary:hover {
                background: linear-gradient(135deg, #6366f1, #4f46e5);
            }
            .preformatted {
                white-space: pre-wrap;
                word-wrap: break-word;
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Courier New', monospace;
            }
        </style>
    </head>
    <body>
        <nav class="navbar shadow-sm py-4">
            <div class="max-w-6xl mx-auto px-4">
                <h1 class="text-2xl font-bold text-gray-800">Crawl4ai</h1>
            </div>
        </nav>

        <div class="max-w-6xl mx-auto mt-8 px-4">
            <div class="card p-6">
                <form method="POST" class="flex space-x-2">
                    <input type="text" name="url" placeholder="Enter website URL" 
                           class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <button type="submit" class="btn-primary">
                        Fetch Data
                    </button>
                </form>
            </div>

            {% if data['text'] %}
<div class="card mt-6 p-6">
    <h2 class="text-xl font-semibold text-gray-800 mb-4">Text Content</h2>
    <div class="preformatted overflow-y-auto max-h-60 border p-4 bg-gray-100">
        {{ data['text'] }}
    </div>
</div>
{% endif %}

{% if data['html'] %}
<div class="card mt-6 p-6">
    <h2 class="text-xl font-semibold text-gray-800 mb-4">Page HTML</h2>
    <div class="preformatted overflow-y-auto max-h-60 border p-4 bg-gray-100">
        <code>{{ data['html'] | e }}</code>
    </div>
</div>
{% endif %}


            {% if data['images'] %}
            <div class="card mt-6 p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">Images</h2>
                <div class="grid grid-cols-3 gap-4">
                    {% for img in data['images'] %}
                    <img src="{{ img }}" alt="Image" class="w-full h-48 object-cover rounded-lg shadow">
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            {% if data['links'] %}
            <div class="card mt-6 p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">Page Links</h2>
                <ul class="list-disc pl-6">
                    {% for link in data['links'] %}
                    <li><a href="{{ link }}" target="_blank" class="text-blue-600 hover:underline">{{ link }}</a></li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}

            {% if data['css'] %}
            <div class="card mt-6 p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">CSS Files</h2>
                <ul class="list-disc pl-6">
                    {% for css in data['css'] %}
                    <li><a href="{{ css }}" target="_blank" class="text-blue-600 hover:underline">{{ css }}</a></li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}

            {% if data['js'] %}
            <div class="card mt-6 p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">JavaScript Files</h2>
                <ul class="list-disc pl-6">
                    {% for js in data['js'] %}
                    <li><a href="{{ js }}" target="_blank" class="text-blue-600 hover:underline">{{ js }}</a></li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}

            {% if data['videos'] %}
            <div class="card mt-6 p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">Videos</h2>
                <div class="grid grid-cols-2 gap-4">
                    {% for video in data['videos'] %}
                    <video controls class="w-full rounded-lg shadow">
                        <source src="{{ video }}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    """, data=data)
    
if __name__ == "__main__":
    app.run(debug=True)