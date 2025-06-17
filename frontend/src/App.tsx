import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import FileUpload from './components/FileUpload';
import PortfolioAnalysis from './components/PortfolioAnalysis';

interface PortfolioData {
  status: string;
  message: string;
  data: any;
}

interface AnalysisData {
  asset_allocation: Record<string, number>;
  sector_concentration: Record<string, number>;
  recommendations: string[];
}

function App() {
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (file: File, password?: string) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (password) {
        formData.append('password', password);
      }

      const response = await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/upload-cas`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setPortfolioData(response.data);
      
      // Automatically analyze portfolio after successful upload
      const analysisResponse = await axios.post(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/analyze-portfolio`,
        response.data.data
      );
      
      setAnalysis(analysisResponse.data.analysis);
    } catch (err: any) {
      console.error('Upload error:', err);
      if (err.response?.data?.error_type === 'password_required') {
        setError('Password required or incorrect password provided');
      } else {
        setError(err.response?.data?.message || 'Error uploading file');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Financial Planner</h1>
        <p>Upload your NSDL CAS PDF file to get personalized investment insights</p>
      </header>

      <main className="App-main">
        <div className="upload-section">
          <FileUpload 
            onUpload={handleFileUpload}
            loading={loading}
            error={error}
          />
        </div>

        {portfolioData && (
          <div className="results-section">
            <div className="upload-success">
              <h3>✅ File Processed Successfully</h3>
              <p>{portfolioData.message}</p>
              <div className="file-stats">
                <p>Pages: {portfolioData.data.total_pages}</p>
                <p>Content Length: {portfolioData.data.extracted_text_length} characters</p>
              </div>
            </div>
          </div>
        )}

        {analysis && (
          <PortfolioAnalysis analysis={analysis} />
        )}
      </main>
    </div>
  );
}

export default App;
