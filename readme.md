1) How to Run
	- Clone the repository & enter the repository on local
	- Create a virtual environment (python3 -m venev gmenv)
	- Enter the virtual environment (source gmenv/bin/activate)
	- Run the requirements.txt (pip install -r requirements.txt)
	- Run the flask file (python3 test.py)
	- Check the response on browser by (http://localhost:9000/api/reviews?page={url}) -> example (http://localhost:9000/api/reviews?page=https://2717recovery.com/products/recovery-cream)
	- Sample responses of 3 urls are given in this repository

2) Workflow
	- This can be understood by breaking it in 2 stages first is using playwright to get the html content out of the page & second is getting review selector & putting it in format.
	- Playwright opens the url in chromium in headless format which means it doesn't need an UI to scrape html content
	- It uses google/flan tokenizer & model to extract selector of html content.
	- It gives a prompt to the tokenizer to extract common review tags in html content.
	- Then it matches those tags with the tags in html content & extracts parents of those tags from html content which generally can be div, section or article.
	- Pagination is applied by clicking on the next button from the pagination container (ul.pagination)