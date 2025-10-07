UI (React) — quick start

From the `ui` directory (Windows cmd.exe):

1. Install dependencies:

   npm install

2. Start the dev server:

   npm start

Notes:
- The app expects the API at http://127.0.0.1:8000 by default. If your API is at a different host/port, update the axios calls in `src/App.js`.
- If you don't have `react-scripts`, install it via the package.json devDependencies above or run `npx create-react-app`.
# Bug Triage UI

A modern React frontend for your bug triage automation project.

## Features
- Submit bug summary and description
- Get predictions for assignee, category, and severity
- Material UI design

## Setup
1. Install dependencies:
   ```sh
   npm install
   ```
2. Start the development server:
   ```sh
   npm start
   ```
3. The app will run at http://localhost:3000

## Backend
Make sure your FastAPI backend is running at http://127.0.0.1:8000

## Customization
You can extend the UI to show model stats, bug history, and more.
