import { useTranslation } from 'react-i18next';
import { useAppStore } from '../state/store';

export const useLang = () => {
  const { i18n, t } = useTranslation();
  const { language, setLanguage } = useAppStore();

  const changeLanguage = (lang: 'en' | 'cs') => {
    i18n.changeLanguage(lang);
    setLanguage(lang);
  };

  return {
    t,
    language,
    changeLanguage,
  };
};
