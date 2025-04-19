# AutoMail - Your Second Brain for Email

![AutoMail Logo](frontend/public/logo.png)

AutoMail is an AI-powered email management system that transforms your inbox into an intelligent workspace. By analyzing your emails, AutoMail extracts meaningful insights, automates repetitive tasks, and helps you stay on top of your communications.

## Features

### 📊 Email Analytics
- **Financial Tracking**: Automatically extracts and categorizes financial transactions from your emails
- **Meeting Detection**: Identifies upcoming meetings and appointments from your emails
- **Todo Extraction**: Creates actionable todo items based on the content of your emails
- **Reply Suggestions**: Identifies emails that need your attention and suggests responses

### 🤖 AI-Powered Automation
- **Auto-Reply Drafts**: Generates contextually appropriate reply drafts for emails that need responses
- **Email Tagging**: Automatically categorizes and labels emails based on their content
- **Reminder Extraction**: Identifies deadlines and important dates mentioned in emails

### 💼 Smart Dashboard
- **Recent Emails**: View your most recent emails with smart time formatting
- **Financial Overview**: Track your income, expenses, and financial health
- **Meeting Calendar**: Never miss an appointment with automatic meeting extraction
- **Todo List**: Stay organized with automatically generated action items

## Architecture

AutoMail is built with a modern tech stack:

### Backend
- **FastAPI**: High-performance API framework for Python
- **Google Gmail API**: For email access and management
- **Claude AI**: For intelligent email analysis and content generation
- **PostgreSQL & MongoDB**: For data storage and retrieval

### Frontend
- **Next.js**: React framework for building the user interface
- **Tailwind CSS**: For responsive and beautiful UI components
- **TypeScript**: For type-safe code and better developer experience

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL
- MongoDB
- Google API credentials
- Anthropic Claude API key

### Installation

#### Backend Setup
1. Clone the repository
   ```
   git clone https://github.com/yourusername/automail.git
   cd automail/backend
   ```

2. Create a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables
   ```
   cp .env.example .env
   # Edit .env with your API keys and database credentials
   ```

5. Run the backend server
   ```
   python main.py
   ```

#### Frontend Setup
1. Navigate to the frontend directory
   ```
   cd ../frontend
   ```

2. Install dependencies
   ```
   npm install
   ```

3. Run the development server
   ```
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## API Endpoints

### Email Analytics
- `GET /email-analytics`: Get comprehensive analytics from your emails

### Recent Emails
- `GET /recent-emails`: Get your most recent emails with formatted data

### Email Processing
- `POST /emails/process`: Process recent emails through all microservices
- `POST /emails/process-one/{email_id}`: Process a specific email
- `POST /emails/webhook`: Webhook for Gmail push notifications

### Auto-Reply
- `POST /auto-reply/run`: Generate auto-reply drafts for emails

### Reminders
- `GET /reminders/extract`: Extract reminders and todos from emails

### Finance
- `GET /finance/analyze`: Analyze financial data from emails

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Anthropic Claude](https://www.anthropic.com/) for AI capabilities
- [Google Gmail API](https://developers.google.com/gmail/api) for email integration
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Next.js](https://nextjs.org/) for the frontend framework
- [Tailwind CSS](https://tailwindcss.com/) for styling
