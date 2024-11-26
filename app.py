import streamlit as st
import pandas as pd
from premai import Prem

# Prem Configuration
API_KEY = "205ICPH4NmJxv9gFYGlMXhpVTr7egbYXTe"  # Replace with your actual API key
PROJECT_ID = "458"  # Replace with your project ID
client = Prem(api_key=API_KEY)

# App Title
st.title("🎯 Customer Review Insights with Prem SDK")

# Upload File Section
uploaded_file = st.file_uploader("Upload a CSV file containing reviews", type=["csv"])

if uploaded_file:
    try:
        # Read the uploaded file
        reviews_df = pd.read_csv(uploaded_file)

        # Smart Detection of Text Column
        def detect_text_column(df):
            scores = {}
            for column in df.columns:
                if df[column].dtype == object:  # Check for string-like columns
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

        # Prem Chat Completion: Sentiment Analysis
        def analyze_sentiment_prem(texts):
            responses = []
            for text in texts:
                messages = [{"role": "user", "content": f"Classify the sentiment of this text as Positive, Negative, or Neutral: '{text}'"}]
                response = client.chat.completions.create(
                    project_id=PROJECT_ID,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=10
                )
                sentiment = response.choices[0].message.content.strip()
                responses.append(sentiment)
            return responses

        st.subheader("Prem Sentiment Analysis")
        reviews_df['sentiment'] = analyze_sentiment_prem(reviews_df[text_column].dropna().tolist())
        st.write(reviews_df[[text_column, 'sentiment']])

        # Prem Chat Completion: Topic Detection
        def detect_topics_prem(texts):
            responses = []
            for text in texts:
                messages = [{"role": "user", "content": f"Identify the topic of this text in one or two words: '{text}'"}]
                response = client.chat.completions.create(
                    project_id=PROJECT_ID,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=20
                )
                topic = response.choices[0].message.content.strip()
                responses.append(topic)
            return responses

        st.subheader("Prem Topic Detection ")
        reviews_df['topic'] = detect_topics_prem(reviews_df[text_column].dropna().tolist())
        st.write(reviews_df[[text_column, 'topic']])

        # Filter by Topic
        st.subheader("Filter Reviews by Topic")
        selected_topic = st.selectbox("Select Topic", options=["All"] + reviews_df['topic'].unique().tolist())
        if selected_topic != "All":
            st.write(reviews_df[reviews_df['topic'] == selected_topic])

        # Webhook Section
        st.subheader("Send Data to Webhook")
        webhook_url = st.text_input("Enter Webhook URL")
        if st.button("Send Insights"):
            payload = reviews_df[[text_column, 'sentiment', 'topic']].to_dict(orient="records")
            try:
                response = requests.post(webhook_url, json=payload)
                st.success(f"Data sent! Webhook Response: {response.status_code}")
            except Exception as e:
                st.error(f"Failed to send data: {e}")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.info("Please upload a file to start.")
