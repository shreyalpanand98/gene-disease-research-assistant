# Hosted capstone demo

The Render Blueprint in `render.yaml` runs the Helix frontend and Python API as one web service. Render supplies the HTTPS link and listening port. GitHub hosts the code and can link to the deployed app from the README.

## Create the demo on Render

1. In the [Render dashboard](https://dashboard.render.com/), create a Blueprint from the GitHub branch that contains `render.yaml`.
2. At the Blueprint prompt, enter `OPENAI_API_KEY` and a unique `HELIX_DEMO_PASSWORD` of at least 16 characters. Enter both in Render's dashboard. These values are omitted from the repository. A dedicated OpenAI project key makes it easier to track demo usage and rotate the key afterward.
3. After deployment, open the assigned HTTPS URL. The browser will prompt for the username `helix` and your demo password. Share the password privately with evaluators.
4. Submit a short question such as “What does penetrance mean?” and verify that the answer links to its source. Open the URL in a private browser window to confirm that it requires the password. Add the verified HTTPS URL to the GitHub README as **Open Helix**.

The Blueprint uses Render's free tier. The first visit after the service has been idle may take about a minute. Conversations and results are held in memory and disappear on a restart. [Render free tier](https://render.com/docs/free)

The separate `/healthz` endpoint exposes only the server's ready status. The demo password protects the app and the research API. The backend checks the configured host and origin and sets HTTPS-only browser session cookies. Local development still starts on `127.0.0.1` with `python web_server.py`.
