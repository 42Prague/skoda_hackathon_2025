# Škoda Smart Stream - Web Application

This is the Next.js web application for the Škoda Smart Stream (S³) platform.

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
npm run build
npm start
```

## Project Structure

- `src/app/` - Next.js App Router pages
- `src/components/` - Reusable React components
- `src/context/` - React context providers (Auth, Theme)
- `src/data/` - Generated JSON data files (from Python ingestion)

## Key Features

- Employee search and filtering
- Individual employee profiles with skill gaps
- Learning feed with 10,000+ courses
- Analytics dashboard
- Department overview
- Documentation and help pages

## Tech Stack

- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- Recharts (data visualization)
- Lucide React (icons)
