import asyncio
from flask import Flask, request, jsonify
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import nest_asyncio
import torch
import re
import html
from transformers import T5Tokenizer, T5ForConditionalGeneration

nest_asyncio.apply()

app = Flask(__name__)

tokenizer = T5Tokenizer.from_pretrained('google/flan-t5-xl')
model = T5ForConditionalGeneration.from_pretrained('google/flan-t5-xl')

async def extract_reviews(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        reviews = []
        seen_reviews = set()
        page_number = 1

        while True:
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')

            prompt = f"What words or phrases might indicate a review section on this page: {url}"
            inputs = tokenizer(prompt, return_tensors="pt")
            outputs = model.generate(**inputs)
            keywords = tokenizer.decode(outputs[0], skip_special_tokens=True)
            keywords_list = keywords.split(', ')

            potential_review_elements = []
            for keyword in keywords_list:
                for element in soup.find_all(string=lambda text: keyword in text):
                    potential_review_elements.extend(element.find_parents())

            review_elements = list(set(potential_review_elements))
            review_elements = [element for element in review_elements
                               if element.name in ['div', 'article', 'section'] and len(element.text) > 50]

            for element in review_elements:
                title = element.find(class_=lambda x: x and 'title' in x.lower()).text if element.find(class_=lambda x: x and 'title' in x.lower()) else 'N/A'
                body = element.find(class_=lambda x: x and ('body' in x.lower() or 'content' in x.lower())).text if element.find(class_=lambda x: x and ('body' in x.lower() or 'content' in x.lower())) else 'N/A'
                rating_element = element.find(class_=lambda x: x and 'rating' in x.lower())
                rating = len(rating_element.find_all(class_=lambda x: x and 'star' in x.lower())) if rating_element else 'N/A'
                reviewer = element.find(class_=lambda x: x and 'author' in x.lower()).text if element.find(class_=lambda x: x and 'author' in x.lower()) else 'N/A'

                if body != 'N/A' and body not in seen_reviews:
                    seen_reviews.add(body)
                    body = html.unescape(body)
                    body = re.sub(r'\n+', '\n', body)
                    body = re.sub(r'\s+', ' ', body)

                    reviews.append({
                        "title": title,
                        "body": body,
                        "rating": rating,
                        "reviewer": reviewer
                    })

            pagination_links = await page.query_selector_all('ul.pagination a')
            next_page = None
            for link in pagination_links:
                text = await link.inner_text()
                if text == str(page_number + 1):
                    next_page = link
                    break

            if next_page:
                await next_page.click()
                await asyncio.sleep(2)
                page_number += 1
            else:
                break

        await browser.close()

        return {
            "reviews_count": len(reviews),
            "reviews": reviews
        }

@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    url = request.args.get('page')
    if not url:
        return jsonify({"error": "Missing 'page' query parameter"}), 400

    try:
        reviews_data = asyncio.run(extract_reviews(url))
        return jsonify(reviews_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def about():
    return jsonify({"success": "Welcome to review api"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
