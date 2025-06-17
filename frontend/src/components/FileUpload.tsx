import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import './FileUpload.css';

interface FileUploadProps {
  onUpload: (file: File, password?: string) => void;
  loading: boolean;
  error: string | null;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUpload, loading, error }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [password, setPassword] = useState('');
  const [showPasswordInput, setShowPasswordInput] = useState(false);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0]);
        setShowPasswordInput(false);
        setPassword('');
      }
    }
  });

  const handleUpload = () => {
    if (selectedFile) {
      onUpload(selectedFile, password || undefined);
    }
  };

  const handlePasswordSubmit = () => {
    if (selectedFile && password) {
      onUpload(selectedFile, password);
    }
  };

  return (
    <div className="file-upload-container">
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop the PDF file here...</p>
        ) : (
          <div className="dropzone-content">
            <div className="upload-icon">📄</div>
            <p>Drag & drop your NSDL CAS PDF file here, or click to select</p>
            <small>Only PDF files are accepted</small>
          </div>
        )}
      </div>

      {selectedFile && (
        <div className="file-selected">
          <div className="file-info">
            <strong>Selected file:</strong> {selectedFile.name}
            <br />
            <small>Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</small>
          </div>
          
          {!showPasswordInput && (
            <div className="upload-actions">
              <button 
                onClick={handleUpload} 
                disabled={loading}
                className="btn btn-primary"
              >
                {loading ? 'Processing...' : 'Upload & Analyze'}
              </button>
              <button 
                onClick={() => setShowPasswordInput(true)}
                className="btn btn-secondary"
              >
                Enter Password
              </button>
            </div>
          )}

          {showPasswordInput && (
            <div className="password-input">
              <label htmlFor="password">PDF Password:</label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter PDF password (usually your PAN)"
                onKeyPress={(e) => e.key === 'Enter' && handlePasswordSubmit()}
              />
              <div className="password-actions">
                <button 
                  onClick={handlePasswordSubmit}
                  disabled={loading || !password}
                  className="btn btn-primary"
                >
                  {loading ? 'Processing...' : 'Upload with Password'}
                </button>
                <button 
                  onClick={() => setShowPasswordInput(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
          {error.includes('password') && !showPasswordInput && (
            <button 
              onClick={() => setShowPasswordInput(true)}
              className="btn btn-link"
            >
              Enter Password
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default FileUpload;