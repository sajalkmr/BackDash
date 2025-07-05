# GoQuant Backtesting Platform

A modern backtesting platform for quantitative trading strategies, built with React, FastAPI, and TypeScript.

## Features

- **Interactive Strategy Builder**: Drag-and-drop interface for building trading strategies
- **Real-time Backtesting**: Fast backtesting engine with instant feedback
- **Advanced Analytics**:
  - Equity curves and drawdown analysis
  - Performance metrics (Sharpe, Sortino, etc.)
  - Trade list and statistics
  - Risk analytics and visualizations
  - Benchmark comparison
- **Technical Indicators**: EMA, RSI, MACD, and more
- **Data Management**: Support for both real and mock market data

## Tech Stack

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- React DnD for drag-and-drop
- Lightweight charting libraries

### Backend
- FastAPI (Python)
- Pandas for data processing
- NumPy for calculations
- SQLite for data storage

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.12+
- pip

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

3. Set up Python virtual environment and install backend dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Data Setup
The application requires market data in CSV format. Due to file size limitations, data files are not included in the repository.

1. Download the sample data:
   - For testing, use the mock data provided in `src/data/mockData.ts`
   - For real data, place your CSV files in:
     - `public/dow_jones_data.csv` (for static serving)
     - `src/data/dow_jones_data.csv` (for direct import)

### Running the Application

1. Start the backend server:
```bash
cd backend
uvicorn main:app --reload
```

2. Start the frontend development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── models/         # Data models
│   │   └── services/       # Business logic
│   └── data/               # Market data
├── src/                    # React frontend
│   ├── components/         # React components
│   │   ├── analytics/      # Analytics components
│   │   └── strategy/       # Strategy builder components
│   ├── data/              # Data loaders
│   ├── types/             # TypeScript types
│   └── utils/             # Utility functions
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
