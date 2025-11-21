import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en';
import cs from './locales/cs';

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    cs: { translation: cs },
  },
  lng: 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;