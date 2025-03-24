import gradio as gr
import requests
import pandas as pd
import json
from datetime import datetime

def get_pageviews(article_title, start, end):
    title_api = article_title.replace(" ", "_")
    url_base = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/{access}/{agent}/{title_api}/daily/{start}/{end}"

    # Parameters
    project = "en.wikipedia"  # English Wikipedia
    access = "all-access"      # All access methods (desktop, mobile, etc.)
    agent = "all-agents"      # Changed from "user" to "all-agents" as per the API documentation

    # Construct the API request URL
    url = url_base.format(
        project=project,
        access=access,
        agent=agent,
        title_api=title_api,
        start=start,
        end=end
    )

    # Send GET request with User-Agent header
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    try:
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()

        if 'items' not in data:
            print(f"No data found for {article_title}")
            return pd.DataFrame()

        views = [{
            'date': item['timestamp'][:8],
            'views': item['views']
        } for item in data['items']]

        df = pd.DataFrame(views)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.rename(columns={'views': article_title}, inplace=True)
        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {article_title}: {e}")
        return pd.DataFrame()
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON for {article_title}: {e}")
        try:
            print(f"Raw response content for {article_title}: {response.text}") # Print the raw response if available
        except AttributeError:
            print(f"No response content to display for {article_title}.")
        return pd.DataFrame()

def plot_pageviews(article_title, start_date, end_date):
    """Fetches pageviews and returns a plot."""
    df = get_pageviews(article_title, start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
    if not df.empty:
        return df.plot(title=f"Pageviews for '{article_title}'").get_figure()
    else:
        return "No data available for the given article and date range."

# Define the Gradio interface
iface = gr.Interface(
    fn=plot_pageviews,
    inputs=[
        gr.Textbox(label="Wikipedia Article Title"),
        gr.Date(label="Start Date", value=datetime(2024, 1, 1)),  # Set a default start date
        gr.Date(label="End Date", value=datetime.now()),        # Set a default end date to today
    ],
    outputs=gr.Plot(label="Pageviews Over Time"),
    title="Wikipedia Pageview Analyzer",
    description="Enter a Wikipedia article title and a date range to visualize its daily pageview history.",
    examples=[
        ["Machine learning", "2024-09-01", "2024-09-30"],
        ["Artificial intelligence", "2024-08-15", "2024-09-15"],
        ["Deep learning", "2024-07-01", "2024-12-31"]
    ]
)

# Launch the Gradio app
if __name__ == "__main__":
    iface.launch(share=True)
