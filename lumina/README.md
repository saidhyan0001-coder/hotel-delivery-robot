# Lumina AI - Production-Ready AI Assistant Web App

Lumina AI is a modern, high-performance, and feature-rich AI chatbot web application inspired by ChatGPT and Gemini. It features persistent conversations, real-time streaming, user authentication, dark/light mode, markdown rendering, and clean security architecture.

---

## 🌟 Key Features

- **Real-Time Token Streaming**: Watch Lumina think and stream responses progressively.
- **Persistent Conversation History**: Sessions, titles, and messages are automatically saved per user.
- **Authentication**: Secure registration and login using NextAuth.js and bcrypt password hashing.
- **Responsive Mobile & Desktop Layout**: Sleek left sidebar on desktop that converts into a drawer on mobile devices.
- **Markdown & Code Support**: Full markdown rendering including formatted tables, lists, and code blocks.
- **Message Management**: Copy AI responses, regenerate replies, and stop generation on-demand.
- **Theme Support**: Seamless Dark Mode and Light Mode theme toggle.
- **Prompt Suggestions**: Actionable suggestion cards on empty chat screen to jumpstart conversations.

---

## 🏗 Tech Stack

- **Framework**: [Next.js 16 (App Router)](https://nextjs.org/)
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS v4](https://tailwindcss.com/)
- **Database**: [SQLite](https://www.sqlite.org/) (via [Prisma ORM](https://www.prisma.io/))
- **Auth**: [NextAuth.js](https://next-auth.js.org/)
- **AI Integration**: [@ai-sdk/openai](https://sdk.vercel.ai/docs)
- **Icons & Markdown**: Lucide React & React Markdown

---

## 🚀 Environment Variables

Create a `.env` file in the `lumina` directory:

```env
DATABASE_URL="file:./dev.db"
AI_API_KEY="your-openai-or-compatible-api-key"
NEXTAUTH_SECRET="your-super-secret-key"
NEXTAUTH_URL="http://localhost:3000"
```

---

## 🛠 Local Setup & Running

1. **Navigate to project directory**:
   ```bash
   cd lumina
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Initialize Database**:
   ```bash
   npx prisma db push
   ```

4. **Start Development Server**:
   ```bash
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔒 Security Architecture

- **Server-Side Secrets**: API keys (`AI_API_KEY`) are NEVER exposed to the frontend bundle. All AI requests pass through the Next.js `/api/chat` route.
- **Authorization**: All conversation endpoints verify the user's active NextAuth session before serving data.
- **Password Security**: User passwords are encrypted with `bcryptjs` before being stored in the database.
