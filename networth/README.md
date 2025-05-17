# NetWorth Visualization

A modern single-page application for interactive data visualization with authentication capabilities.

## Features

- 🔐 **Authentication System**
  - Sign-in and Sign-up functionality using Supabase
  - Modal-based authentication flow
  - Secure user session management

- 🎨 **Modern UI Components**
  - Built with shadcn/ui components
  - Clean and consistent design system
  - Responsive layout

- 📊 **Interactive Data Visualization**
  - Powered by Visx for high-performance visualizations
  - Interactive zoom and pan capabilities
  - Real-time data point tracking
  - Customizable chart components

## Project Structure

```
networth/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn components
│   │   ├── auth/         # authentication components
│   │   └── visualization/# chart components
│   ├── lib/
│   │   ├── supabase.ts   # Supabase client configuration
│   │   └── utils.ts      # utility functions
│   └── App.tsx           # main application component
├── public/
└── package.json
```

## Tech Stack

- **Frontend Framework**: React 18
- **Authentication**: Supabase
- **UI Components**: shadcn/ui
- **Data Visualization**: Visx
- **Styling**: Tailwind CSS
- **Build Tool**: Vite
- **Language**: TypeScript

## Getting Started

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set up your Supabase project and add the credentials to your environment variables
4. Start the development server:
   ```bash
   npm run dev
   ```

## Authentication Flow

1. Users are presented with a modal for sign-in/sign-up on initial load
2. After successful authentication, the main visualization interface is displayed
3. User session is maintained using Supabase authentication

## Visualization Features

- Interactive zoom and pan functionality
- Real-time data point tracking
- Customizable chart components
- Responsive design that adapts to different screen sizes

## Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

MIT
