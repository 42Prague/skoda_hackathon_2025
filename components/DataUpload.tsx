import React, { useState, useCallback } from 'react';
import { useTranslation } from '../contexts/LanguageContext';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || (process.env.VITE_API_URL) || 'http://localhost:8000';

interface UploadResult {
  success: boolean;
  format_detected?: string;
  encoding_used?: string;
  employees_processed?: number;
  skills_extracted?: number;
  time_range?: string;
  validation_errors?: string[];
  validation_warnings?: string[];
  files_generated?: {
    employees_csv: string;
    skill_matrix_csv: string;
    skill_evolution_csv: string;
  };
  error?: string;
  columns_found?: string[];
  suggestion?: string;
}

export const DataUpload: React.FC = () => {
  const { language, setLanguage, t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [dragActive, setDragActive] = useState(false);

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  }, []);

  // Handle file input change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  // Upload file
  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/api/upload-data?language=${language}`, {
        method: 'POST',
        body: formData,
      });

      const data: UploadResult = await response.json();
      setResult(data);

      if (data.success) {
        // Trigger data reload in parent components (via event)
        window.dispatchEvent(new Event('dataUploaded'));
      }
    } catch (error) {
      console.error('Upload failed:', error);
      setResult({
        success: false,
        error: 'Network error. Please ensure backend is running on port 8000.'
      });
    } finally {
      setUploading(false);
    }
  };

  // Language toggle
  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'cz' : 'en');
  };

  // Format detection badge
  const getFormatBadge = (format: string) => {
    const formatNames: { [key: string]: string } = {
      'format1_hr': t('format_hr_system'),
      'format2_planning': t('format_planning'),
      'format3_lms': t('format_lms'),
      'format4_projects': t('format_projects'),
      'format5_qualifications': t('format_qualifications')
    };
    return formatNames[format] || format;
  };

  return (
    <div style={styles.container}>
      {/* Language Toggle */}
      <div style={styles.languageToggle}>
        <button onClick={toggleLanguage} style={styles.langButton}>
          {language === 'en' ? '🇬🇧 EN' : '🇨🇿 CZ'}
          <span style={styles.langButtonText}>
            {t('switch_language')}
          </span>
        </button>
      </div>

      <h2 style={styles.title}>{t('upload_title')}</h2>

      {/* Drag & Drop Zone */}
      <div
        style={{
          ...styles.dropzone,
          ...(dragActive ? styles.dropzoneActive : {}),
          ...(file ? styles.dropzoneHasFile : {})
        }}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div style={styles.dropzoneContent}>
          <div style={styles.uploadIcon}>📄</div>
          <p style={styles.dropzoneText}>
            {file ? file.name : t('upload_description')}
          </p>

          {/* File Input */}
          <label htmlFor="file-upload" style={styles.fileLabel}>
            <span style={styles.fileButton}>{t('upload_button')}</span>
            <input
              id="file-upload"
              type="file"
              accept=".csv,.xlsx,.xls,.pdf"
              onChange={handleFileChange}
              style={styles.fileInput}
            />
          </label>

          {file && (
            <div style={styles.fileInfo}>
              <p style={styles.fileName}>📎 {file.name}</p>
              <p style={styles.fileSize}>
                {(file.size / 1024).toFixed(2)} KB
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Upload Button */}
      {file && !uploading && !result && (
        <button
          onClick={handleUpload}
          style={styles.uploadButton}
        >
          🚀 {t('upload_button')}
        </button>
      )}

      {/* Loading */}
      {uploading && (
        <div style={styles.loading}>
          <div style={styles.spinner}></div>
          <p>{t('upload_processing')}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div style={{
          ...styles.result,
          ...(result.success ? styles.resultSuccess : styles.resultError)
        }}>
          {result.success ? (
            <>
              <h3 style={styles.resultTitle}>✅ {t('upload_success')}</h3>

              {/* Format Detection */}
              {result.format_detected && (
                <div style={styles.resultRow}>
                  <strong>{t('format_detected')}:</strong>
                  <span style={styles.badge}>
                    {getFormatBadge(result.format_detected)}
                  </span>
                </div>
              )}

              {/* Statistics */}
              <div style={styles.stats}>
                <div style={styles.statCard}>
                  <div style={styles.statValue}>{result.employees_processed}</div>
                  <div style={styles.statLabel}>{t('employees_processed')}</div>
                </div>
                <div style={styles.statCard}>
                  <div style={styles.statValue}>{result.skills_extracted}</div>
                  <div style={styles.statLabel}>{t('skills_extracted')}</div>
                </div>
                <div style={styles.statCard}>
                  <div style={styles.statValue}>{result.time_range}</div>
                  <div style={styles.statLabel}>{t('time_range')}</div>
                </div>
              </div>

              {/* Warnings */}
              {result.validation_warnings && result.validation_warnings.length > 0 && (
                <div style={styles.warnings}>
                  <p><strong>⚠️ Warnings:</strong></p>
                  <ul>
                    {result.validation_warnings.map((warning, idx) => (
                      <li key={idx}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Success Message */}
              <p style={styles.successMessage}>
                Data successfully uploaded and analyzed. Genome and evolution visualizations have been updated.
              </p>
            </>
          ) : (
            <>
              <h3 style={styles.resultTitle}>❌ {t('upload_error')}</h3>

              {result.error && (
                <p style={styles.errorMessage}>{result.error}</p>
              )}

              {result.columns_found && result.columns_found.length > 0 && (
                <div style={styles.errorDetails}>
                  <p><strong>Columns found in file:</strong></p>
                  <code style={styles.code}>
                    {result.columns_found.join(', ')}
                  </code>
                </div>
              )}

              {result.suggestion && (
                <p style={styles.suggestion}>
                  <strong>💡 Suggestion:</strong> {result.suggestion}
                </p>
              )}

              {result.validation_errors && result.validation_errors.length > 0 && (
                <div style={styles.errors}>
                  <p><strong>{t('validation_errors')}:</strong></p>
                  <ul>
                    {result.validation_errors.map((error, idx) => (
                      <li key={idx}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {/* Retry Button */}
          <button
            onClick={() => {
              setFile(null);
              setResult(null);
            }}
            style={styles.retryButton}
          >
            ↺ Upload Another File
          </button>
        </div>
      )}

      {/* Supported Formats Info */}
      <details style={styles.details}>
        <summary style={styles.summary}>📋 Supported Formats (5 formats)</summary>
        <div style={styles.formatList}>
          <div style={styles.formatItem}>
            <strong>1. Czech HR System</strong>
            <p>VP, TO, ID obj., ITyp, STyp, Začátek, Konec</p>
          </div>
          <div style={styles.formatItem}>
            <strong>2. Planning System</strong>
            <p>Var.plánu, Typ obj., ID objektu, Subtyp, Platí od, Platí do</p>
          </div>
          <div style={styles.formatItem}>
            <strong>3. Learning Management System (LMS)</strong>
            <p>Employee ID, Content Title, Content Type, Completed Date</p>
          </div>
          <div style={styles.formatItem}>
            <strong>4. Project/Task Data</strong>
            <p>ID P, Počát.datum, Koncové datum, ID Q, Název Q</p>
          </div>
          <div style={styles.formatItem}>
            <strong>5. Qualifications</strong>
            <p>ID kvalifikace, Kvalifikace, Číslo FM</p>
          </div>
          <p style={styles.formatNote}>
            <strong>Auto-detection:</strong> System automatically detects format based on column headers. At least 60% of required columns must be present.
          </p>
        </div>
      </details>
    </div>
  );
};

// Inline styles (for simplicity - can be moved to CSS modules)
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '20px',
    fontFamily: 'system-ui, -apple-system, sans-serif'
  },
  languageToggle: {
    display: 'flex',
    justifyContent: 'flex-end',
    marginBottom: '20px'
  },
  langButton: {
    padding: '8px 16px',
    fontSize: '14px',
    border: '1px solid #ccc',
    borderRadius: '6px',
    background: 'white',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    transition: 'all 0.2s'
  },
  langButtonText: {
    marginLeft: '4px'
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '20px',
    color: '#333'
  },
  dropzone: {
    border: '2px dashed #ccc',
    borderRadius: '8px',
    padding: '40px',
    textAlign: 'center' as const,
    backgroundColor: '#f9f9f9',
    transition: 'all 0.3s',
    cursor: 'pointer'
  },
  dropzoneActive: {
    borderColor: '#4CAF50',
    backgroundColor: '#e8f5e9'
  },
  dropzoneHasFile: {
    borderColor: '#2196F3',
    backgroundColor: '#e3f2fd'
  },
  dropzoneContent: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    gap: '16px'
  },
  uploadIcon: {
    fontSize: '48px'
  },
  dropzoneText: {
    margin: '0',
    fontSize: '16px',
    color: '#666'
  },
  fileLabel: {
    cursor: 'pointer'
  },
  fileButton: {
    display: 'inline-block',
    padding: '10px 20px',
    backgroundColor: '#2196F3',
    color: 'white',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'background-color 0.2s'
  },
  fileInput: {
    display: 'none'
  },
  fileInfo: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: 'white',
    borderRadius: '6px',
    border: '1px solid #ddd'
  },
  fileName: {
    margin: '0',
    fontWeight: 'bold',
    color: '#333'
  },
  fileSize: {
    margin: '4px 0 0',
    fontSize: '14px',
    color: '#666'
  },
  uploadButton: {
    marginTop: '20px',
    padding: '12px 24px',
    fontSize: '16px',
    fontWeight: 'bold',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    width: '100%',
    transition: 'background-color 0.2s'
  },
  loading: {
    marginTop: '20px',
    textAlign: 'center' as const,
    padding: '40px'
  },
  spinner: {
    border: '4px solid #f3f3f3',
    borderTop: '4px solid #2196F3',
    borderRadius: '50%',
    width: '40px',
    height: '40px',
    animation: 'spin 1s linear infinite',
    margin: '0 auto 16px'
  },
  result: {
    marginTop: '20px',
    padding: '20px',
    borderRadius: '8px',
    border: '1px solid #ddd'
  },
  resultSuccess: {
    backgroundColor: '#e8f5e9',
    borderColor: '#4CAF50'
  },
  resultError: {
    backgroundColor: '#ffebee',
    borderColor: '#f44336'
  },
  resultTitle: {
    margin: '0 0 16px',
    fontSize: '20px',
    fontWeight: 'bold'
  },
  resultRow: {
    marginBottom: '12px',
    display: 'flex',
    gap: '12px',
    alignItems: 'center'
  },
  badge: {
    display: 'inline-block',
    padding: '4px 12px',
    backgroundColor: '#2196F3',
    color: 'white',
    borderRadius: '12px',
    fontSize: '14px'
  },
  stats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '16px',
    margin: '20px 0'
  },
  statCard: {
    backgroundColor: 'white',
    padding: '16px',
    borderRadius: '8px',
    textAlign: 'center' as const,
    border: '1px solid #ddd'
  },
  statValue: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#2196F3',
    marginBottom: '8px'
  },
  statLabel: {
    fontSize: '14px',
    color: '#666'
  },
  warnings: {
    backgroundColor: '#fff3cd',
    padding: '12px',
    borderRadius: '6px',
    marginBottom: '16px',
    border: '1px solid #ffc107'
  },
  successMessage: {
    fontSize: '14px',
    color: '#4CAF50',
    marginTop: '16px'
  },
  errorMessage: {
    fontSize: '14px',
    color: '#f44336',
    marginBottom: '12px'
  },
  errorDetails: {
    marginTop: '12px',
    padding: '12px',
    backgroundColor: 'white',
    borderRadius: '6px',
    border: '1px solid #ddd'
  },
  code: {
    display: 'block',
    padding: '8px',
    backgroundColor: '#f5f5f5',
    borderRadius: '4px',
    fontSize: '12px',
    fontFamily: 'monospace',
    marginTop: '8px',
    whiteSpace: 'pre-wrap' as const
  },
  suggestion: {
    marginTop: '12px',
    padding: '12px',
    backgroundColor: '#e3f2fd',
    borderRadius: '6px',
    border: '1px solid #2196F3'
  },
  errors: {
    marginTop: '12px'
  },
  retryButton: {
    marginTop: '16px',
    padding: '10px 20px',
    backgroundColor: '#666',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  details: {
    marginTop: '30px',
    padding: '16px',
    backgroundColor: '#f5f5f5',
    borderRadius: '8px'
  },
  summary: {
    cursor: 'pointer',
    fontWeight: 'bold',
    fontSize: '16px',
    color: '#333',
    padding: '8px'
  },
  formatList: {
    marginTop: '16px'
  },
  formatItem: {
    marginBottom: '16px',
    padding: '12px',
    backgroundColor: 'white',
    borderRadius: '6px',
    border: '1px solid #ddd'
  },
  formatNote: {
    marginTop: '16px',
    fontSize: '14px',
    color: '#666',
    fontStyle: 'italic'
  }
};
