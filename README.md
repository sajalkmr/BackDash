# BackDash

A modern backtesting platform for quantitative trading strategies with visual strategy builder and comprehensive analytics.

## Features

- **Visual Strategy Builder**: Drag-and-drop interface for building trading strategies
- **Technical Indicators**: 9 indicators including SMA, EMA, RSI, MACD, Bollinger Bands, and more
- **Advanced Backtesting**: Event-driven engine with realistic market simulation
- **Real-time Analytics**: Performance metrics, equity curves, and risk analysis
- **Multiple Assets**: Support for major cryptocurrency pairs

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **Backend**: FastAPI (Python), Pandas, NumPy
- **API**: RESTful endpoints with comprehensive documentation

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.12+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sajalkmr/BackDash.git
cd BackDash
```

2. Install frontend dependencies:
```bash
npm install
```

3. Set up backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application

1. Start backend:
```bash
cd backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

2. Start frontend:
```bash
npm run dev
```

3. Access:
- Frontend: `http://localhost:5173`
- API Docs: `http://127.0.0.1:8000/docs`

## Project Structure

```
├── backend/          # FastAPI backend
│   ├── app/         # Application code
│   └── data/        # Market data
├── src/             # React frontend
│   ├── components/  # UI components
│   └── utils/       # Utilities
└── public/          # Static assets
```

## API Endpoints

- `/api/v1/strategy/*` - Strategy management and validation
- `/api/v1/data/*` - Market data endpoints
- `/api/v1/analytics/*` - Performance analytics

## License

MIT License
