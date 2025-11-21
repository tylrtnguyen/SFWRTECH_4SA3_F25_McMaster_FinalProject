# JobTrust Frontend

A modern Next.js 15+ dashboard for JobTrust - a platform to help job seekers in their job search journey.

## Features

- **Authentication**: Secure sign up and login with Supabase Auth
- **Protected Routes**: Dashboard routes require authentication
- **Dashboard Overview**: Comprehensive dashboard with key metrics and statistics
- **Job Search**: Search jobs by URL, manual input, or file upload
- **Job Analysis**: Analyze job postings for fraud detection and scoring
- **Match Score**: Calculate job match scores based on resume
- **Resume Recommendations**: Get personalized resume tips
- **Job Tracking**: Bookmark and track jobs through the application process
- **User Settings**: Manage profile and preferences
- **Dark Mode**: Theme toggle for light/dark mode

## Tech Stack

- **Next.js 15+**: React framework with App Router
- **TypeScript**: Type-safe development
- **Supabase**: Authentication and database
- **shadcn/ui**: High-quality component library
- **Tailwind CSS**: Utility-first CSS framework
- **Radix UI**: Accessible component primitives
- **Lucide React**: Icon library

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn or pnpm

### Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

2. Run the development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Build for Production

```bash
npm run build
npm start
```

## Color Palette

The dashboard uses the JobTrust color palette:

### Light Mode
- **Primary**: #0a66c2 (Primary buttons, CTAs, active states)
- **Primary Hover**: #084d92 (Hover state for primary buttons)
- **Secondary**: #00b2a9 (Secondary buttons, accent elements)
- **Success**: #36B37E (Success messages, positive indicators)
- **Background Primary**: #FFFFFF (Main page background)
- **Background Secondary**: #F4F5F7 (Cards, panels)
- **Text Primary**: #172B4D (Main body text, headings)
- **Text Secondary**: #5E6C84 (Supporting text, labels)
- **Text Tertiary**: #8993A4 (Disabled text, placeholders)
- **Border Default**: #DFE1E6 (Input borders, dividers)
- **Accent Warning**: #eed971 (Warnings, notifications)

### Dark Mode
- **Primary**: #3d8fd7 (Primary buttons, CTAs)
- **Primary Hover**: #2a7abc (Hover state)
- **Secondary**: #4dd4cb (Secondary buttons, accents)
- **Success**: #57D9A3 (Success messages)
- **Background Primary**: #1a1d23 (Main page background)
- **Background Secondary**: #22262e (Cards, panels)
- **Background Tertiary**: #2d323c (Modals, dropdowns)
- **Text Primary**: #e4e6eb (Main body text)
- **Text Secondary**: #b0b3b8 (Supporting text)
- **Text Tertiary**: #8a8d91 (Disabled text)
- **Border Default**: #3a3f4b (Borders, dividers)
- **Accent Warning**: #d9c760 (Warnings, notifications)

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── dashboard/         # Dashboard pages
│   ├── layout.tsx          # Root layout
│   ├── page.tsx           # Home page (redirects to dashboard)
│   └── globals.css        # Global styles with color palette
├── components/             # React components
│   ├── ui/                # shadcn/ui components
│   ├── sidebar.tsx        # Sidebar navigation
│   ├── navbar.tsx         # Top navigation bar
│   ├── dashboard-layout.tsx # Dashboard layout wrapper
│   ├── job-search.tsx     # Job search component
│   ├── stat-card.tsx      # Statistics card component
│   └── theme-provider.tsx # Theme provider for dark mode
├── lib/                    # Utility functions
│   └── utils.ts          # Utility functions (cn helper)
└── public/                # Static assets
```

## Environment Variables

Create a `.env.local` file in the root directory:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your-supabase-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### Getting Supabase Credentials

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings** → **API**
4. Copy the **Project URL** and set it as `NEXT_PUBLIC_SUPABASE_URL`
5. Copy the **anon/public** key and set it as `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Configuring Supabase Auth

**Important**: This application uses password-based authentication without email confirmation.

See [SUPABASE_AUTH_SETUP.md](./SUPABASE_AUTH_SETUP.md) for detailed instructions on configuring Supabase Auth settings.

## API Integration

The frontend is designed to work with the JobTrust backend API. Update the API URL in your environment variables to connect to your backend instance.

## License

This project is part of a software architecture course final project.

