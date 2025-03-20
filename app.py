from flask import Flask, render_template, jsonify, request
import pandas as pd
import plotly.express as px
import plotly.utils
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from wordcloud import WordCloud
import numpy as np
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

class TrendAnalyzer:
    def __init__(self):
        self.trends_data = self._fetch_real_trends()
        self.last_update = datetime.now()
        self.update_interval = 3600  # Update every hour

    def _fetch_real_trends(self):
        try:
            # Fetch trends from fashion websites
            websites = [
                'https://www.vogue.com/fashion',
                'https://www.elle.com/fashion',
                'https://www.harpersbazaar.com/fashion'
            ]
            
            all_text = ""
            trends = []
            
            for url in websites:
                response = requests.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    all_text += soup.get_text()
                    
                    # Extract article titles and headlines
                    headlines = soup.find_all(['h1', 'h2', 'h3'])
                    for headline in headlines:
                        if headline.text.strip():
                            trends.append(headline.text.strip())

            # Generate word cloud from collected text
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate(all_text)
            words = [(word, freq) for word, freq in wordcloud.words_.items()]
            words.sort(key=lambda x: x[1], reverse=True)

            # Extract categories and their frequencies
            categories = {
                'Streetwear': 0, 'Formal': 0, 'Casual': 0,
                'Athletic': 0, 'Vintage': 0, 'Sustainable': 0
            }
            
            for word, freq in words:
                for category in categories:
                    if category.lower() in word.lower():
                        categories[category] += freq * 100

            return {
                'categories': list(categories.keys()),
                'popularity': [min(100, max(0, int(v))) for v in categories.values()],
                'trending_items': self._process_trends(trends)
            }
        except Exception as e:
            print(f"Error fetching trends: {e}")
            return self._get_fallback_data()

    def _process_trends(self, trends):
        # Process and score trending items
        trend_scores = {}
        for trend in trends:
            words = trend.lower().split()
            for word in words:
                if len(word) > 3:  # Ignore short words
                    trend_scores[word] = trend_scores.get(word, 0) + 1

        # Convert to list of items with scores
        items = [{'name': k.title(), 'trend_score': min(100, v * 10)} 
                for k, v in sorted(trend_scores.items(), key=lambda x: x[1], reverse=True)[:5]]
        return items

    def _get_fallback_data(self):
        return {
            'categories': ['Streetwear', 'Formal', 'Casual', 'Athletic', 'Vintage', 'Sustainable'],
            'popularity': [85, 60, 75, 80, 65, 90],
            'trending_items': [
                {'name': 'Sustainable Fashion', 'trend_score': 95},
                {'name': 'Oversized Blazers', 'trend_score': 88},
                {'name': 'Wide-leg Pants', 'trend_score': 82},
                {'name': 'Platform Shoes', 'trend_score': 78},
                {'name': 'Crop Tops', 'trend_score': 75}
            ]
        }

    def get_trending_items(self):
        if (datetime.now() - self.last_update).seconds > self.update_interval:
            self.trends_data = self._fetch_real_trends()
            self.last_update = datetime.now()
        return {'items': self.trends_data['trending_items']}

    def get_color_trends(self):
        # Color trends based on current fashion seasons
        season = self._get_current_season()
        color_trends = {
            'spring': {
                'colors': ['#FF9ECD', '#87CEEB', '#98FB98', '#DDA0DD', '#F0E68C'],
                'popularity': [92, 88, 85, 80, 75]
            },
            'summer': {
                'colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD'],
                'popularity': [90, 85, 80, 75, 70]
            },
            'fall': {
                'colors': ['#8B4513', '#DAA520', '#CD853F', '#D2691E', '#B8860B'],
                'popularity': [88, 85, 82, 78, 75]
            },
            'winter': {
                'colors': ['#483D8B', '#2F4F4F', '#800000', '#4B0082', '#000080'],
                'popularity': [90, 85, 80, 75, 70]
            }
        }
        return color_trends[season]

    def _get_current_season(self):
        month = datetime.now().month
        if month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'fall'
        else:
            return 'winter'

    def get_categories(self):
        if (datetime.now() - self.last_update).seconds > self.update_interval:
            self.trends_data = self._fetch_real_trends()
            self.last_update = datetime.now()
        return {
            'categories': self.trends_data['categories'],
            'popularity': self.trends_data['popularity']
        }

analyzer = TrendAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/trends')
def get_trends():
    trends = analyzer.get_trending_items()
    return jsonify(trends)

@app.route('/api/colors')
def get_colors():
    colors = analyzer.get_color_trends()
    return jsonify(colors)

@app.route('/api/categories')
def get_categories():
    return jsonify(analyzer.get_categories())

if __name__ == '__main__':
    app.run(debug=True, port=5000)
