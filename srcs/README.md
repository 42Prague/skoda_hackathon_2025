# S³ — Škoda Smart Stream

![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?logo=typescript)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

> **AI-powered Learning & Development Platform for Škoda Auto**

S³ is a comprehensive HR and learning management system that helps Škoda Auto identify skill gaps, recommend personalized learning paths, and track employee development. The platform uses real organizational data to provide actionable insights for both employees and HR managers.

## ✨ Features

### For Employees
- **Personalized Learning Feed** - Browse 10,000+ micro-learning modules across multiple categories
- **Skill Gap Visualization** - "Swiss Cheese" profile showing strengths and areas for improvement
- **Course Recommendations** - AI-powered suggestions based on your role and skill gaps
- **Progress Tracking** - Monitor your learning journey and completed courses
- **Search & Filter** - Find relevant courses quickly with advanced search

### For HR Managers
- **Employee Search** - Find employees with advanced filters (skill gaps, department, etc.)
- **Analytics Dashboard** - Comprehensive insights into workforce skills and learning trends
- **Department Overview** - Track skill health across departments
- **Module Assignment** - Assign courses directly to employees
- **Learning Analytics** - Track completion rates, popular courses, and top learners

## 🏗️ Architecture

The project consists of two main components:

1. **Data Ingestion Pipeline** (`src/s3/`) - Python scripts that process raw Škoda data files
2. **Web Application** (`web/`) - Next.js frontend with TypeScript

```
.
├── data/                    # Raw Škoda data files (Excel, TXT)
├── src/s3/                  # Python data processing pipeline
│   ├── ingest.py           # Main ingestion script
│   ├── loader.py           # Data loading utilities
│   └── ...
├── web/                     # Next.js web application
│   ├── src/
│   │   ├── app/            # Next.js app router pages
│   │   ├── components/     # React components
│   │   ├── context/        # React context providers
│   │   └── data/           # Generated JSON data files
│   └── ...
└── artifacts/               # Generated artifacts (translations, vector store)
```

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **Poetry** (for Python dependency management)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Skoda.git
   cd Skoda
   ```

2. **Set up Python environment**
   ```bash
   # Install Poetry if you haven't already
   curl -sSL https://install.python-poetry.org | python3 -
   
   # Install Python dependencies
   poetry install
   ```

3. **Process the data**
   ```bash
   # This will generate users.json, courses.json, and other data files
   poetry run python -m src.s3.ingest
   ```

4. **Set up the web application**
   ```bash
   cd web
   npm install
   ```

5. **Configure environment variables**

   Create a `.env.local` file inside the `web/` directory:
   ```bash
   cd web
   cp .env.local.example .env.local  # if the example file exists
   ```
   Or create it manually with:
   ```
   NEXT_PUBLIC_LOGIN_USERNAME=Maria
   NEXT_PUBLIC_LOGIN_PASSWORD=Any
   ```
   (Use your own secure credentials in production.)

6. **Run the development server**
   ```bash
   npm run dev
   ```

7. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Demo Credentials

For the login page, you can use any username and password - it's a demo system.

## 🚀 Deployment

### Production Deployment with Apache

To deploy the application on an Ubuntu server with Apache as a reverse proxy:

1. **Clone and navigate to the project**
   ```bash
   git clone https://github.com/ExceptedPrism3/Skoda.git
   cd Skoda
   ```

2. **Run the automated setup script**
   ```bash
   chmod +x setup-server.sh
   ./setup-server.sh
   ```

   The script will:
   - Install Node.js 20+ and Python dependencies
   - Set up the Python virtual environment
   - Process data files (if present in `data/` folder)
   - Build the Next.js application
   - Configure PM2 for process management
   - Set up Apache reverse proxy configuration
   - Start the application

3. **Manual setup (if needed)**

   If you prefer manual setup or need to customize:

   ```bash
   # Set up Python environment
   python3 -m venv venv
   source venv/bin/activate
   pip install pandas transformers scikit-learn numpy scipy openpyxl sentencepiece pydantic
   
   # Process data
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   python -m s3.ingest
   
   # Build Next.js app
   cd web
   npm install
   NEXT_PUBLIC_BASE_PATH=/skoda npm run build
   cd ..
   
   # Start with PM2
   pm2 start ecosystem.config.js
   pm2 save
   pm2 startup  # Follow the output to enable auto-start on boot
   ```

4. **Apache Configuration**

   The setup script automatically configures Apache. If you have an existing SSL VirtualHost, it will add the `/skoda` location blocks to it. Otherwise, it creates a new HTTP-only configuration.

   The app runs on port **3002** by default (configurable in `ecosystem.config.js`).

5. **Access the application**

   - HTTP: `http://your-server-ip/skoda`
   - HTTPS: `https://your-server-ip/skoda` (if SSL is configured)

### Important Notes

- **Port Configuration**: The app uses port 3002 by default. Make sure this port is available or update `ecosystem.config.js` and Apache configuration accordingly.
- **Base Path**: The application is configured to run under `/skoda` subpath. To change this, update `NEXT_PUBLIC_BASE_PATH` in both the build command and `ecosystem.config.js`.
- **Login Credentials**: Set `NEXT_PUBLIC_LOGIN_USERNAME` and `NEXT_PUBLIC_LOGIN_PASSWORD` (preferably via `.env.local`) before building so the login page can validate against them.
- **SSL/HTTPS**: If you have SSL certificates, ensure your Apache SSL VirtualHost includes the `/skoda` location blocks (the setup script handles this automatically).
- **Data Files**: Place your data files in the `data/` folder before running the setup script, or run the data ingestion manually after setup.

### Useful Commands

```bash
# PM2 Management
pm2 status              # Check app status
pm2 logs skoda-web      # View logs
pm2 restart skoda-web   # Restart app
pm2 stop skoda-web      # Stop app

# Apache Logs
sudo tail -f /var/log/apache2/skoda_error.log
sudo tail -f /var/log/apache2/skoda_access.log

# Rebuild after code changes
cd web
NEXT_PUBLIC_BASE_PATH=/skoda npm run build
pm2 restart skoda-web
```

## 📊 Data Sources

The platform uses real Škoda Auto data from multiple sources:

- **ERP Data** (`ERP_SK1.Start_month - SE.xlsx`) - Employee profiles, roles, education
- **Training History** (`ZHRPD_VZD_STA_007.xlsx`, `ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx`) - Course completions
- **Degreed Platform** (`Degreed.xlsx`) - External learning platform data
- **Skill Mapping** (`Skill_mapping.xlsx`) - Course-to-skill mappings
- **Organizational Hierarchy** (`RLS.sa_org_hierarchy - SE.xlsx`) - Department structure
- **Course Descriptions** (TXT files) - Multi-language course content
- **Job Descriptions** (RE_RHRHAZ00 files) - Role-specific responsibilities

## 🎯 Key Pages

- **`/`** - Employee search with filters
- **`/employee/[id]`** - Individual employee profile with skills and recommendations
- **`/feed`** - Daily micro-challenges and course catalog
- **`/analytics`** - Comprehensive analytics dashboard
- **`/department`** - Department overview and skill health
- **`/documentation`** - Platform documentation and help
- **`/settings`** - User settings

## 🛠️ Technology Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Recharts** - Data visualization
- **Lucide React** - Icon library

### Backend/Data Processing
- **Python 3.11+** - Data processing
- **Pandas** - Data manipulation
- **Transformers** - Czech-to-English translation
- **scikit-learn** - Vector embeddings and similarity

## 📁 Project Structure

```
Skoda/
├── data/                          # Raw data files (Excel, TXT, PDF)
├── src/s3/                        # Python data processing
│   ├── ingest.py                 # Main ingestion script
│   ├── loader.py                 # File loading utilities
│   ├── chunker.py                # Text chunking
│   ├── tagger.py                 # Content tagging
│   ├── embedder.py               # Text embeddings
│   ├── vector_store.py           # Vector storage
│   └── ...
├── web/                           # Next.js application
│   ├── src/
│   │   ├── app/                  # Pages (App Router)
│   │   │   ├── page.tsx         # Employee search
│   │   │   ├── employee/[id]/   # Employee detail
│   │   │   ├── feed/            # Learning feed
│   │   │   ├── analytics/       # Analytics dashboard
│   │   │   └── ...
│   │   ├── components/          # React components
│   │   ├── context/             # Context providers
│   │   └── data/                # Generated JSON data
│   ├── package.json
│   └── ...
├── artifacts/                     # Generated artifacts
│   ├── translation_cache.json   # Translation cache
│   └── vector_store/            # Vector embeddings
└── README.md
```

## 🔄 Data Processing Workflow

1. **Load Raw Data** - Read Excel and text files from `data/` directory
2. **Translate** - Convert Czech text to English using translation models
3. **Process** - Extract courses, users, skills, and relationships
4. **Enrich** - Add job descriptions, course descriptions, and metadata
5. **Export** - Generate JSON files for the web application

Run the ingestion script whenever you update the source data:
```bash
poetry run python -m src.s3.ingest
```

## 🎨 Design Features

- **Dark Mode Support** - Full dark/light theme support
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Smooth Animations** - Polished UI with smooth transitions
- **Accessibility** - WCAG-compliant design patterns

## 📈 Analytics Features

- Department distribution and skill health
- Top skills and proficiency levels
- Learning activity trends
- Course completion rates
- Top learners leaderboard
- Popular courses analysis

## 🔐 Authentication

The platform uses a simple demo authentication system. In production, this would integrate with Škoda's SSO system.

## 📝 License

This project is released under the MIT License. See `LICENSE` file for details.

## 🤝 Contributing

This is a hackathon project for Škoda Auto. For questions or contributions, please open an issue or contact the team.

## 🙏 Acknowledgments

- **Škoda Auto** - For providing the dataset and hackathon opportunity
- **42 Heilbronn × 42 Prague** - Hackathon organization
- Built with ❤️ for better employee learning experiences

---

**Note**: This is a prototype/demo system. For production use, additional security, performance optimizations, and integrations would be required.
