import React, { createContext, useContext, useState, useEffect } from 'react';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || (process.env.VITE_API_URL) || 'http://localhost:8000';

// Translation types
interface Translations {
  [key: string]: string;
}

interface LanguageContextType {
  language: 'en' | 'cz';
  setLanguage: (lang: 'en' | 'cz') => void;
  t: (key: string) => string;
  translations: Translations;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<'en' | 'cz'>('en');
  const [translations, setTranslations] = useState<Translations>({});

  // Load translations from backend when language changes
  useEffect(() => {
    const loadTranslations = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/translations/${language}`);
        const data = await response.json();

        if (data.success) {
          setTranslations(data.labels);
        }
      } catch (error) {
        console.error('Failed to load translations:', error);
        // Fallback to default English labels
        setTranslations({
          upload_title: 'Upload Employee Data',
          upload_description: 'Drag and drop CSV, Excel, or PDF files here',
          upload_button: 'Select File',
          upload_processing: 'Processing file...',
          upload_success: 'Data uploaded successfully!',
          upload_error: 'Upload failed. Please check the file format.',
          format_detected: 'Format detected',
          employees_processed: 'Employees processed',
          skills_extracted: 'Skills extracted',
          time_range: 'Time range',
          validation_errors: 'Validation errors',
          switch_language: language === 'en' ? 'Switch to Czech' : 'Přepnout na Angličtinu'
        });
      }
    };

    loadTranslations();
  }, [language]);

  // Translation function
  const t = (key: string): string => {
    return translations[key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, translations }}>
      {children}
    </LanguageContext.Provider>
  );
};

// Custom hook for using translations
export const useTranslation = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useTranslation must be used within a LanguageProvider');
  }
  return context;
};
