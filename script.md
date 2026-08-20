# 🎬 Zomato AI Recommender — Demo Script

This script is designed for a **3 to 5-minute video walkthrough** of the Zomato AI Recommender project (Milestone 1). It covers the architecture, the UI, and the LLM integration.

---

## 🕒 Part 1: Introduction (0:00 - 0:45)

**[Visual]**
- Screen recording starts on the **Streamlit Frontend** homepage (Welcome Screen).

**[Audio / Voiceover]**
> "Hello! Today I'm going to walk you through the Zomato AI Recommender, a premium, intelligent food-discovery application."
>
> "This project was built to solve a common problem: finding the perfect restaurant based on complex, subjective preferences. Instead of just filtering by simple numbers, this app uses a massive dataset of 51,000+ Bangalore restaurants and ranks them using Groq's blazing-fast LLaMA 3 70B Large Language Model."
>
> "The architecture is split into two parts: a FastAPI backend serving a high-performance REST API, and a dynamic, beautifully styled Streamlit frontend."

---

## 🕒 Part 2: The Core Workflow & UI (0:45 - 2:00)

**[Visual]**
- Hover over the left sidebar.
- Open the **Location** dropdown and select a neighborhood like *Koramangala*.
- Move the **Budget** slider to *₹1500*.
- Select *Italian* from the **Cuisine** dropdown.
- Type in the **Additional Preferences** box: *"Looking for a romantic place with rooftop seating."*

**[Audio / Voiceover]**
> "Let's dive into a live demo. On the left sidebar, we have our preference engine."
>
> "Notice how the UI is styled with a premium glassmorphism aesthetic, rather than the default Streamlit look. I'll select Koramangala as the location, set a medium budget of ₹1500, and choose Italian."
>
> "But here is where the AI comes in. In the 'Additional Preferences', I can type something subjective, like 'looking for a romantic place with rooftop seating'."

**[Visual]**
- Click **"🔍 Get Recommendations"**.
- Show the loading spinner.
- Scroll through the beautifully rendered restaurant cards.
- Highlight the **"✨ AI Reason"** section on the top result.

**[Audio / Voiceover]**
> "When I hit 'Recommend', the FastAPI backend kicks into gear. First, it uses Pandas to filter the 51,000-record dataset down to the best 20 statistical matches."
>
> "Then, it sends those candidates to the LLaMA 3 70B model via the Groq API. The LLM reads the reviews and attributes of those restaurants, and ranks the top 5 specifically based on my request for a romantic rooftop vibe."
>
> "As you can see, the results are presented in these premium cards. And at the bottom of each card, the LLM provides an 'AI Reason' explaining exactly *why* it picked this restaurant for me."

---

## 🕒 Part 3: Architecture & Edge Cases (2:00 - 3:15)

**[Visual]**
- Switch tab to the **VS Code / IDE** showing `src/services/recommendation.py` or the `tests/` folder.
- Highlight the fallback mechanisms in the code.

**[Audio / Voiceover]**
> "Under the hood, this system is built for production resilience."
>
> "What happens if the Groq API goes down, or if the user doesn't have an API key? The backend has an automatic **Smart Fallback** mode. If the LLM is unavailable, it gracefully degrades to a deterministic algorithm that ranks the filtered restaurants by a weighted score of their rating and popularity (votes), ensuring the user always gets a recommendation."
>
> "Furthermore, what if the user asks for a combination that doesn't exist? Like 'Italian food under ₹200 with a 5-star rating'?"

**[Visual]**
- Switch back to the **Browser**.
- Change the budget to *₹500* and Minimum Rating to *4.5*. Hit Recommend.
- Highlight the yellow **"⚠️ We relaxed filters"** alert banner that appears on the UI.

**[Audio / Voiceover]**
> "The engine includes an intelligent filter-relaxation algorithm. Instead of just showing an empty screen, it iteratively relaxes the constraints—like lowering the minimum rating or increasing the budget—until it finds matches. It then transparently alerts the user via this yellow banner that it had to adjust their filters to find these great options."

---

## 🕒 Part 4: Deployment & Conclusion (3:15 - 4:00)

**[Visual]**
- Switch tab to the **Railway Dashboard** showing the FastAPI deployment.
- Switch tab to the **Streamlit Cloud Dashboard** showing the frontend deployment.
- Open the `/docs` Swagger UI of the FastAPI app to show the API endpoints.

**[Audio / Voiceover]**
> "Finally, the application is fully deployed to the cloud."
>
> "The FastAPI backend is hosted on Railway, which automatically pulls from GitHub and serves the REST API. You can see the Swagger documentation here, exposing endpoints like `/recommendations` and `/health`."
>
> "The frontend is deployed on Streamlit Community Cloud. We also implemented a Parquet caching system, which compresses the 51,000-record Hugging Face dataset into a tiny, highly efficient offline file to ensure lightning-fast cold boots on the cloud."
>
> "That wraps up Milestone 1 of the Zomato AI Recommender. Thank you for watching!"

---

### 💡 Tips for Recording
- **Resolution:** Record in 1080p so the code and UI text are readable.
- **Pacing:** Don't rush when clicking through the UI; give the viewer a second to read the AI explanations.
- **Environment:** Make sure to run `gh auth login` and `git push` so your latest code is live before recording!
