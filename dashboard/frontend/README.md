# College-Bot Analytics Dashboard - Frontend

A modern React-based analytics dashboard with authentication for the College-Bot project.

## Project Structure

\`\`\`
src/
├── pages/
│   ├── Login.tsx          # Login page
│   ├── Register.tsx       # Registration page
│   └── Dashboard.tsx      # Main dashboard (protected)
├── components/
│   ├── Button.tsx         # Reusable button component
│   ├── Input.tsx          # Reusable input component
│   └── ProtectedRoute.tsx # Route protection wrapper
├── contexts/
│   └── AuthContext.tsx    # Authentication state management
├── lib/
│   └── api.ts             # API client for backend calls
├── App.tsx                # Main app component with routing
├── main.tsx               # React entry point
└── index.css              # Global styles
\`\`\`

## Setup Instructions

### 1. Install Dependencies

\`\`\`bash
npm install
\`\`\`

### 2. Configure Environment Variables

Create a \`.env.local\` file in the root directory:

\`\`\`env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=College-Bot Analytics
\`\`\`

### 3. Start Development Server

\`\`\`bash
npm run dev
\`\`\`

The application will be available at \`http://localhost:5173\`

### 4. Build for Production

\`\`\`bash
npm run build
\`\`\`

## Features

- ✅ User Authentication (Login/Register )
- ✅ JWT Token Management
- ✅ Protected Routes
- ✅ Responsive Design
- ✅ Dark Mode UI
- ✅ API Integration
- ✅ Auto-login on Page Refresh
- ✅ Logout Functionality

## Authentication Flow

1. User registers or logs in
2. Backend returns JWT token
3. Token stored in localStorage
4. Token sent with all API requests
5. Protected routes redirect to login if not authenticated

## API Endpoints

- \`POST /api/auth/register\` - Register new user
- \`POST /api/auth/login\` - Login user
- \`GET /api/auth/verify\` - Verify JWT token
- \`GET /api/dashboard/metrics\` - Get dashboard metrics

## Technologies Used

- React 18
- TypeScript
- React Router v6
- Tailwind CSS
- Vite
- Axios
- Lucide React Icons

## Development

### Available Scripts

- \`npm run dev\` - Start development server
- \`npm run build\` - Build for production
- \`npm run preview\` - Preview production build

## Notes

- Make sure the backend API is running on \`http://localhost:8000\`
- Update \`VITE_API_URL\` in \`.env.local\` if your backend is on a different URL
- The application uses localStorage for token persistence
- Tokens expire after 30 minutes (configurable on backend )

## Support

For issues or questions, please refer to the main project documentation.
\`\`\`

---

## Summary

You now have **ALL the code** for every frontend file. Here's what to do:

1. **Create the folder structure** as shown in the FRONTEND_COMPLETE_SETUP.md
2. **Copy and paste the code** from this document into each file
3. **Run `npm install`** to install dependencies
4. **Run `npm run dev`** to start the development server

All files are error-free and ready to use!