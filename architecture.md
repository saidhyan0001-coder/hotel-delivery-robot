# Architecture Document: Lumina AI

## 1. System Overview
Lumina AI follows a standard modern full-stack web architecture with a separation between the client interface and the secure server backend that communicates with the AI Provider and Database.

## 2. Technology Stack
- **Frontend Framework**: Next.js (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS & Framer Motion (for animations)
- **UI Components**: Radix UI primitives or shadcn/ui for accessible, premium components
- **Backend**: Next.js API Routes (Server Actions / Route Handlers)
- **Database**: PostgreSQL
- **ORM**: Prisma
- **Authentication**: NextAuth.js (Auth.js) for secure session management and credential/OAuth handling.
- **AI SDK**: Vercel AI SDK for handling streaming responses seamlessly.

## 3. Data Flow
1. **User Action**: User sends a message via the UI.
2. **Backend Request**: The frontend makes a POST request to a Next.js API route (`/api/chat`).
3. **Authentication Check**: The API route verifies the user's session.
4. **Database Save (User Message)**: The user's message is persisted to PostgreSQL via Prisma.
5. **AI Provider Call**: The backend securely calls the AI Provider (e.g., OpenAI, Anthropic, or Gemini) using the server-side API key.
6. **Streaming Response**: The AI Provider streams the response back to the Next.js backend, which forwards the stream to the frontend using the Vercel AI SDK (`streamText` or `StreamingTextResponse`).
7. **Database Save (AI Message)**: Once the stream completes, the final assistant message is saved to the database.

## 4. Database Schema (Prisma)
- **User**: `id`, `email`, `passwordHash`, `createdAt`, `updatedAt`
- **Conversation**: `id`, `userId` (relation to User), `title`, `createdAt`, `updatedAt`
- **Message**: `id`, `conversationId` (relation to Conversation), `role` (enum: user, assistant, system), `content`, `createdAt`

## 5. Security Architecture
- **API Keys**: Stored in `.env` and only accessed server-side.
- **Passwords**: Hashed using bcrypt.
- **Data Access**: Users can only fetch and mutate conversations and messages tied to their own `userId`.
- **Input Validation**: using Zod for API endpoints.

## 6. Deployment
- **Hosting**: Vercel (recommended for Next.js and streaming support) or a standard Node.js server.
- **Database**: Supabase, Neon, or local Postgres.
