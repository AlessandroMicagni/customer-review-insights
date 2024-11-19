import streamlit as st
import pandas as pd
from textblob import TextBlob
import requests

# App Title
st.title("🎯 Customer Review Insights")

# Upload File Section
uploaded_file = st.file_uploader("Upload a CSV file containing reviews", type=["csv"])

if uploaded_file:
    try:
        # Read the CSV file
        reviews_df = pd.read_csv(uploaded_file)

        # Smart Detection of Text Column
        def detect_text_column(df):
            scores = {}
            for column in df.columns:
                if df[column].dtype == object:  # Only consider object (string-like) columns
                    text_content_ratio = df[column].apply(lambda x: isinstance(x, str)).mean()
                    avg_text_length = df[column].apply(lambda x: len(str(x)) if isinstance(x, str) else 0).mean()
                    keyword_match = 1 if any(keyword in column.lower() for keyword in ['review', 'feedback', 'comment', 'message']) else 0
                    
                    # Calculate a score combining the metrics
                    score = (text_content_ratio * 0.5) + (avg_text_length * 0.4) + (keyword_match * 0.1)
                    scores[column] = score
            
            # Select the column with the highest score
            if scores:
                best_column = max(scores, key=scores.get)
                return best_column, scores[best_column]
            return None, 0

        # Detect the review column
        text_column, column_score = detect_text_column(reviews_df)
        if not text_column:
            st.error("No suitable text column found. Please ensure your file contains review-like data.")
            st.stop()

        st.success(f"Detected review text column: '{text_column}' (Score: {column_score:.2f})")
        st.write(reviews_df.head())

        # Perform Sentiment Analysis
        st.subheader("Sentiment Analysis")
        reviews_df['sentiment'] = reviews_df[text_column].apply(
            lambda x: TextBlob(str(x)).sentiment.polarity if isinstance(x, str) else 0
        )
        reviews_df['sentiment_category'] = reviews_df['sentiment'].apply(
            lambda x: "Positive" if x > 0 else "Negative" if x < 0 else "Neutral"
        )
        st.write(reviews_df[[text_column, 'sentiment_category']])

        # Detect Topics Based on Keywords
        def detect_topic(review):
            review = review.lower()
            if "delivery" in review:
                return "Delivery"
            elif "quality" in review or "build" in review:
                return "Product Quality"
            elif "support" in review or "service" in review:
                return "Customer Support"
            elif "price" in review or "expensive" in review:
                return "Pricing"
            return "Other"

        reviews_df['topic'] = reviews_df[text_column].apply(detect_topic)

        st.subheader("Reviews Organized by Topic")
        st.write(reviews_df[[text_column, 'topic']])

        # Detect Types Based on Sentiment and Words
        def detect_type(review, sentiment):
            review = review.lower()
            if sentiment == "Negative":
                return "Complaint"
            elif sentiment == "Positive" and ("thank" in review or "love" in review):
                return "Praise"
            elif "should" in review or "could" in review:
                return "Suggestion"
            return "General Feedback"

        reviews_df['type'] = reviews_df.apply(
            lambda row: detect_type(row[text_column], row['sentiment_category']), axis=1
        )

        st.subheader("Reviews Organized by Type")
        st.write(reviews_df[[text_column, 'type']])

        # Filter by Topic
        st.subheader("Filter Reviews by Topic")
        selected_topic = st.selectbox("Select Topic", options=["All"] + reviews_df['topic'].unique().tolist())
        if selected_topic != "All":
            st.write(reviews_df[reviews_df['topic'] == selected_topic])

        # Filter by Type
        st.subheader("Filter Reviews by Type")
        selected_type = st.selectbox("Select Type", options=["All"] + reviews_df['type'].unique().tolist())
        if selected_type != "All":
            st.write(reviews_df[reviews_df['type'] == selected_type])

        # Webhook Section
        st.subheader("Send Data to Webhook")
        webhook_url = st.text_input("Enter Webhook URL")
        if st.button("Send Insights"):
            payload = reviews_df[[text_column, 'sentiment_category', 'topic', 'type']].to_dict(orient="records")
            try:
                response = requests.post(webhook_url, json=payload)
                st.success(f"Data sent! Webhook Response: {response.status_code}")
            except Exception as e:
                st.error(f"Failed to send data: {e}")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.info("Please upload a file to start.")
